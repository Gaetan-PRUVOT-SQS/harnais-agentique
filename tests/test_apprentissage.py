"""Boucle d'apprentissage : plafond, accord, curateur."""

import importlib.util
import json
import sys
from datetime import date
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
BAC = RACINE / "build" / "apprentissage-preuve"
MODULE = RACINE / "skills" / "apprentissage" / "boucle.py"


def _boucle():
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("boucle_apprentissage", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _vide():
    if BAC.exists():
        for chemin in sorted(BAC.rglob("*"), reverse=True):
            if chemin.is_file() or chemin.is_symlink():
                chemin.unlink()
            else:
                chemin.rmdir()
        BAC.rmdir()
    BAC.mkdir(parents=True)


def test_memoire_plafond_et_doublon():
    boucle = _boucle()
    _vide()
    chemin = BAC / "apprentissage.md"
    boucle.ajouter_memoire(chemin, "npm seulement")
    boucle.ajouter_memoire(chemin, "npm seulement")
    assert chemin.read_text(encoding="utf-8") == "npm seulement\n"
    boucle.ajouter_memoire(chemin, "npm")
    assert chemin.read_text(encoding="utf-8") == "npm seulement\nnpm\n"
    with pytest.raises(boucle.Refus):
        boucle.ajouter_memoire(chemin, "x" * boucle.CAP_MEMOIRE)


def test_memoire_borne_exacte_et_entree_vide():
    boucle = _boucle()
    _vide()
    chemin = BAC / "apprentissage.md"
    plein = "a" * (boucle.CAP_MEMOIRE - 1)
    assert boucle.ajouter_memoire(chemin, plein) == plein + "\n"
    assert len(chemin.read_text(encoding="utf-8")) == boucle.CAP_MEMOIRE
    with pytest.raises(boucle.Refus):
        boucle.ajouter_memoire(BAC / "trop.md", "b" * boucle.CAP_MEMOIRE)
    assert not (BAC / "trop.md").exists()
    with pytest.raises(boucle.Refus):
        boucle.ajouter_memoire(BAC / "encore.md", "c" * (boucle.CAP_MEMOIRE + 1))
    assert not (BAC / "encore.md").exists()
    with pytest.raises(boucle.Refus):
        boucle.ajouter_memoire(BAC / "vide.md", "   ")
    assert not (BAC / "vide.md").exists()


def test_profil_plafond():
    boucle = _boucle()
    borne = "p" * boucle.CAP_PROFIL
    assert boucle.borne_profil(borne) == borne
    with pytest.raises(boucle.Refus):
        boucle.borne_profil("p" * (boucle.CAP_PROFIL + 1))


def test_brouillon_sans_accord_ne_cree_pas_la_skill():
    boucle = _boucle()
    _vide()
    corps = "---\nname: pose-locale\n---\n\n# Pose\n"
    dest = boucle.deposer(BAC / "skills", BAC / "journal", "pose-locale", corps, False)
    assert dest == BAC / "journal" / "pose-locale.md"
    assert dest.is_file()
    assert not (BAC / "skills" / "pose-locale").exists()
    assert not (BAC / "journal" / "ledger.jsonl").exists()


def test_accord_pose_la_skill_et_le_journal():
    boucle = _boucle()
    _vide()
    corps = "---\nname: pose-locale\n---\n\n# Pose\n"
    dest = boucle.deposer(BAC / "skills", BAC / "journal", "pose-locale", corps, True)
    assert dest.is_file()
    assert dest.read_text(encoding="utf-8") == corps
    ligne = json.loads((BAC / "journal" / "ledger.jsonl").read_text(encoding="utf-8"))
    assert ligne == {"action": "create", "nom": "pose-locale", "acteur": "agent"}


def test_refus_nom_secret_et_frontmatter():
    boucle = _boucle()
    _vide()
    corps = "---\nname: ok\n---\n"
    with pytest.raises(boucle.Refus):
        boucle.deposer(BAC / "skills", BAC / "journal", "../ok", corps, True)
    with pytest.raises(boucle.Refus):
        boucle.deposer(BAC / "skills", BAC / "journal", "Pose", "---\nname: Pose\n---\n", True)
    with pytest.raises(boucle.Refus):
        boucle.deposer(BAC / "skills", BAC / "journal", "pose-locale", "# sans nom\n", True)
    assert not (BAC / "skills").exists()
    marque = "BEGIN " + "PRIVATE KEY"
    with pytest.raises(boucle.Refus):
        boucle.ajouter_memoire(BAC / "m.md", marque)
    assert not (BAC / "m.md").exists()
    with pytest.raises(boucle.Refus):
        boucle.deposer(
            BAC / "skills",
            BAC / "journal",
            "pose-locale",
            "---\nname: pose-locale\n---\n" + marque + "\n",
            True,
        )
    assert not (BAC / "skills" / "pose-locale").exists()


def test_lien_qui_sort_du_catalogue():
    boucle = _boucle()
    _vide()
    catalogue = BAC / "skills"
    dehors = BAC / "dehors"
    dehors.mkdir(parents=True)
    catalogue.mkdir()
    (catalogue / "pose-locale").symlink_to(dehors, target_is_directory=True)
    corps = "---\nname: pose-locale\n---\n\n# Pose\n"
    with pytest.raises(boucle.Refus):
        boucle.deposer(catalogue, BAC / "journal", "pose-locale", corps, True)
    assert not (dehors / "SKILL.md").exists()
    assert not (BAC / "journal" / "ledger.jsonl").exists()


def test_curateur_agent_seulement():
    boucle = _boucle()
    jour = date(2026, 10, 30)
    user = {
        "created_by": "learn",
        "created_at": "2026-01-01",
        "last_used_at": "2026-01-01",
        "use_count": 0,
    }
    assert boucle.transition(user, jour) == "conserve"
    jeune = {
        "created_by": "agent",
        "created_at": "2026-10-20",
        "use_count": 0,
    }
    assert boucle.transition(jeune, jour) == "active"
    stale = {
        "created_by": "agent",
        "created_at": "2026-09-01",
        "last_used_at": "2026-10-01",
        "use_count": 2,
    }
    assert boucle.transition(stale, jour) == "stale"
    vieux = {
        "created_by": "agent",
        "created_at": "2026-08-01",
        "last_used_at": "2026-08-01",
        "use_count": 1,
        "pinned": True,
    }
    assert boucle.transition(vieux, jour) == "active"
    archive = {
        "created_by": "agent",
        "created_at": "2026-08-01",
        "last_used_at": "2026-08-01",
        "use_count": 1,
    }
    assert boucle.transition(archive, jour) == "archive"


def test_curateur_bornes_14_et_30():
    boucle = _boucle()
    jour = date(2026, 10, 30)

    def fiche(**champs):
        base = {"created_by": "agent", "use_count": 1, "created_at": "2026-08-01"}
        base.update(champs)
        return base

    assert boucle.transition(fiche(last_used_at="2026-10-17"), jour) == "active"
    assert boucle.transition(fiche(last_used_at="2026-10-16"), jour) == "stale"
    assert boucle.transition(fiche(last_used_at="2026-09-30"), jour) == "archive"
    grace = fiche(created_at="2026-10-20", last_used_at="2026-09-01", use_count=0)
    assert boucle.transition(grace, jour) == "active"
    jamais = fiche(created_at="2026-10-16", use_count=0)
    assert boucle.transition(jamais, jour) == "stale"


