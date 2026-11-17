#!/usr/bin/env python3
"""Fabrique une image disque GPT démarrable par Limine (BIOS et UEFI), sans root.

image-disque --noyau KERNEL.elf --sortie build/disque.img [--protocole multiboot1]
             [--racine DOSSIER] [--initrd DOSSIER] [--taille-mio 64] [--esp-mio 32]
             [--cmdline TEXTE] [--nom NOM]
    Partition 1 : ESP en FAT (Limine, limine.conf, noyau, initrd cpio).
    Partition 2 : racine en ext2, remplie depuis --racine.
    Partition 3 : démarrage BIOS (1 Mio, second étage de Limine en GPT).
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

SECTEUR = 512
MIO = 1 << 20
ALIGNEMENT = MIO
FIN_RESERVEE = MIO
PROTOCOLES = ('multiboot1', 'multiboot2', 'limine', 'linux')
LIMINE = Path(os.environ.get('LIMINE_DIR', Path.home() / '.local/share/limine/12.9.1'))
FICHIERS_EFI = ('BOOTX64.EFI', 'BOOTIA32.EFI', 'BOOTAA64.EFI', 'BOOTRISCV64.EFI')


class Erreur(Exception):
    pass


@dataclass(frozen=True)
class Plan:
    taille: int
    bios_debut: int
    esp_debut: int
    esp_taille: int
    racine_debut: int
    racine_taille: int

    def secteurs(self, octets: int) -> int:
        return octets // SECTEUR


def planifier(taille_mio: int, esp_mio: int) -> Plan:
    if esp_mio < 8:
        raise Erreur('ESP de 8 Mio au moins')
    taille = taille_mio * MIO
    bios_debut = ALIGNEMENT
    esp_debut = bios_debut + ALIGNEMENT
    esp_taille = esp_mio * MIO
    racine_debut = esp_debut + esp_taille
    racine_taille = taille - racine_debut - FIN_RESERVEE
    if racine_taille < 4 * MIO:
        raise Erreur(f'image trop petite : {taille_mio} Mio pour une ESP de {esp_mio} Mio')
    return Plan(taille, bios_debut, esp_debut, esp_taille, racine_debut, racine_taille)


def config_limine(nom: str, protocole: str, initrd: bool, cmdline: str) -> str:
    lignes = [
        'timeout: 0',
        'serial: yes',
        '',
        f'/{nom}',
        f'    protocol: {protocole}',
        '    path: boot():/boot/kernel.elf',
    ]
    if cmdline:
        lignes.append(f'    cmdline: {cmdline}')
    if initrd:
        lignes.append('    module_path: boot():/boot/initrd.cpio')
    return '\n'.join(lignes) + '\n'


def commande_gpt(image: Path, plan: Plan) -> list[str]:
    esp_fin = plan.secteurs(plan.esp_debut + plan.esp_taille) - 1
    racine_fin = plan.secteurs(plan.racine_debut + plan.racine_taille) - 1
    return [
        'sgdisk',
        '-o',
        '-n',
        f'1:{plan.secteurs(plan.esp_debut)}:{esp_fin}',
        '-t',
        '1:EF00',
        '-c',
        '1:ESP',
        '-n',
        f'2:{plan.secteurs(plan.racine_debut)}:{racine_fin}',
        '-t',
        '2:8300',
        '-c',
        '2:racine',
        '-n',
        f'3:{plan.secteurs(plan.bios_debut)}:{plan.secteurs(plan.esp_debut) - 1}',
        '-t',
        '3:EF02',
        '-c',
        '3:bios',
        str(image),
    ]


def lancer(commande: list[str], entree: bytes | None = None) -> bytes:
    try:
        resultat = subprocess.run(commande, input=entree, capture_output=True, check=False)
    except FileNotFoundError as erreur:
        raise Erreur(f'outil absent : {commande[0]}') from erreur
    if resultat.returncode != 0:
        detail = resultat.stderr.decode(errors='replace').strip()[-400:]
        raise Erreur(f'{Path(commande[0]).name} a échoué : {detail}')
    return resultat.stdout


def cpio(dossier: Path) -> bytes:
    chemins = sorted(str(p.relative_to(dossier)) for p in dossier.rglob('*'))
    liste = ''.join(c + '\n' for c in ['.', *chemins]).encode()
    try:
        resultat = subprocess.run(
            ['cpio', '-o', '-H', 'newc', '--reproducible', '--owner=+0:+0', '--quiet'],
            input=liste,
            capture_output=True,
            check=False,
            cwd=dossier,
        )
    except FileNotFoundError as erreur:
        raise Erreur('outil absent : cpio') from erreur
    if resultat.returncode != 0:
        raise Erreur('cpio a échoué : ' + resultat.stderr.decode(errors='replace')[-300:])
    return resultat.stdout


def remplir_esp(image: Path, plan: Plan, fichiers: dict[str, Path]) -> None:
    cible = f'{image}@@{plan.esp_debut}'
    lancer(
        [
            'mformat',
            '-i',
            cible,
            '-T',
            str(plan.secteurs(plan.esp_taille)),
            '-h',
            '64',
            '-s',
            '32',
            '-v',
            'ESP',
            '::',
        ]
    )
    lancer(['mmd', '-i', cible, '::/EFI', '::/EFI/BOOT', '::/boot', '::/boot/limine'])
    for destination, source in sorted(fichiers.items()):
        lancer(['mcopy', '-i', cible, str(source), '::' + destination])


def ecrire_racine(image: Path, plan: Plan, racine: Path | None) -> None:
    commande = ['mkfs.ext2', '-q', '-F', '-L', 'racine', '-E', f'offset={plan.racine_debut}']
    if racine is not None:
        commande += ['-d', str(racine)]
    lancer([*commande, str(image), f'{plan.racine_taille // 1024}k'])


def fichiers_esp(travail: Path, noyau: Path, config: str, initrd: bytes | None) -> dict[str, Path]:
    conf = travail / 'limine.conf'
    conf.write_text(config)
    fichiers = {
        '/boot/kernel.elf': noyau,
        '/boot/limine/limine.conf': conf,
        '/boot/limine/limine-bios.sys': LIMINE / 'limine-bios.sys',
    }
    for nom in FICHIERS_EFI:
        fichiers[f'/EFI/BOOT/{nom}'] = LIMINE / nom
    if initrd is not None:
        archive = travail / 'initrd.cpio'
        archive.write_bytes(initrd)
        fichiers['/boot/initrd.cpio'] = archive
    return fichiers


def verifier_entrees(arguments: argparse.Namespace) -> None:
    if not arguments.noyau.is_file():
        raise Erreur(f'noyau introuvable : {arguments.noyau}')
    for dossier in (arguments.racine, arguments.initrd):
        if dossier is not None and not dossier.is_dir():
            raise Erreur(f'dossier introuvable : {dossier}')
    manquants = [
        n for n in ('limine', 'limine-bios.sys', *FICHIERS_EFI) if not (LIMINE / n).is_file()
    ]
    if manquants:
        raise Erreur(f'Limine incomplet dans {LIMINE} : {", ".join(manquants)}')


def fabriquer(arguments: argparse.Namespace) -> Plan:
    verifier_entrees(arguments)
    plan = planifier(arguments.taille_mio, arguments.esp_mio)
    image: Path = arguments.sortie
    travail = image.parent / (image.name + '.travail')
    travail.mkdir(parents=True, exist_ok=True)
    initrd = cpio(arguments.initrd) if arguments.initrd else None
    config = config_limine(
        arguments.nom, arguments.protocole, initrd is not None, arguments.cmdline
    )
    image.unlink(missing_ok=True)
    with image.open('wb') as flux:
        flux.truncate(plan.taille)
    lancer(commande_gpt(image, plan))
    remplir_esp(image, plan, fichiers_esp(travail, arguments.noyau, config, initrd))
    ecrire_racine(image, plan, arguments.racine)
    lancer([str(LIMINE / 'limine'), 'bios-install', str(image)])
    lancer(['sgdisk', '-v', str(image)])
    shutil.rmtree(travail)
    return plan


def analyser(argv: list[str]) -> argparse.Namespace:
    parseur = argparse.ArgumentParser(
        prog='image-disque',
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parseur.add_argument('--noyau', type=Path, required=True)
    parseur.add_argument('--sortie', type=Path, required=True)
    parseur.add_argument('--protocole', choices=PROTOCOLES, default='multiboot1')
    parseur.add_argument('--racine', type=Path)
    parseur.add_argument('--initrd', type=Path)
    parseur.add_argument('--taille-mio', type=int, default=64)
    parseur.add_argument('--esp-mio', type=int, default=32)
    parseur.add_argument('--cmdline', default='')
    parseur.add_argument('--nom', default='systeme')
    return parseur.parse_args(argv)


def main(argv: list[str]) -> int:
    arguments = analyser(argv)
    try:
        plan = fabriquer(arguments)
    except Erreur as erreur:
        print(f'image-disque : {erreur}', file=sys.stderr)
        return 1
    print(
        f'{arguments.sortie} : {plan.taille // MIO} Mio, ESP {plan.esp_taille // MIO} Mio, '
        f'racine ext2 {plan.racine_taille // MIO} Mio, Limine BIOS et UEFI'
    )
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
