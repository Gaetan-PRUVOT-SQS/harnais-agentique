from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
_chargeur = SourceFileLoader('verifier_finance', str(RACINE / 'verifier'))
verifier = module_from_spec(spec_from_loader('verifier_finance', _chargeur))
_chargeur.exec_module(verifier)

NOMS = (
    'finance-quantitative',
    'pricing-derives',
    'revenu-fixe',
    'risque-quantitatif',
    'methodes-numeriques-finance',
    'portefeuille-quantitatif',
    'microstructure-marche',
    'mlp-series',
    'mlp-traits',
    'mlp-etiquetage',
    'mlp-validation',
    'mlp-modeles',
    'mlp-surapprentissage',
    'mlp-allocation',
    'mlp-causalite',
)

ANCRES = {
    'finance-quantitative': ('SR 26-2', 'MTH 9831', 'IEOR E4703', 'T+1', 'contrôle de fin'),
    'pricing-derives': ('Gatheral', 'Dupire', 'Feller', 'Merton'),
    'revenu-fixe': ('SOFR', '30/360', 'DV01', 'Hull-White'),
    'risque-quantitatif': ('97,5', 'MAR33', 'Artzner', 'CVA'),
    'methodes-numeriques-finance': ('Euler-Maruyama', 'parite_call_put', 'Kloeden'),
    'portefeuille-quantitatif': ('Ledoit', 'Bailey', 'ml4t-lookahead-bias', 'mlp-allocation'),
    'microstructure-marche': ('Perold', 'Kyle', 'strictement antérieure'),
    'mlp-series': ('Easley', 'ω_0 = 1', 'ml4t-lookahead-bias'),
    'mlp-traits': ('SADF', 'Lempel-Ziv', 'VPIN'),
    'mlp-etiquetage': ('Triple barrière', 'F1', 'c_t'),
    'mlp-modeles': ('neg_log_loss', 'log-uniforme', 'molécules'),
    'mlp-validation': ('embargo', 'C(N - 1, k - 1)', 'MDA'),
    'mlp-surapprentissage': ('Euler-Mascheroni', 'PBO', 'Φ⁻¹'),
    'mlp-allocation': ('quasi-diagonale', '3469961', 'ml4t-latent-factors'),
    'mlp-causalite': ('type B', '5131050', 'confondeur'),
}


def _texte(nom):
    return (RACINE / 'skills' / nom / 'SKILL.md').read_text(encoding='utf-8')


def test_descriptions_sous_le_plafond():
    for nom in NOMS:
        donnees = verifier.frontmatter(_texte(nom))
        assert donnees.get('name') == nom
        assert verifier.probleme_description(donnees.get('description')) is None
        assert '\u2014' not in _texte(nom)
        assert '\u2013' not in _texte(nom)


def test_la_porte_cite_des_skills_presents():
    porte = _texte('finance-quantitative')
    for nom in NOMS:
        if nom == 'finance-quantitative':
            continue
        assert nom in porte
        assert (RACINE / 'skills' / nom / 'SKILL.md').is_file()
        assert 'finance-quantitative' in _texte(nom)


def test_ancres_metier():
    for nom, ancres in ANCRES.items():
        texte = _texte(nom)
        for ancre in ancres:
            assert ancre in texte, nom


def test_le_listing_tient_dans_le_budget():
    ok, message = verifier.controle_budget(RACINE / 'skills', RACINE.parent / '.claude')
    assert ok, message


def test_agents_cite_le_domaine():
    agents = (RACINE / 'AGENTS.md').read_text(encoding='utf-8')
    for nom in NOMS:
        assert nom in agents
