"""Boucle locale calquée sur Hermes : mémoire bornée, brouillon, curateur."""

import json
import re
from datetime import date

CAP_MEMOIRE = 2200
CAP_PROFIL = 1375
JOURS_STALE = 14
JOURS_ARCHIVE = 30
_NOM = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class Refus(Exception):
    pass


def _sans_secret(texte):
    if "PRIVATE KEY" in texte:
        raise Refus("secret")


def ajouter_memoire(chemin, entree):
    entree = entree.strip()
    if not entree:
        raise Refus("entree vide")
    _sans_secret(entree)
    if len(entree) > CAP_MEMOIRE:
        raise Refus("plafond")
    actuel = chemin.read_text(encoding="utf-8") if chemin.is_file() else ""
    if entree in actuel.splitlines():
        return actuel
    nouveau = f"{actuel.rstrip(chr(10))}\n{entree}\n" if actuel else f"{entree}\n"
    if len(nouveau) > CAP_MEMOIRE:
        raise Refus("plafond")
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(nouveau, encoding="utf-8")
    return nouveau


def borne_profil(texte):
    if len(texte) > CAP_PROFIL:
        raise Refus("plafond profil")
    return texte


def _nom_valide(nom):
    if not _NOM.fullmatch(nom):
        raise Refus("nom")


def _dans(racine, cible):
    racine = racine.resolve()
    cible = cible.resolve()
    if racine != cible and racine not in cible.parents:
        raise Refus("chemin")


def deposer(catalogue, journal, nom, corps, approuve):
    _nom_valide(nom)
    _sans_secret(corps)
    if f"name: {nom}" not in corps.split("\n", 20)[0:20]:
        raise Refus("frontmatter")
    if not approuve:
        dest = journal / f"{nom}.md"
        _dans(journal, dest)
        journal.mkdir(parents=True, exist_ok=True)
        dest.write_text(corps, encoding="utf-8")
        return dest
    dest = catalogue / nom / "SKILL.md"
    _dans(catalogue, dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(corps, encoding="utf-8")
    ligne = json.dumps(
        {"action": "create", "nom": nom, "acteur": "agent"},
        ensure_ascii=False,
    )
    journal.mkdir(parents=True, exist_ok=True)
    ledger = journal / "ledger.jsonl"
    with ledger.open("a", encoding="utf-8") as fichier:
        fichier.write(ligne + "\n")
    return dest


def transition(fiche, jour):
    if fiche.get("created_by") != "agent":
        return "conserve"
    if fiche.get("pinned"):
        return "active"
    cree = date.fromisoformat(fiche["created_at"])
    dernier = date.fromisoformat(fiche.get("last_used_at") or fiche["created_at"])
    age = (jour - cree).days
    inutilise = (jour - dernier).days
    if fiche.get("use_count", 0) == 0 and age < JOURS_STALE:
        return "active"
    if inutilise >= JOURS_ARCHIVE and age >= JOURS_STALE:
        return "archive"
    if inutilise >= JOURS_STALE:
        return "stale"
    return "active"
