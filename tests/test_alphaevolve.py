"""AlphaEvolve : le candidat mesuré le meilleur reste, sans population."""

from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
AGENTS = RACINE / "AGENTS.md"
AGILE = RACINE / "skills/pratiques-agiles/SKILL.md"
EVOLVE = RACINE / "skills/openevolve/SKILL.md"
PLAFOND_OCTETS = 32768


def test_on_garde_le_candidat_mesure_le_meilleur():
    texte = AGENTS.read_text(encoding="utf-8")
    assert "AlphaEvolve :" in texte
    assert "on garde le candidat qu'une commande mesure le meilleur" in texte
    assert "Un score moins bon, ou pas mesuré, ne le remplace pas" in texte
    assert "Pas de population ni de boucle d'évolution" in texte
    assert "graine, évaluateur, sortie et budget restent ceux que la demande nomme" in texte


def test_la_boucle_et_le_parent_restent():
    texte = AGENTS.read_text(encoding="utf-8")
    assert "On s'arrête quand il est tenu" in texte
    assert "pas de boucle de fond" in texte
    assert "Pas d'installation ni de boucle LLM" in texte
    agile = AGILE.read_text(encoding="utf-8")
    assert "On garde le candidat qu'une commande mesure le meilleur" in agile
    assert "pas de boucle de fond" in agile
    evolve = EVOLVE.read_text(encoding="utf-8")
    assert "ne remplace pas ce parent" in evolve
    assert "Pas de population lancée d'ici" in evolve


def test_fichier_de_regles_sous_32_kio():
    assert AGENTS.stat().st_size <= PLAFOND_OCTETS
