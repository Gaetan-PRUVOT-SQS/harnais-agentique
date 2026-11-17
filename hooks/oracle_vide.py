#!/usr/bin/env python3
"""Tests du tour sans assertion, et code plus récent que le début du tour."""

import ast
import os
import re
import sys
from pathlib import Path

EXTENSIONS_CODE = {
    '.py', '.js', '.jsx', '.ts', '.tsx', '.php', '.c', '.h', '.rs', '.go', '.sh', '.bash',
}
MAX_LIGNES = 20
APPEL_DYNAMIQUE = re.compile(r'\b(?:it|test)\s*\(')
TEST_JS = re.compile(r'\.(?:test|spec)\.(?:jsx?|tsx?)$')
FORT_JS = re.compile(
    r'\.(?:toBe|toEqual|toStrictEqual|toThrow|toHave|toContain|toMatch|'
    r'toBeCloseTo|toBeGreaterThan|toBeLessThan|toBeInstanceOf|toBeNull|toBeNaN)\s*\('
    r'|\bassert\.(?:equal|strictEqual|deepEqual|deepStrictEqual|notEqual|notStrictEqual|'
    r'throws|rejects|match)\s*\('
    r'|\bassert\s*\([^)]*(?:===|!==|==|!=|<=|>=|<|>)'
)
FAIBLE_JS = re.compile(
    r'\.(?:toBeTruthy|toBeFalsy|toBeDefined|toBeUndefined)\s*\('
    r'|\bassert\.ok\s*\('
    r'|\bassert\s*\(\s*[A-Za-z_$.][\w$.]*\s*\)'
)
FORT_PHP = re.compile(
    r'\b(?:assertSame|assertEquals|assertEqual|assertCount|assertMatches|assertInstanceOf|'
    r'assertContains|assertGreater|assertLess|assertString|expectException|assertJson|'
    r'assertFile|assertArrayHasKey)\b',
    re.IGNORECASE,
)
FAIBLE_PHP = re.compile(
    r'\b(?:assertNotNull|assertNull|assertTrue|assertFalse|assertEmpty|assertNotEmpty)\b',
    re.IGNORECASE,
)
METHODES_FAIBLES = (
    'assertisnotnone', 'assertisnone', 'asserttrue', 'assertfalse', 'assertisnull',
)


def ignores():
    texte = (Path(__file__).resolve().parent / 'ignores.sh').read_text(encoding='utf-8')
    trouve = re.search(r'IGNORES="([^"]*)"', texte)
    return set(trouve.group(1).split()) if trouve else set()


def plus_recent(chemin, limite):
    try:
        info = chemin.lstat()
    except OSError:
        return False
    return max(info.st_mtime, info.st_ctime) > limite


def marcher(racine, limite):
    racine = Path(racine)
    sauts = ignores()
    for dossier, sous, fichiers in os.walk(racine):
        sous[:] = [nom for nom in sous if nom not in sauts]
        for nom in fichiers:
            chemin = Path(dossier) / nom
            if chemin.is_symlink() or not plus_recent(chemin, limite):
                continue
            yield chemin


def nom_appel(noeud):
    if isinstance(noeud, ast.Name):
        return noeud.id
    if isinstance(noeud, ast.Attribute):
        return nom_appel(noeud.value) + '.' + noeud.attr
    return ''


def assert_faible(noeud):
    test = noeud.test
    if isinstance(test, ast.Constant):
        return True
    if isinstance(test, (ast.Name, ast.Attribute)):
        return True
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
        return isinstance(test.operand, (ast.Name, ast.Attribute, ast.Constant))
    if isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(test.ops[0], (ast.Is, ast.IsNot)):
        cotes = [test.left, *test.comparators]
        return any(isinstance(cote, ast.Constant) and cote.value is None for cote in cotes)
    return False


def oracle_fort(fonction):
    for noeud in ast.walk(fonction):
        if isinstance(noeud, ast.Assert) and not assert_faible(noeud):
            return True
        if not isinstance(noeud, ast.Call):
            continue
        nom = nom_appel(noeud.func).lower()
        if nom.endswith('raises'):
            return True
        if 'assert' in nom and not nom.endswith(METHODES_FAIBLES):
            return True
    return False


def fonctions_py(source):
    try:
        arbre = ast.parse(source)
    except SyntaxError:
        return []
    noms = []
    for noeud in ast.walk(arbre):
        if (isinstance(noeud, (ast.FunctionDef, ast.AsyncFunctionDef))
                and noeud.name.startswith('test') and not oracle_fort(noeud)):
            noms.append(noeud.name)
    return noms


