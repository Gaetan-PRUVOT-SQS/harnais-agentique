"""Contrat visuel : DESIGN.md maison, lu sur une UI."""

from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
DESIGN = RACINE / "DESIGN.md"
AGENTS = RACINE / "AGENTS.md"

TITRES = (
    "## Lecture",
    "## Rôles",
    "## Projet",
    "## Cohérence",
    "## Revue",
    "## Hors pile",
)


def _texte(chemin):
    return chemin.read_text(encoding="utf-8")


def test_design_md_present():
    assert DESIGN.is_file()
    brut = _texte(DESIGN)
    assert brut.startswith("# DESIGN.md\n")
    for titre in TITRES:
        assert titre in brut


def test_maison_sans_marque_inventee():
    brut = _texte(DESIGN)
    assert "n'invente pas de marque" in brut
    assert "Tant que ces champs sont vides, on s'arrête" in brut
    assert "capture de l'app qui tourne" in brut
    assert "sans le nom écrit dedans" in brut
    assert "Pas de connecteur Higgsfield" in brut


def test_agents_pointe_vers_design_md():
    ligne = [
        ligne
        for ligne in _texte(AGENTS).splitlines()
        if "Projet avec une UI" in ligne
    ]
    assert len(ligne) == 1
    assert "`DESIGN.md` à la racine du projet" in ligne[0]
    assert "`~/.agents/DESIGN.md`" in ligne[0]


def test_skills_ui_dans_selon_le_contexte():
    ligne = [
        ligne
        for ligne in _texte(AGENTS).splitlines()
        if ligne.startswith("- Selon le contexte :")
    ]
    assert len(ligne) == 1
    for skill in ("frontend-design", "wcag", "web-design-guidelines"):
        assert skill in ligne[0]


