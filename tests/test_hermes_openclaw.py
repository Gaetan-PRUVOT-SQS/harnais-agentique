"""Hermes et OpenClaw : le contrôle qui revient va dans la suite, pas sur une horloge."""

from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
AGENTS = RACINE / "AGENTS.md"
AGILE = RACINE / "skills/pratiques-agiles/SKILL.md"
BOUCLE = RACINE / "skills/tests-regression-auto/SKILL.md"
PLAFOND_OCTETS = 32768


def test_le_controle_qui_revient_entre_dans_la_suite():
    texte = AGENTS.read_text(encoding="utf-8")
    assert "un contrôle qui revient entre dans la suite" in texte
    assert "se relance sans question" in texte
    assert "S'il n'y a rien à ajouter, on le dit en une ligne" in texte
    assert "rien ne s'arme en silence" in texte
    assert "un cas de suite n'en crée pas un autre" in texte


def test_l_horloge_attend_une_demande_et_la_passe_reste():
    texte = AGENTS.read_text(encoding="utf-8")
    assert "Une horloge, un gateway ou une livraison vers un chat" in texte
    assert "attend une demande explicite" in texte
    assert "Pas de tâche de fond" in texte
    assert "pas de boucle de fond" in texte
    agile = AGILE.read_text(encoding="utf-8")
    assert "rien ne s'arme en silence" in agile
    assert "Pas de tâche de fond" in agile
    boucle = " ".join(BOUCLE.read_text(encoding="utf-8").split())
    assert "Cette passe n'ouvre pas de tâche de fond ni de worktree." in boucle
    assert "un cas de suite n'en crée pas un autre" in boucle


def test_fichier_de_regles_sous_32_kio():
    assert AGENTS.stat().st_size <= PLAFOND_OCTETS