def est_test_py(chemin):
    return chemin.suffix == '.py' and (chemin.name.startswith('test_') or chemin.name.endswith('_test.py'))


def sauter_chaine(texte, index):
    quote = texte[index]
    i = index + 1
    while i < len(texte):
        if texte[i] == '\\':
            i += 2
            continue
        if texte[i] == quote:
            return i + 1
        i += 1
    return len(texte)


def jusqu_a(texte, debut, ouvrant, fermant):
    profondeur = 0
    i = debut
    while i < len(texte):
        car = texte[i]
        if car in '"\'`':
            i = sauter_chaine(texte, i)
            continue
        if car == ouvrant:
            profondeur += 1
        elif car == fermant:
            profondeur -= 1
            if profondeur == 0:
                return texte[debut + 1:i]
        i += 1
    return None


def classe_texte(corps, fort, faible):
    if fort.search(corps):
        return 'fort'
    if faible.search(corps):
        return 'faible'
    if re.search(r'\b(?:expect|assert)\b', corps, re.IGNORECASE):
        return 'fort'
    return 'vide'


def appels_js(texte):
    noms = []
    for match in APPEL_DYNAMIQUE.finditer(texte):
        region = jusqu_a(texte, match.end() - 1, '(', ')')
        if region is None:
            continue
        label = ''
        if region and region[0] in '"\'`':
            fin = sauter_chaine(region, 0)
            label = region[1:fin - 1]
        accolade = region.find('{')
        corps = jusqu_a(region, accolade, '{', '}') if accolade >= 0 else region
        if corps is None:
            continue
        if classe_texte(corps, FORT_JS, FAIBLE_JS) != 'fort':
            noms.append(label or match.group(0).split('(')[0].strip())
    return noms


def fonctions_php(texte):
    noms = []
    for match in re.finditer(r'\bfunction\s+(test\w*)\s*\(', texte):
        accolade = texte.find('{', match.end())
        if accolade < 0:
            continue
        corps = jusqu_a(texte, accolade, '{', '}')
        if corps is None:
            continue
        if classe_texte(corps, FORT_PHP, FAIBLE_PHP) != 'fort':
            noms.append(match.group(1))
    return noms


def lignes_autres(texte, nom):
    if TEST_JS.search(nom):
        return appels_js(texte)
    if nom.endswith(('Test.php', 'Tests.php')):
        return fonctions_php(texte)
    return []


def lire(chemin):
    try:
        return chemin.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return None


def rapport(racine, depuis):
    limite = Path(depuis).stat().st_mtime
    lignes = []
    base = Path(racine)
    for chemin in marcher(base, limite):
        if est_test_py(chemin):
            texte = lire(chemin)
            if texte is None:
                continue
            relatif = chemin.relative_to(base)
            lignes.extend(f'{relatif}:{nom}' for nom in fonctions_py(texte))
        elif TEST_JS.search(chemin.name) or chemin.name.endswith(('Test.php', 'Tests.php')):
            texte = lire(chemin)
            if texte is None:
                continue
            lignes.extend(f'{chemin.relative_to(base)}:{nom}' for nom in lignes_autres(texte, chemin.name))
        if len(lignes) >= MAX_LIGNES:
            break
    return lignes[:MAX_LIGNES]


def code_recent(racine, depuis):
    limite = Path(depuis).stat().st_mtime
    base = Path(racine)
    trouves = []
    for chemin in marcher(base, limite):
        if chemin.suffix in EXTENSIONS_CODE:
            trouves.append(str(chemin.relative_to(base)))
        if len(trouves) >= MAX_LIGNES:
            break
    return trouves


def main(argv):
    mode = 'oracles'
    dossier = None
    depuis = None
    index = 1
    while index < len(argv):
        mot = argv[index]
        if mot == '--code-recent':
            mode = 'code'
        elif mot in ('--dir', '--depuis') and index + 1 < len(argv):
            index += 1
            if mot == '--dir':
                dossier = Path(argv[index])
            else:
                depuis = Path(argv[index])
        else:
            return 2
        index += 1
    if dossier is None or depuis is None or not depuis.is_file() or not dossier.is_dir():
        return 0
    lignes = code_recent(dossier, depuis) if mode == 'code' else rapport(dossier, depuis)
    if lignes:
        sys.stdout.write('\n'.join(lignes) + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
