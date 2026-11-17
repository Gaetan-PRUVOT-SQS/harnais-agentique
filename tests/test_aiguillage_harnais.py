"""Plafond du fichier de règles et aiguillage des orchestrateurs."""

from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
AGENTS = RACINE / "AGENTS.md"
PLAFOND_OCTETS = 32768


def test_fichier_de_regles_sous_32_kio():
    assert AGENTS.stat().st_size <= PLAFOND_OCTETS


def test_aiguillage_des_quatre_portes():
    texte = AGENTS.read_text(encoding="utf-8")
    assert "Aiguillage :" in texte
    assert "délégation de la session reste dans cette section" in texte
    assert "workflow Rhai" in texte
    assert "`agent-orcha`" in texte
    assert "skill `langgraph`" in texte
    assert "sans CLI" in texte
