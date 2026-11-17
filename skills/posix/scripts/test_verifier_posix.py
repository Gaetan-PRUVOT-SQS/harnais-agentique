from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

import verifier_posix as vp

ICI = Path(__file__).parent
FIXTURES = ICI / 'fixtures'
ABSENTS_DE_LA_GLIBC = {'tcgetwinsize', 'tcsetwinsize'}


def test_noms_restrict_et_tableaux_ignores() -> None:
    assert vp.normaliser_parametre('const char *restrict chemin') == ('const', 'char', '*')
    assert vp.normaliser_parametre('int descripteurs[2]') == ('int', '*')
    assert vp.normaliser_parametre('char *const argv[]') == ('char', '*', 'const', '*')
    assert vp.normaliser_parametre('struct stat *') == ('struct', 'stat', '*')
    assert vp.normaliser_parametre('struct stat *etat') == ('struct', 'stat', '*')
    assert vp.normaliser_parametre('size_t') == ('size_t',)
    assert vp.normaliser_parametre('unsigned') == vp.normaliser_parametre('unsigned int n')


def test_declarations_conformes() -> None:
    lues = dict(vp.declarations((FIXTURES / 'conforme' / 'unistd.h').read_text()))
    assert set(lues) == {'write', 'getpid', 'pipe', 'execve', '_exit', 'sleep', 'ft_maison'}
    assert lues['_exit'] == vp.Signature(('void',), (('int',),))


def test_declaration_sans_prototype() -> None:
    [(nom, signature)] = vp.declarations('int\tf();')
    assert signature.parametres == (vp.SANS_PROTOTYPE,)
    assert signature.texte(nom) == 'int f()'
    assert signature != vp.Signature(('int',), ())


def test_entetes_conformes(capsys: pytest.CaptureFixture[str]) -> None:
    assert vp.main(['entetes', str(FIXTURES / 'conforme')]) == 0
    assert '8 conformes, 0 écarts, 1 hors référence' in capsys.readouterr().out


def test_entetes_avec_ecarts(capsys: pytest.CaptureFixture[str]) -> None:
    assert vp.main(['entetes', str(FIXTURES / 'ecarts')]) == 1
    sortie = capsys.readouterr().out
    assert 'KO write : long int write' in sortie
    assert 'KO getpid : int getpid(void) au lieu de pid_t getpid(void)' in sortie
    assert 'KO strdup : déclarée dans <unistd.h>, POSIX la met dans <string.h>' in sortie
    assert 'KO access : déclarée dans <stdio.h>, POSIX la met dans <unistd.h>' in sortie


def test_errno_valide_avec_paire_permise(capsys: pytest.CaptureFixture[str]) -> None:
    assert vp.main(['errno', str(FIXTURES / 'errno-valide.liste')]) == 0
    sortie = capsys.readouterr().out
    assert 'extensions hors POSIX : EMAISON' in sortie
    assert '3 noms POSIX sur 78, 0 problèmes' in sortie


def test_errno_fautive(capsys: pytest.CaptureFixture[str]) -> None:
    assert vp.main(['errno', str(FIXTURES / 'errno-fautive.liste')]) == 1
    sortie = capsys.readouterr().out
    assert 'KO EINVAL, ERANGE : même valeur 22' in sortie
    assert 'KO EIO : valeur « 0 » non positive' in sortie
    assert 'KO erreur : nom hors de l espace' in sortie


def test_errno_complet(capsys: pytest.CaptureFixture[str]) -> None:
    assert vp.main(['errno', '--complet', str(FIXTURES / 'errno-valide.liste')]) == 1
    assert 'KO E2BIG : absent' in capsys.readouterr().out


def test_dossier_absent(capsys: pytest.CaptureFixture[str]) -> None:
    assert vp.main(['entetes', str(FIXTURES / 'absent')]) == 2
    assert 'dossier introuvable' in capsys.readouterr().err


def test_reference_d_erreurs() -> None:
    noms = (vp.REFERENCE / 'errno.txt').read_text().split()
    assert len(noms) == len(set(noms)) == 78


def test_reference_conforme_a_la_glibc() -> None:
    if not shutil.which('gcc'):
        pytest.skip('gcc absent')
    lignes = (vp.REFERENCE / 'interfaces.tsv').read_text().splitlines()
    code = ['#define _GNU_SOURCE']
    code += [f'#include <{e}>' for e in sorted({ligne.split('\t')[0] for ligne in lignes})]
    for ligne in lignes:
        m = re.fullmatch(r'(.*?)\b(\w+)\((.*)\);', ligne.split('\t')[1])
        assert m, ligne
        retour, nom, params = m.groups()
        code.append(
            f'_Static_assert(__builtin_types_compatible_p(__typeof__({nom}), '
            f'{retour.strip()} ({params})), "{nom}");'
        )
    build = ICI / 'build'
    build.mkdir(exist_ok=True)
    source = build / 'reference_hote.c'
    try:
        source.write_text('\n'.join(code) + '\n')
        env = {'LC_ALL': 'C', 'PATH': '/usr/bin:/bin'}
        commande = ['gcc', '-std=c17', '-fsyntax-only', str(source)]
        r = subprocess.run(commande, capture_output=True, text=True, check=False, env=env)
    finally:
        shutil.rmtree(build)
    fautives = set(re.findall(r"'(\w+)' undeclared|\"(\w+)\"", r.stderr))
    noms = {n for paire in fautives for n in paire if n}
    assert noms <= ABSENTS_DE_LA_GLIBC, r.stderr
