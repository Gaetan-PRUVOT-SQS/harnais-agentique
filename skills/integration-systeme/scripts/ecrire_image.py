#!/usr/bin/env python3
"""Écrit une image de démarrage sur une clé USB ou une carte SD, cible vérifiée.

ecrire-image IMAGE /dev/disk/by-id/usb-... [--ecrire] [--taille-max GIO]
    Sans --ecrire : vérifie et affiche la cible, n'écrit rien.
    Avec --ecrire : dd, vidage du cache du disque, relecture comparée à l'image.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

PAR_ID = Path('/dev/disk/by-id')
GIO = 1 << 30
TAILLE_MAX_GIO = 256
ECRITURE = (
    'dd if="$1" of="$2" bs=4M conv=fsync oflag=direct status=progress'
    ' && blockdev --flushbufs "$2" && cmp -n "$3" "$1" "$2"'
)
COLONNES = 'NAME,PATH,TYPE,TRAN,RM,SIZE,MODEL,SERIAL,MOUNTPOINTS'

Disque = dict[str, Any]


class Refus(Exception):
    pass


def refus_chemin(chemin: str) -> str | None:
    if not chemin.startswith(str(PAR_ID) + '/'):
        return (
            'donner la cible par /dev/disk/by-id/ : le nom porte le modèle '
            "et le numéro de série, /dev/sdX change d'un branchement à l'autre"
        )
    if '-part' in Path(chemin).name:
        return 'la cible est une partition, donner le disque entier'
    return None


def points_de_montage(disque: Disque) -> list[str]:
    montages = [m for m in disque.get('mountpoints') or [] if m]
    for enfant in disque.get('children') or []:
        montages += points_de_montage(enfant)
    return montages


def refus_cible(
    disque: Disque, taille_image: int, type_mmc: str | None, taille_max: int
) -> list[str]:
    raisons = []
    if disque.get('type') != 'disk':
        raisons.append(f"{disque.get('path')} n'est pas un disque entier")
    carte_sd = str(disque.get('name', '')).startswith('mmcblk') and type_mmc == 'SD'
    if disque.get('tran') != 'usb' and not carte_sd:
        raisons.append(f'ni clé USB ni carte SD (transport {disque.get("tran")}, type {type_mmc})')
    montages = points_de_montage(disque)
    if montages:
        raisons.append(
            'partitions montées : '
            + ', '.join(montages)
            + ' (udisksctl unmount -b /dev/<partition>)'
        )
    taille = int(disque.get('size') or 0)
    if taille_image > taille:
        raisons.append(f'image de {taille_image} octets, disque de {taille}')
    if taille > taille_max:
        raisons.append(
            f'disque de {taille // GIO} Gio, au-delà de {taille_max // GIO} '
            'Gio (disque de sauvegarde ?), --taille-max pour lever'
        )
    return raisons


def commande_ecriture(
    image: str, noeud: str, taille: int, inscriptible: bool, shell: str
) -> list[str]:
    commande = [shell, '-c', ECRITURE, 'ecrire-image', image, noeud, str(taille)]
    if inscriptible:
        return commande
    return ['pkexec', *commande]


def candidats() -> list[str]:
    if not PAR_ID.is_dir():
        return []
    return sorted(
        str(p)
        for p in PAR_ID.iterdir()
        if p.name.startswith(('usb-', 'mmc-')) and '-part' not in p.name
    )


def type_mmc(nom: str) -> str | None:
    fichier = Path('/sys/block') / nom / 'device' / 'type'
    if not nom.startswith('mmcblk') or not fichier.is_file():
        return None
    return fichier.read_text().strip()


def lire_disque(noeud: str) -> Disque:
    sortie = subprocess.run(
        ['lsblk', '-J', '-b', '-o', COLONNES, noeud], capture_output=True, text=True, check=True
    ).stdout
    disques: list[Disque] = json.loads(sortie)['blockdevices']
    if len(disques) != 1:
        raise Refus(f'lsblk renvoie {len(disques)} périphériques pour {noeud}')
    return disques[0]


def resoudre(chemin: str) -> str:
    raison = refus_chemin(chemin)
    if raison:
        raise Refus(raison)
    noeud = os.path.realpath(chemin)
    if not os.path.exists(noeud) or not stat.S_ISBLK(os.stat(noeud).st_mode):
        raise Refus(f'{chemin} ne mène à aucun périphérique bloc branché')
    return noeud


def verifier_image(image: Path) -> int:
    if not image.is_file():
        raise Refus(f"{image} n'est pas un fichier")
    taille = image.stat().st_size
    if taille == 0:
        raise Refus(f'{image} est vide')
    return taille


def empreinte(image: Path) -> str:
    somme = hashlib.sha256()
    with image.open('rb') as flux:
        for bloc in iter(lambda: flux.read(1 << 20), b''):
            somme.update(bloc)
    return somme.hexdigest()


def examiner(image: Path, chemin: str, taille_max: int) -> tuple[str, Disque, int]:
    taille_image = verifier_image(image)
    noeud = resoudre(chemin)
    disque = lire_disque(noeud)
    raisons = refus_cible(disque, taille_image, type_mmc(disque['name']), taille_max)
    if raisons:
        raise Refus('cible refusée :\n  - ' + '\n  - '.join(raisons))
    return noeud, disque, taille_image


def afficher(image: Path, chemin: str, noeud: str, disque: Disque, taille: int) -> None:
    print(f'image  : {image} ({taille} octets, sha256 {empreinte(image)})')
    print(f'cible  : {chemin}')
    print(
        f'         {noeud}, {disque.get("model")}, série {disque.get("serial")}, '
        f'{int(disque["size"]) / GIO:.1f} Gio, transport {disque.get("tran")}'
    )


def ecrire(image: Path, chemin: str, noeud: str, taille: int) -> None:
    if os.path.realpath(chemin) != noeud:
        raise Refus(f'{chemin} a changé de nœud depuis la vérification, relancer')
    shell = shutil.which('sh') or '/bin/sh'
    commande = commande_ecriture(
        str(image.resolve()), noeud, taille, os.access(noeud, os.W_OK), shell
    )
    subprocess.run(commande, check=True)


def analyser(argv: list[str]) -> argparse.Namespace:
    parseur = argparse.ArgumentParser(
        prog='ecrire-image',
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parseur.add_argument('image', type=Path)
    parseur.add_argument('cible', help='/dev/disk/by-id/usb-... ou mmc-... (disque entier)')
    parseur.add_argument('--ecrire', action='store_true', help='écrire vraiment')
    parseur.add_argument('--taille-max', type=int, default=TAILLE_MAX_GIO, metavar='GIO')
    arguments = parseur.parse_args(argv)
    if arguments.taille_max <= 0:
        parseur.error('--taille-max doit être positif')
    return arguments


def main(argv: list[str]) -> int:
    arguments = analyser(argv)
    try:
        noeud, disque, taille = examiner(
            arguments.image, arguments.cible, arguments.taille_max * GIO
        )
        afficher(arguments.image, arguments.cible, noeud, disque, taille)
        if not arguments.ecrire:
            print('simulation : rien écrit, relancer avec --ecrire')
            return 0
        ecrire(arguments.image, arguments.cible, noeud, taille)
    except Refus as erreur:
        print(f'ecrire-image : {erreur}', file=sys.stderr)
        proposes = candidats()
        if proposes:
            print('clés et cartes branchées :\n  ' + '\n  '.join(proposes), file=sys.stderr)
        return 1
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as erreur:
        print(f'ecrire-image : échec, {erreur}', file=sys.stderr)
        return 1
    print("écrit et relu : identique à l'image")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
