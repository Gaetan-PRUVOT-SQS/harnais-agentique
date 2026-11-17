from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
_chargeur = SourceFileLoader('verifier_wss', str(RACINE / 'verifier'))
verifier = module_from_spec(spec_from_loader('verifier_wss', _chargeur))
_chargeur.exec_module(verifier)

NOM = 'weight-space-surgery'
ANCRES = (
    'W = W0 - scale * outer(u, mask * (u @ W0))',
    'orthogonal control',
    'held-out',
    'down_proj',
    'sha256',
    'no weight access, stop',
)


def _texte():
    return (RACINE / 'skills' / NOM / 'SKILL.md').read_text(encoding='utf-8')


def test_description_et_nom():
    donnees = verifier.frontmatter(_texte())
    assert donnees.get('name') == NOM
    assert verifier.probleme_description(donnees.get('description')) is None
    assert 'sans réentraînement' in donnees.get('description')
    assert 'weight-space surgery' in donnees.get('description')
    assert '\u2014' not in _texte()
    assert '\u2013' not in _texte()


def test_ancres_de_la_recette():
    texte = _texte()
    for ancre in ANCRES:
        assert ancre in texte, ancre


def test_agents_cite_le_skill():
    agents = (RACINE / 'AGENTS.md').read_text(encoding='utf-8')
    assert NOM in agents
    assert 'sans réentraînement' in agents
