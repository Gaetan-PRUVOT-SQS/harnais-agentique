#!/usr/bin/env python3
"""Liste le code tiers d'un projet REUSE et échoue sur toute dépendance non voulue.

licences-tierces --licence-projet LICENCE [--autorisees A,B] [--dir DOSSIER]
                 [--exceptions FICHIER]
    Code 1 si le projet n'est pas conforme REUSE, si une licence tierce
    n'est pas autorisée, si un texte de licence apparaît dans du code
    déclaré maison (copie non déclarée) sans exception déclarée, ou si une
    exception déclarée ne sert plus.

    Exceptions : DOSSIER/licences-exceptions.toml par défaut, une table
    [[exception]] par fichier, avec chemin, marqueurs tolérés et raison.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

SOURCES = {'.c', '.h', '.s', '.S', '.asm', '.inc', '.ld', '.py', '.sh', '.bash', '.mk'}
NOMS_SOURCES = {'Makefile', 'makefile', 'GNUmakefile'}
MARQUEURS = re.compile(
    r'SPDX-License-Identifier|Permission is hereby granted'
    r'|GNU (?:Lesser |Affero )?General Public License|This program is free software'
    r'|Redistribution and use in source and binary forms|Licensed under the Apache License'
    r'|Mozilla Public License|Copyright \(c\)|Copyright ©',
    re.IGNORECASE,
)
OPERATEURS = {'AND', 'OR', 'WITH'}
TAILLE_MAX = 1 << 20
EXCEPTIONS = 'licences-exceptions.toml'
CLES_EXCEPTION = {'chemin', 'marqueurs', 'raison'}

Fichier = dict[str, Any]
Exceptions = dict[str, tuple[set[str], str]]


class Erreur(Exception):
    pass


def expression(fichier: Fichier) -> str:
    valeurs = [e['value'] for e in fichier.get('spdx_expressions') or []]
    return ' AND '.join(sorted(set(valeurs)))


def identifiants(expr: str) -> set[str]:
    return {m for m in re.findall(r'[A-Za-z0-9.+-]+', expr) if m not in OPERATEURS}


def classer(
    fichiers: list[Fichier], projet: str, autorisees: set[str]
) -> tuple[list[str], dict[str, list[str]], list[str]]:
    maison: list[str] = []
    tiers: dict[str, list[str]] = {}
    refuses: list[str] = []
    for fichier in fichiers:
        expr = expression(fichier)
        if expr == projet:
            maison.append(fichier['path'])
            continue
        tiers.setdefault(expr, []).append(fichier['path'])
        if not identifiants(expr) <= autorisees | {projet}:
            refuses.append(fichier['path'])
    return sorted(maison), {k: sorted(v) for k, v in tiers.items()}, sorted(refuses)


def marqueurs_trouves(texte: str) -> list[str]:
    return sorted({m.group(0) for m in MARQUEURS.finditer(texte)})


def est_source(chemin: Path) -> bool:
    return chemin.suffix in SOURCES or chemin.name in NOMS_SOURCES


def copies_soupconnees(dossier: Path, maison: list[str]) -> dict[str, list[str]]:
    soupcons = {}
    for relatif in maison:
        chemin = dossier / relatif
        if not est_source(chemin) or chemin.stat().st_size > TAILLE_MAX:
            continue
        trouves = marqueurs_trouves(chemin.read_text(errors='replace'))
        if trouves:
            soupcons[relatif] = trouves
    return soupcons


def valider_exception(entree: Any) -> tuple[str, set[str], str]:
    if not isinstance(entree, dict) or set(entree) != CLES_EXCEPTION:
        raise Erreur(f'exception mal formée, clés attendues : {", ".join(sorted(CLES_EXCEPTION))}')
    chemin, marqueurs, raison = entree['chemin'], entree['marqueurs'], entree['raison']
    if not isinstance(chemin, str) or not chemin:
        raise Erreur('exception sans chemin')
    if not isinstance(raison, str) or not raison.strip():
        raise Erreur(f'exception sans raison : {chemin}')
    if (
        not isinstance(marqueurs, list)
        or not marqueurs
        or not all(isinstance(m, str) and MARQUEURS.fullmatch(m) for m in marqueurs)
    ):
        raise Erreur(f'marqueurs invalides pour {chemin} : un marqueur reconnu par exception')
    return chemin, {m.lower() for m in marqueurs}, raison.strip()


def analyser_exceptions(donnees: dict[str, Any]) -> Exceptions:
    if set(donnees) - {'exception'}:
        raise Erreur('seules les tables [[exception]] sont permises')
    exceptions: Exceptions = {}
    for entree in donnees.get('exception', []):
        chemin, marqueurs, raison = valider_exception(entree)
        if chemin in exceptions:
            raise Erreur(f'exception en double : {chemin}')
        exceptions[chemin] = (marqueurs, raison)
    return exceptions


def lire_exceptions(chemin: Path, obligatoire: bool) -> Exceptions:
    if not chemin.is_file():
        if obligatoire:
            raise Erreur(f'fichier d exceptions absent : {chemin}')
        return {}
    try:
        return analyser_exceptions(tomllib.loads(chemin.read_text()))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as erreur:
        raise Erreur(f'{chemin.name} illisible : {erreur}') from erreur


def appliquer_exceptions(
    soupcons: dict[str, list[str]], exceptions: Exceptions
) -> tuple[dict[str, list[str]], list[str], list[str]]:
    restants: dict[str, list[str]] = {}
    appliquees: list[str] = []
    for chemin, trouves in soupcons.items():
        toleres = exceptions.get(chemin, (set(), ''))[0]
        reste = [t for t in trouves if t.lower() not in toleres]
        if reste:
            restants[chemin] = reste
        if len(reste) < len(trouves):
            appliquees.append(chemin)
    perimees = []
    for chemin, (marqueurs, _) in sorted(exceptions.items()):
        vus = {t.lower() for t in soupcons.get(chemin, [])}
        if marqueurs - vus:
            perimees.append(f'{chemin} : {", ".join(sorted(marqueurs - vus))}')
    return restants, sorted(appliquees), perimees


def lire_reuse(dossier: Path) -> dict[str, Any]:
    try:
        sortie = subprocess.run(
            ['reuse', '--root', str(dossier), 'lint', '--json'],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as erreur:
        raise Erreur('reuse absent (installer le paquet reuse)') from erreur
    try:
        rapport: dict[str, Any] = json.loads(sortie.stdout)
    except json.JSONDecodeError as erreur:
        raise Erreur('reuse lint illisible : ' + sortie.stderr.strip()[-300:]) from erreur
    return rapport


def non_conformites(rapport: dict[str, Any]) -> list[str]:
    manques = rapport.get('non_compliant') or {}
    return [f'{cle} : {", ".join(map(str, v))}' for cle, v in manques.items() if v]


def analyser(argv: list[str]) -> argparse.Namespace:
    parseur = argparse.ArgumentParser(
        prog='licences-tierces',
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parseur.add_argument('--licence-projet', required=True, metavar='SPDX')
    parseur.add_argument('--autorisees', default='', metavar='A,B')
    parseur.add_argument('--dir', type=Path, default=Path())
    parseur.add_argument('--exceptions', type=Path, metavar='FICHIER')
    return parseur.parse_args(argv)


def afficher(maison: list[str], tiers: dict[str, list[str]], projet: str) -> None:
    pluriel = 's' if len(maison) > 1 else ''
    print(f'code maison : {len(maison)} fichier{pluriel} ({projet})')
    if not tiers:
        print('code tiers : aucun')
    for licence, chemins in sorted(tiers.items()):
        print(f'code tiers {licence or "sans licence"} : {", ".join(chemins)}')


def main(argv: list[str]) -> int:
    arguments = analyser(argv)
    autorisees = {a for a in arguments.autorisees.split(',') if a}
    dossier = arguments.dir.resolve()
    try:
        rapport = lire_reuse(dossier)
        exceptions = lire_exceptions(
            arguments.exceptions or dossier / EXCEPTIONS, arguments.exceptions is not None
        )
    except Erreur as erreur:
        print(f'licences-tierces : {erreur}', file=sys.stderr)
        return 1
    manques = non_conformites(rapport)
    maison, tiers, refuses = classer(rapport['files'], arguments.licence_projet, autorisees)
    soupcons, appliquees, perimees = appliquer_exceptions(
        copies_soupconnees(dossier, maison), exceptions
    )
    afficher(maison, tiers, arguments.licence_projet)
    for chemin in appliquees:
        print(f'exception déclarée : {chemin} ({exceptions[chemin][1]})')
    for manque in manques:
        print(f'non conforme REUSE, {manque}')
    for chemin in refuses:
        print(f'licence tierce non autorisée : {chemin}')
    for chemin, trouves in sorted(soupcons.items()):
        print(f'copie non déclarée ? {chemin} : {", ".join(trouves)}')
    for perimee in perimees:
        print(f'exception périmée, marqueur absent : {perimee}')
    return 1 if manques or refuses or soupcons or perimees else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
