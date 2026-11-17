"""Régression de LangGraph.js sur ce poste."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

HOME = Path.home()
NODE = HOME / ".local/share/mise/installs/node/lts/bin/node"
RACINE = HOME / ".local/opt/langgraph"
pytestmark = pytest.mark.skipif(not RACINE.exists(), reason='langgraph posé sous ~/.local/opt/langgraph')
FIXTURE = Path(__file__).resolve().parent / "fixtures/langgraph_somme.mjs"
VERSION = "1.5.3"
CORE = "1.3.2"
ZOD = "4.6.7"


def _env():
    env = os.environ.copy()
    for cle in (
        "LANGSMITH_TRACING",
        "LANGSMITH_TRACING_V2",
        "LANGCHAIN_TRACING",
        "LANGCHAIN_TRACING_V2",
        "LANGSMITH_API_KEY",
        "LANGCHAIN_API_KEY",
        "OPENAI_API_KEY",
    ):
        env.pop(cle, None)
    return env


def _sortie(args, **kwargs):
    return subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
        env=_env(),
        **kwargs,
    )


def test_versions_epinglées():
    manifest = json.loads((RACINE / "package.json").read_text(encoding="utf-8"))
    assert manifest["dependencies"]["@langchain/langgraph"] == VERSION
    assert manifest["dependencies"]["@langchain/core"] == CORE
    assert manifest["dependencies"]["zod"] == ZOD
    installe = json.loads(
        (RACINE / "node_modules/@langchain/langgraph/package.json").read_text(
            encoding="utf-8"
        )
    )
    assert installe["version"] == VERSION
    assert installe["license"] == "MIT"
    verrou = (RACINE / "package-lock.json").read_text(encoding="utf-8")
    assert '"node_modules/@langchain/langgraph"' in verrou
    assert f'"version": "{VERSION}"' in verrou


def test_somme_sans_modele_ni_port():
    avant = _sortie(["ss", "-ltn"]).stdout
    fait = _sortie(
        [str(NODE), "--input-type=module"],
        cwd=RACINE,
        input=FIXTURE.read_text(encoding="utf-8"),
    )
    assert fait.returncode == 0
    assert fait.stdout == "somme 1\n"
    assert fait.stderr == ""
    apres = _sortie(["ss", "-ltn"]).stdout
    assert apres == avant


def test_cli_serveur_absent():
    assert shutil.which("langgraphjs") is None
    binaire = NODE.parent / "langgraphjs"
    assert not binaire.exists()


def test_regle_du_harnais():
    skill = (HOME / ".agents/skills/langgraph/SKILL.md").read_text(encoding="utf-8")
    machine = (HOME / ".agents/skills/langgraph/MACHINE.md").read_text(encoding="utf-8")
    agents = (HOME / ".agents/AGENTS.md").read_text(encoding="utf-8")
    chaine = (HOME / ".agents/memory/machine/toolchain.md").read_text(encoding="utf-8")
    fixture = FIXTURE.read_text(encoding="utf-8")
    assert "name: langgraph" in skill
    assert "tests/fixtures/langgraph_somme.mjs" in skill
    assert "Multi-agents" in skill
    assert "langgraphjs" in skill
    description = next(
        ligne.split(":", 1)[1].strip()
        for ligne in skill.splitlines()
        if ligne.startswith("description:")
    )
    assert len(description) <= 1024
    assert "LangGraph" in description
    assert VERSION in machine
    assert "127.0.0.1" in machine
    assert "LANGCHAIN_TRACING_V2" in machine
    assert "skills/langgraph/MACHINE.md" in agents
    assert "langgraphjs" in agents
    assert "Multi-agents" in agents
    assert VERSION in chaine
    assert '@langchain/langgraph' in fixture
    assert "MemorySaver" in fixture
