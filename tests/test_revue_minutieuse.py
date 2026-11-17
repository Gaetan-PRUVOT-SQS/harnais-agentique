"""Barre ligne à ligne : skill chargé pour tout code, trois questions, voisins."""

from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
SKILL = RACINE / "skills/revue-minutieuse/SKILL.md"
TAXONOMIE = RACINE / "skills/revue-minutieuse/references/taxonomie.md"
OUTILS = RACINE / "skills/revue-minutieuse/references/outils.md"
AGENTS = RACINE / "AGENTS.md"
SENIOR = RACINE / "skills/pratiques-dev-senior/SKILL.md"
REVUE = RACINE / "skills/revue-validation/SKILL.md"
JUSTIFIER = RACINE / "skills/justifier-choix-techniques/SKILL.md"
CODE_REVIEW = RACINE / "skills/code-review/SKILL.md"


def _texte(chemin):
    return chemin.read_text(encoding="utf-8")


def test_skill_present_et_name():
    brut = _texte(SKILL)
    assert brut.startswith("---\nname: revue-minutieuse\n")
    assert "justifier chaque ligne" in brut
    assert "/revue-minutieuse" in brut
    assert TAXONOMIE.is_file()
    assert OUTILS.is_file()


def test_trois_questions():
    brut = _texte(SKILL)
    for mot in ("**Compris**", "**Nécessaire**", "**Vivant**"):
        assert mot in brut
    assert "Un symbole sans raison sort de la liste" in brut
    assert "Le code mort dans le changement est un bloquant" in _texte(REVUE)


def test_charge_pour_tout_code():
    ligne = [
        ligne
        for ligne in _texte(AGENTS).splitlines()
        if ligne.startswith("- Toujours pour du code :")
    ]
    assert len(ligne) == 1
    assert "revue-minutieuse" in ligne[0]
    assert "pratiques-dev-senior" in ligne[0]


def test_voisins_pointent_sans_recopier_le_moteur():
    senior = _texte(SENIOR)
    assert "`revue-minutieuse`" in senior
    assert "Barre ligne à ligne avant d'écrire" in senior
    justifier = _texte(JUSTIFIER)
    assert "`revue-minutieuse`" in justifier
    review = _texte(CODE_REVIEW)
    assert "`revue-minutieuse`" in review
    assert "Map a flow → identify an obligation" not in _texte(SKILL)


def test_taxonomie_classes_et_goto_fail():
    brut = _texte(TAXONOMIE)
    for classe in (
        "Inatteignable",
        "Inutilisé",
        "Sans effet",
        "Commenté",
        "Spéculatif",
        "Doublon",
        "Désactivé",
        "Debug",
        "Pass-through",
        "Valeur morte",
    ):
        assert classe in brut
    assert "CVE-2014-1266" in brut
    assert "CWE-561" in _texte(SKILL)


def test_outils_projet_dabord():
    brut = _texte(OUTILS)
    assert "compilateur et linter **du projet**" in brut
    assert "gcc -Wall -Wextra -Werror" in brut
    assert "knip" in brut
    assert "vulture" in brut
