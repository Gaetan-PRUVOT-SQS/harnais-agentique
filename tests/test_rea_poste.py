"""Régression de l'installation REA sur ce poste."""

import os
import subprocess
import tomllib
from pathlib import Path

import pytest

HOME = Path.home()
CONFIG = HOME / ".grok" / "config.toml"
GHIDRA = HOME / ".local" / "opt" / "ghidra"
REA = HOME / ".local" / "share" / "mise" / "installs" / "node" / "lts" / "bin" / "rea"
JAVA = HOME / ".local" / "share" / "mise" / "installs" / "java" / "temurin-25.0.5+8.0.LTS"
INSTALL_1214 = GHIDRA / "ghidra_12.1.4_PUBLIC"
REFUS = (
    "Read(**/.env)",
    "Read(**/.ssh/id_ed25519)",
    "Edit(**/.netrc)",
    "Write(**/.aws/credentials)",
    "Bash(python*.env*)",
)


def _config():
    return tomllib.loads(CONFIG.read_text(encoding="utf-8"))


def test_serveur_rea_pointe_ghidra_1214():
    serveur = _config()["mcp_servers"]["rea"]
    assert serveur["command"] == str(REA)
    assert serveur["args"] == ["mcp"]
    assert serveur.get("enabled", True) is True
    env = serveur["env"]
    assert env["GHIDRA_INSTALL_DIR"] == str(INSTALL_1214)
    assert "current" not in Path(env["GHIDRA_INSTALL_DIR"]).parts
    assert env["JAVA_HOME"] == str(JAVA)
    assert "HOPPER_LAUNCHER_PATH" not in env
    assert "REA_JADX_MCP_JAR" not in env
    assert "REA_KUNA_COMMAND" not in env
    version = subprocess.run(
        [str(REA), "--version"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert version.stdout.strip() == "6.8.0"
    assert (GHIDRA / "current").readlink() == Path("ghidra_12.2_PUBLIC")
    props = (INSTALL_1214 / "Ghidra" / "application.properties").read_text(encoding="utf-8")
    assert "application.version=12.1.4\n" in props
    props_22 = (GHIDRA / "ghidra_12.2_PUBLIC" / "Ghidra" / "application.properties").read_text(
        encoding="utf-8"
    )
    assert "application.version=12.2\n" in props_22


def test_refus_de_secrets_et_compat_mcp_intacts():
    data = _config()
    for regle in REFUS:
        assert regle in data["permission"]["deny"]
    assert data["compat"]["claude"]["mcps"] is False
    assert data["compat"]["cursor"]["mcps"] is False


def test_finder_suit_le_lien_current():
    script = HOME / ".agents" / "skills" / "ghidra" / "scripts" / "find-ghidra.sh"
    env = os.environ.copy()
    env.pop("GHIDRA_HOME", None)
    rendu = subprocess.run(
        [str(script)],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert rendu.stdout.strip() == str(GHIDRA / "current" / "support" / "analyzeHeadless")


def test_machine_md_garde_les_limites():
    texte = (HOME / ".agents" / "skills" / "reverse-engineer-anything" / "MACHINE.md").read_text(
        encoding="utf-8"
    )
    assert "Ne pas relancer `rea setup`" in texte
    assert "--install-hopper" in texte
    assert "rea-evidence" in texte
    assert "12.1.4" in texte
    assert "12.2" in texte


PHRASES_PRATIQUE = (
    "SHA-256",
    "observation, inférence, inconnu",
    "On s'arrête dès que la question a sa réponse.",
    "L'original reste intact.",
    "second outil",
    "Pas de résolution DNS",
)

POINTEUR_PRATIQUES = "Pratiques communes : `skills/reverse-engineer-anything/MACHINE.md`."

FICHIERS_POINTEUR = (
    "AGENTS.md",
    "skills/ghidra/MACHINE.md",
    "skills/re-ioc-extraction/MACHINE.md",
    "skills/re-unpacker/MACHINE.md",
)


@pytest.mark.parametrize("phrase", PHRASES_PRATIQUE)
def test_pratique_presente(phrase):
    texte = (HOME / ".agents" / "skills" / "reverse-engineer-anything" / "MACHINE.md").read_text(
        encoding="utf-8"
    )
    assert phrase in texte


@pytest.mark.parametrize("relatif", FICHIERS_POINTEUR)
def test_pointeur_pratiques(relatif):
    texte = (HOME / ".agents" / relatif).read_text(encoding="utf-8")
    assert POINTEUR_PRATIQUES in texte


def test_skill_rea_gere_reste_celui_du_paquet():
    skill = (HOME / ".agents" / "skills" / "reverse-engineer-anything" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert 'version: "49"' in skill
    assert "tool_count: 229" in skill
    assert "On s'arrête dès que la question a sa réponse." not in skill
