---
name: orcha
description: Agent Orcha déjà installé (npm agent-orcha). Use for Agent Orcha, agent-orcha, a YAML agent, or a YAML workflow of that server.
---

# Agent Orcha

Sur cette machine, lire [MACHINE.md](MACHINE.md) avant toute phase. S'il contredit ce fichier, MACHINE.md prime. `~/.agents/AGENTS.md` prime sur les deux.

Agent Orcha est un serveur d'agents déclarés en YAML : agents, workflows, connaissances, MCP. Les délégations d'agents de Grok restent celles de la section Multi-agents. L'outil Workflow de Grok reste celui des scripts Rhai déjà là.

## Commande

`agent-orcha` est le binaire npm. Il n'a pas de `--version`.

```
agent-orcha --help
```

`--help`, `-h` et `help` affichent l'usage et sortent. Ils n'écoutent pas et ne créent pas de workspace.

Sans argument, ou avec `start`, le serveur démarre. Seulement si la demande le dit. Dans ce cas : `HOST=127.0.0.1` et `P2P_ENABLED=false`. Le défaut du paquet npm est `0.0.0.0`, port `3333`, et le P2P ouvert. Le détail est dans MACHINE.md.

Une commande inconnue sort 1 et n'écoute pas.

## Workspace

Le défaut est `~/.orcha/workspace` (`WORKSPACE` pour un autre dossier). Le premier `start` y copie des exemples s'il n'y a pas encore `agents/`. On ne le crée pas pour essayer le skill.

Les agents sont des fichiers `agents/*.agent.yaml`. Les workflows sont des YAML à étapes ou ReAct. `models.yaml` décrit les modèles. `mcp.json` décrit les serveurs MCP. On n'écrit pas de clé d'API dans ces fichiers : la valeur vient de l'environnement au moment du `start` demandé.

## Hors de ce skill

Pas de Docker, pas de téléchargement de modèle, pas d'unité systemd. Le réseau P2P (Hyperswarm) reste arrêté tant que la demande ne le demande pas.
