#!/usr/bin/env python3
"""Compare une libc maison à POSIX.1-2024 (Issue 8).

verifier-posix errno LISTE [--complet]
    LISTE : lignes « NOM<tab>VALEUR<tab>message » (format de genere-errno).
    Code 1 si une valeur n'est pas un entier positif, si deux noms partagent
    une valeur (sauf EAGAIN et EWOULDBLOCK, ENOTSUP et EOPNOTSUPP), si un nom
    ne commence pas par E suivi d'une majuscule ou d'un chiffre, ou, avec
    --complet, s'il manque un des 78 noms d'Issue 8.

verifier-posix entetes DOSSIER [DOSSIER ...]
    Lit les .h sous chaque DOSSIER (racine des include) et compare chaque
    fonction déclarée à la référence : même en-tête, même type de retour,
    mêmes types de paramètres (noms, restrict et attributs ignorés, tableau
    en paramètre lu comme pointeur). Code 1 sur tout écart.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REFERENCE = Path(__file__).resolve().parent / 'reference'
PAIRES_PERMISES = {frozenset({'EAGAIN', 'EWOULDBLOCK'}), frozenset({'ENOTSUP', 'EOPNOTSUPP'})}
NOM_ERREUR = re.compile(r'E[A-Z0-9][A-Z0-9_]*')
JETON = re.compile(r'\.\.\.|[A-Za-z_]\w*|\[[^\]]*\]|[*(),]')
MOTS_TYPE = {
    'void',
    'char',
    'short',
    'int',
    'long',
    'float',
    'double',
    'signed',
    'unsigned',
    'const',
    'volatile',
    'restrict',
    '_Bool',
    'struct',
    'union',
    'enum',
}
IGNORES = {'restrict', '__restrict', '__restrict__', 'extern', '_Noreturn', 'noreturn', 'inline'}
ETIQUETTES = {'struct', 'union', 'enum'}
SPECIFIEURS = {
    'void',
    'char',
    'short',
    'int',
    'long',
    'float',
    'double',
    'signed',
    'unsigned',
    '_Bool',
}
QUALIFICATIFS = {'const', 'volatile'}
SANS_PROTOTYPE = ('sans prototype',)


class Erreur(Exception):
    pass


@dataclass(frozen=True)
class Signature:
    retour: tuple[str, ...]
    parametres: tuple[tuple[str, ...], ...]

    def texte(self, nom: str) -> str:
        if self.parametres == (SANS_PROTOTYPE,):
            return f'{" ".join(self.retour)} {nom}()'
        params = ', '.join(' '.join(p) for p in self.parametres) or 'void'
        return f'{" ".join(self.retour)} {nom}({params})'


def retirer_groupes(texte: str, ouvrant: str, fermant: str) -> str:
    sortie: list[str] = []
    profondeur = 0
    for c in texte:
        if c == ouvrant:
            profondeur += 1
        elif c == fermant and profondeur:
            profondeur -= 1
        elif not profondeur:
            sortie.append(c)
    return ''.join(sortie)


def retirer_attributs(texte: str) -> str:
    while (debut := texte.find('__attribute__')) >= 0:
        ouvre = texte.find('(', debut)
        if ouvre < 0:
            raise Erreur(f'__attribute__ sans parenthèse : {texte[debut : debut + 40]}')
        profondeur, i = 0, ouvre
        while i < len(texte):
            profondeur += {'(': 1, ')': -1}.get(texte[i], 0)
            if profondeur == 0:
                break
            i += 1
        texte = texte[:debut] + texte[i + 1 :]
    return texte


def canoniser(jetons: list[str]) -> tuple[str, ...]:
    fin = 0
    while fin < len(jetons) and jetons[fin] in SPECIFIEURS | QUALIFICATIFS:
        fin += 1
    tete, reste = jetons[:fin], jetons[fin:]
    specs = [j for j in tete if j in SPECIFIEURS]
    if not specs:
        return tuple(jetons)
    signe = [j for j in specs if j in {'signed', 'unsigned'}]
    tailles = [j for j in specs if j in {'short', 'long'}]
    base = [j for j in specs if j not in {'signed', 'unsigned', 'short', 'long', 'int'}] or ['int']
    if signe == ['signed'] and base == ['int']:
        signe = []
    quals = sorted(j for j in tete if j in QUALIFICATIFS)
    return tuple(quals + signe + tailles + base + reste)


def normaliser_parametre(texte: str) -> tuple[str, ...]:
    jetons = [j for j in JETON.findall(texte) if j not in IGNORES]
    idents = [i for i, j in enumerate(jetons) if re.fullmatch(r'[A-Za-z_]\w*', j)]
    if idents:
        dernier = idents[-1]
        avant = jetons[dernier - 1] if dernier else ''
        a_un_type = any(jetons[i] not in {'const', 'volatile'} for i in idents[:-1])
        if jetons[dernier] not in MOTS_TYPE and a_un_type and avant not in ETIQUETTES:
            del jetons[dernier]
    for i, jeton in enumerate(jetons):
        if jeton.startswith('['):
            jetons[i] = '*'
            break
    return canoniser([j for j in jetons if not j.startswith('[')])


def decouper_parametres(texte: str) -> list[str]:
    morceaux: list[str] = []
    courant: list[str] = []
    profondeur = 0
    for c in texte:
        if c == ',' and profondeur == 0:
            morceaux.append(''.join(courant))
            courant = []
            continue
        profondeur += {'(': 1, ')': -1}.get(c, 0)
        courant.append(c)
    morceaux.append(''.join(courant))
    return [m.strip() for m in morceaux if m.strip()]


def lire_declaration(texte: str) -> tuple[str, Signature] | None:
    texte = ' '.join(retirer_attributs(texte).split())
    m = re.fullmatch(r'(?P<avant>[^()]*?)\b(?P<nom>[A-Za-z_]\w*)\s*\((?P<params>.*)\)', texte)
    if not m or not m['avant'].strip() or m['avant'].split()[0] == 'typedef':
        return None
    retour = canoniser([j for j in JETON.findall(m['avant']) if j not in IGNORES | {'static'}])
    params = decouper_parametres(m['params'])
    if not params:
        return m['nom'], Signature(retour, (SANS_PROTOTYPE,))
    if params == ['void']:
        params = []
    return m['nom'], Signature(retour, tuple(normaliser_parametre(p) for p in params))


def declarations(source: str) -> list[tuple[str, Signature]]:
    source = re.sub(r'/\*.*?\*/|//[^\n]*', ' ', source, flags=re.S)
    source = re.sub(r'^\s*#(?:[^\n]*\\\n)*[^\n]*', ' ', source, flags=re.M)
    source = retirer_groupes(source, '{', '}')
    trouvees = (lire_declaration(morceau) for morceau in source.split(';'))
    return [d for d in trouvees if d is not None]


def lire_reference() -> dict[str, tuple[str, Signature]]:
    reference: dict[str, tuple[str, Signature]] = {}
    for ligne in (REFERENCE / 'interfaces.tsv').read_text().splitlines():
        entete, prototype = ligne.split('\t')
        lue = lire_declaration(prototype.rstrip(';'))
        if lue is None:
            raise Erreur(f'référence illisible : {ligne}')
        reference[lue[0]] = (entete, lue[1])
    return reference


def entete_proprietaire(chemin: str) -> str:
    dossier, _, nom = chemin.rpartition('/')
    if dossier == 'bits' and '_' in nom:
        return nom.split('_', 1)[0] + '.h'
    return chemin


def verifier_entetes(dossiers: list[Path]) -> int:
    reference = lire_reference()
    ecarts = conformes = hors = 0
    for dossier in dossiers:
        if not dossier.is_dir():
            raise Erreur(f'{dossier} : dossier introuvable')
        for fichier in sorted(dossier.rglob('*.h')):
            entete = entete_proprietaire(fichier.relative_to(dossier).as_posix())
            for nom, signature in declarations(fichier.read_text(errors='replace')):
                if nom not in reference:
                    hors += 1
                    continue
                attendu_entete, attendue = reference[nom]
                if entete != attendu_entete:
                    print(
                        f'KO {nom} : déclarée dans <{entete}>, POSIX la met dans <{attendu_entete}>'
                    )
                    ecarts += 1
                elif signature != attendue:
                    print(f'KO {nom} : {signature.texte(nom)} au lieu de {attendue.texte(nom)}')
                    ecarts += 1
                else:
                    conformes += 1
    print(f'{conformes} conformes, {ecarts} écarts, {hors} hors référence')
    return 1 if ecarts else 0


def lire_liste(liste: Path) -> list[tuple[str, str]]:
    lignes = [ligne.split('\t') for ligne in liste.read_text().splitlines() if ligne.strip()]
    return [(champs[0].strip(), champs[1].strip() if len(champs) > 1 else '') for champs in lignes]


def verifier_errno(liste: Path, complet: bool) -> int:
    posix = set((REFERENCE / 'errno.txt').read_text().split())
    entrees = lire_liste(liste)
    problemes: list[str] = []
    par_valeur: dict[int, list[str]] = {}
    for nom, valeur in entrees:
        if not NOM_ERREUR.fullmatch(nom):
            problemes.append(f'{nom} : nom hors de l espace E[A-Z0-9]* de <errno.h>')
        if not valeur.isdigit() or int(valeur) <= 0:
            problemes.append(f'{nom} : valeur « {valeur} » non positive')
            continue
        par_valeur.setdefault(int(valeur), []).append(nom)
    for commune, noms in sorted(par_valeur.items()):
        if len(noms) > 1 and frozenset(noms) not in PAIRES_PERMISES:
            problemes.append(f'{", ".join(noms)} : même valeur {commune}')
    noms_lus = {nom for nom, _ in entrees}
    if complet:
        problemes += [f'{nom} : absent' for nom in sorted(posix - noms_lus)]
    for probleme in problemes:
        print(f'KO {probleme}')
    extensions = sorted(noms_lus - posix)
    if extensions:
        print(f'extensions hors POSIX : {", ".join(extensions)}')
    print(f'{len(noms_lus & posix)} noms POSIX sur {len(posix)}, {len(problemes)} problèmes')
    return 1 if problemes else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog='verifier-posix',
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sous = parser.add_subparsers(dest='commande', required=True)
    p_errno = sous.add_parser('errno')
    p_errno.add_argument('liste', type=Path)
    p_errno.add_argument('--complet', action='store_true')
    p_entetes = sous.add_parser('entetes')
    p_entetes.add_argument('dossiers', type=Path, nargs='+')
    args = parser.parse_args(argv)
    try:
        if args.commande == 'errno':
            return verifier_errno(args.liste, args.complet)
        return verifier_entetes(args.dossiers)
    except (Erreur, OSError, ValueError) as e:
        print(f'verifier-posix : {e}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
