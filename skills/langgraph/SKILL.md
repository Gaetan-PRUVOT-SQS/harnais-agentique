---
name: langgraph
description: Graphe d'agents LangGraph.js déjà installé. Use for LangGraph, a state graph, a checkpoint, or a durable multi-agent workflow.
---

# LangGraph

Sur cette machine, lire [MACHINE.md](MACHINE.md) avant toute phase. S'il contredit ce fichier, MACHINE.md prime. `~/.agents/AGENTS.md` prime sur les deux.

LangGraph.js est une bibliothèque de graphes avec état. Un nœud lit l'état, le met à jour, et les arêtes décident de la suite. On s'en sert quand le travail est un workflow durable dans un projet. Les délégations de la session restent dans la section Multi-agents. Le serveur YAML reste `agent-orcha`, et seulement si la demande le dit.

## Graphe

Le cas qui tient lieu d'exemple est `tests/fixtures/langgraph_somme.mjs`. Il tourne sans modèle : un nœud ajoute 1, `MemorySaver` garde le fil `preuve`, le résultat est `somme 1`.

`Annotation.Root` décrit l'état. `addNode` et `addEdge` relient les nœuds. `START` et `END` sont les bords. `compile` fige le graphe. Avec un checkpointer, `invoke` reçoit `configurable.thread_id`.

Un appel de modèle attend, dans la même demande, le modèle, le budget, et une clé déjà présente dans l'environnement. On ne lance pas un graphe pour essayer le skill. On n'écrit pas la clé dans un fichier, un journal ou un commit.

## Hors de ce skill

Le CLI `langgraphjs` n'est pas installé. `dev` et `up` ouvrent un serveur. Pas de Docker, pas de LangSmith, pas de trace activée par le skill.
