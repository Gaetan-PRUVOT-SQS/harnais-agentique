# Harnais local

Ce fichier prime sur le reste du skill. `~/.agents/AGENTS.md` prime sur ce fichier.

## Source

https://github.com/langchain-ai/langgraphjs

Bibliothèque `@langchain/langgraph` `1.5.3`, licence MIT, Node `>=18`. Avec elle : `@langchain/core` `1.3.2`, `zod` `4.6.7`. Le dépôt n'est pas cloné ici.

## Place

Dossier canonique du skill : `~/.agents/skills/langgraph`. Grok lit `~/.agents/skills` directement.

Install : `~/.local/opt/langgraph`. `npm install --ignore-scripts` depuis ce dossier. Le `package-lock.json` fixe l'arbre. Node 24.22.2.

## Quand lancer

Un graphe se lance dans le projet qui le possède, avec le Node du poste, en important cette installation ou les mêmes versions déclarées dans le projet. Le résultat et les checkpoints vont dans le projet, jamais dans `/tmp`.

`MemorySaver` garde l'état en mémoire, le temps du processus. Le paquet sqlite de checkpoint n'est pas installé.

`@langchain/langgraph-cli` n'est pas installé. `langgraphjs dev` et `langgraphjs up` ouvrent un serveur d'API. On ne les ajoute pas sans une demande qui le dit, et l'écoute resterait sur `127.0.0.1`.

La trace LangSmith part seulement si `LANGSMITH_TRACING`, `LANGSMITH_TRACING_V2`, `LANGCHAIN_TRACING` ou `LANGCHAIN_TRACING_V2` vaut `true`. On ne les exporte pas. On ne lit pas la clé, on ne la copie pas.

## Écriture

Un seul écrivain. Pas de workers en parallèle, pas de worktree, pas de copie du dépôt. Le skill ne commit pas.

## Délégation

Lecture d'un rapport déjà écrit : un seul niveau. Le parent garde les conclusions. Un sous-agent ne lance pas un graphe qui appelle un modèle.
