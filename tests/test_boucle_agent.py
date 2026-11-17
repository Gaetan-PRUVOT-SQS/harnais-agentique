"""Boucle de l'agent : critère, arrêt, échec, plafond du fichier de règles."""

from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
AGENTS = RACINE / "AGENTS.md"
AGILE = RACINE / "skills/pratiques-agiles/SKILL.md"
ORCH = RACINE / "skills/multi-agent-orchestration/SKILL.md"
PLAFOND_OCTETS = 32768


def test_boucle_fixe_le_critere_et_l_arret():
    texte = AGENTS.read_text(encoding="utf-8")
    assert "critère mesurable de la tranche" in texte
    assert "On s'arrête quand il est tenu" in texte
    assert "ne se relance pas tel quel" in texte
    assert "Pas de chantier hors demande" in texte
    assert "pas de boucle de fond" in texte


def test_la_preuve_reste_une_commande():
    texte = AGENTS.read_text(encoding="utf-8")
    assert "Une lecture, un plan ou un résumé n'est pas une vérification" in texte
    assert "Aiguillage :" in texte
    agile = AGILE.read_text(encoding="utf-8")
    assert "critère mesurable de la tranche" in agile
    assert "pas de boucle de fond" in agile
    orch = ORCH.read_text(encoding="utf-8")
    assert "ne se relance pas tel quel" in orch
    assert "Après 2, s'arrêter" in orch


def test_fichier_de_regles_sous_32_kio():
    assert AGENTS.stat().st_size <= PLAFOND_OCTETS
