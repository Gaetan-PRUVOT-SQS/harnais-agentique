"""Régression d'Agent Orcha sur ce poste."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HOME = Path.home()
BINAIRE = HOME / ".local/share/mise/installs/node/lts/bin/agent-orcha"
pytestmark = pytest.mark.skipif(not BINAIRE.exists(), reason='agent-orcha posé via mise')
VERSION = "2026.409.2324"
COMMIT = "ae0ef939ed9a4c1116fe2de652d3e7aa63632750"
LIGNE_HOTE = (
    "const host = process.env['HOST'] ?? (isSea() ? '127.0.0.1' : '0.0.0.0');"
)
LIGNE_P2P = (
    "const p2pEnabled = envP2P !== undefined ? envP2P !== 'false' : savedP2P !== false;"
)


def _env():
    env = os.environ.copy()
    for cle in ("WORKSPACE", "HOST", "PORT", "P2P_ENABLED", "AUTH_PASSWORD"):
        env.pop(cle, None)
    return env


def _sortie(args, timeout=8):
    return subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=_env(),
    )


def _paquet():
    return BINAIRE.resolve().parents[1]


def test_aide_sans_workspace_ni_port():
    avant = _sortie(["ss", "-ltn"]).stdout
    assert not (HOME / ".orcha").exists()
    fait = _sortie([str(BINAIRE), "--help"])
    assert fait.returncode == 0
    assert "Agent Orcha CLI" in fait.stdout
    assert "Start the Agent Orcha server (default)" in fait.stdout
    assert "Server running" not in fait.stdout
    assert "Creating workspace" not in fait.stdout
    assert fait.stderr == ""
    assert not (HOME / ".orcha").exists()
    apres = _sortie(["ss", "-ltn"]).stdout
    assert ":3333" not in apres or ":3333" in avant
    reste = _sortie(["pgrep", "-af", "dist/src/cli/index.js"])
    assert reste.returncode == 1
    assert reste.stdout == ""


def test_version_inconnue_sort_1():
    fait = _sortie([str(BINAIRE), "--version"])
    assert fait.returncode == 1
    assert "Unknown command: --version" in fait.stderr
    assert "Server running" not in fait.stdout
    assert not (HOME / ".orcha").exists()


def test_commande_inconnue_sort_1():
    fait = _sortie([str(BINAIRE), "definitely-not-a-command"])
    assert fait.returncode == 1
    assert "Unknown command: definitely-not-a-command" in fait.stderr
    assert not (HOME / ".orcha").exists()


def test_paquet_epingle_et_defauts():
    paquet = _paquet()
    meta = json.loads((paquet / "package.json").read_text(encoding="utf-8"))
    assert meta["version"] == VERSION
    assert meta["name"] == "agent-orcha"
    start = (paquet / "dist/src/cli/commands/start.js").read_text(encoding="utf-8")
    orchestre = (paquet / "dist/lib/orchestrator.js").read_text(encoding="utf-8")
    assert LIGNE_HOTE in start
    assert LIGNE_P2P in orchestre
    natifs = paquet / "node_modules" / "@agent-orcha"
    assert (natifs / "node-omni-orcha-linux-x64").is_dir()
    assert (natifs / "node-omni-orcha-linux-x64-cuda").is_dir()
    assert not (paquet / "ui").exists()


def test_ancien_paquet_python_absent():
    assert not (HOME / ".local/bin/orcha").exists()
    assert not (HOME / ".local/src/orcha").exists()
    assert not (HOME / ".agents/skills/orcha/bin/orcha").exists()
    fait = subprocess.run(
        [sys.executable, "-c", "import orcha"],
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert fait.returncode != 0
    assert "ModuleNotFoundError" in fait.stderr


def test_regle_du_harnais():
    skill = (HOME / ".agents/skills/orcha/SKILL.md").read_text(encoding="utf-8")
    machine = (HOME / ".agents/skills/orcha/MACHINE.md").read_text(encoding="utf-8")
    agents = (HOME / ".agents/AGENTS.md").read_text(encoding="utf-8")
    chaine = (HOME / ".agents/memory/machine/toolchain.md").read_text(encoding="utf-8")
    assert "name: orcha" in skill
    assert "agent-orcha" in skill
    assert "HOST=127.0.0.1" in skill
    assert "P2P_ENABLED=false" in skill
    assert "python3 -m orcha" not in skill
    description = next(
        ligne.split(":", 1)[1].strip()
        for ligne in skill.splitlines()
        if ligne.startswith("description:")
    )
    assert len(description) <= 1024
    assert "agent-orcha" in description
    assert VERSION in machine
    assert COMMIT in machine
    assert "ddalcu/agent-orcha" in machine
    assert "0.0.0.0" in machine
    assert "P2P_ENABLED=false" in machine
    assert "python3 -m orcha" not in agents
    assert "HOST=127.0.0.1" in agents
    assert "P2P_ENABLED=false" in agents
    assert "skills/orcha/MACHINE.md" in agents
    assert "Multi-agents" in agents
    assert VERSION in chaine
    assert "1.0.0a2" not in chaine
