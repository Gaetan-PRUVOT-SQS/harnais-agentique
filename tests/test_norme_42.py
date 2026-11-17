import json
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / 'fixtures' / 'norme-42'
PHRASE = 'le code C respecte la norme 42, seul le bandeau 42 est exclu'
VERSION = '3.3.60'
FICHIERS = (
    'AGENTS.md',
    'skills/c-systems/SKILL.md',
    'skills/pratiques-dev-senior/SKILL.md',
)
pytestmark = pytest.mark.skipif(not (Path.home() / ".local" / "bin" / "norminette").is_file(), reason="norminette absente")



def _binaire():
    candidat = Path.home() / '.local/bin/norminette'
    assert candidat.is_file()
    return str(candidat)


def _codes(nom):
    fini = subprocess.run(
        [_binaire(), '-f', 'json', str(FIXTURES / nom)],
        capture_output=True, text=True, check=False, timeout=30)
    donnees = json.loads(fini.stdout)
    return {erreur['name'] for erreur in donnees['files'][0]['errors']}


def test_phrase_norme_42_relue():
    for relatif in FICHIERS:
        texte = (RACINE / relatif).read_text(encoding='utf-8')
        assert PHRASE in ' '.join(texte.split()), relatif


def test_norminette_installee():
    fini = subprocess.run([_binaire(), '-v'], capture_output=True, text=True, check=False, timeout=30)
    assert fini.returncode == 0
    assert VERSION in fini.stdout


def test_bandeau_seul_ecart_sur_le_fichier_propre():
    assert _codes('zero.c') == {'INVALID_HEADER'}
    assert _codes('zero.h') == {'INVALID_HEADER'}


def test_goto_reste_refuse():
    codes = _codes('saut.c')
    assert 'GOTO_FBIDDEN' in codes
    assert 'INVALID_HEADER' in codes
