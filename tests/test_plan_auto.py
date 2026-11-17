"""Plan court et automatisation : ancres du harnais, plafond du fichier de règles."""

from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
AGENTS = RACINE / "AGENTS.md"
BOUCLE = RACINE / "skills/tests-regression-auto/SKILL.md"
AGILE = RACINE / "skills/pratiques-agiles/SKILL.md"
DEVOPS = RACINE / "skills/pratiques-agiles/references/devops.md"
PLAFOND_OCTETS = 32768


def test_plan_nomme_fichiers_ordre_et_tests():
    texte = AGENTS.read_text(encoding="utf-8")
    assert "fichiers, ordre, tests qui prouvent" in texte
    assert "sans attendre un accord" in texte
    assert "réécrire ce plan" in texte
    assert "Un diff d'une phrase se code directement" in texte
    assert "Une lecture, un plan ou un résumé n'est pas une vérification" in texte


def test_automatisation_reste_la_passe_existante():
    texte = AGENTS.read_text(encoding="utf-8")
    assert "passe après le commit" in texte
    assert "Pas de tâche de fond" in texte
    assert "pas de worktree pour cette passe" in texte
    assert "puis l'automatisation maximale" in texte
    boucle = BOUCLE.read_text(encoding="utf-8")
    assert "Automatisation maximale, après le commit" in boucle
    assert "Cette passe n'ouvre pas de tâche de fond ni de worktree." in boucle
    agile = AGILE.read_text(encoding="utf-8")
    assert "fichiers, ordre, tests qui prouvent" in agile
    assert "Les bandes DORA ne sont pas un quota" in agile
    devops = DEVOPS.read_text(encoding="utf-8")
    assert "ne sont pas un objectif" in devops


def test_fichier_de_regles_sous_32_kio():
    assert AGENTS.stat().st_size <= PLAFOND_OCTETS
