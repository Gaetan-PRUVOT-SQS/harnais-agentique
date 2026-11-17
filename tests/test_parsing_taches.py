from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
_chargeur = SourceFileLoader('verifier_parsing_taches', str(RACINE / 'verifier'))
verifier = module_from_spec(spec_from_loader('verifier_parsing_taches', _chargeur))
_chargeur.exec_module(verifier)

SKILL = RACINE / 'skills' / 'parsing-taches' / 'SKILL.md'
AGENTS = RACINE / 'AGENTS.md'

PHRASES = (
    'Le parseur décrit le travail',
    'estimate',
    'bound',
    'request',
    'Type explicite',
    'lot mixte',
    'rang_u',
    'TASK_WEIGHT_SQL',
    'Requirements',
    'rsc_fpops_est',
)


def test_skill_present_et_branche():
    texte = SKILL.read_text(encoding='utf-8')
    agents = AGENTS.read_text(encoding='utf-8')
    donnees = verifier.frontmatter(texte)
    assert donnees.get('name') == 'parsing-taches'
    assert verifier.probleme_description(donnees.get('description')) is None
    assert 'parseWorkload' in donnees['description']
    assert '/parsing-taches' in donnees['description']
    assert '\u2014' not in texte
    assert '\u2013' not in texte
    for phrase in PHRASES:
        assert phrase in texte, phrase
    assert 'parsing-taches' in agents
