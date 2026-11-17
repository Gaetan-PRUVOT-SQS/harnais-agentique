---
name: parametres-initiaux-session
disable-model-invocation: true
description: >
  Use when tempted to resume prior work from memory, the workspace, git or a
  previous session without an explicit request, or when the user mentions
  paramètres initiaux, nouveau projet, session vierge.
---

# Paramètres initiaux de session

La règle est dans `~/.agents/AGENTS.md` (section « Langue et échanges ») :
chaque nouvelle conversation part de zéro, sauf reprise explicite. Ce skill
n'en donne que l'application.

## Reprise

Seulement sur « reprends », « continue sur », « on reprend », « resume », ou un
projet nommé. Ambigu : une phrase, reprendre un existant ou partir de zéro ?

## Sans reprise

- Ne pas charger `~/.agents/memory/projets/`, un ancien fil ou des « recent
  sessions » injectées.
- Le dossier courant, les fichiers ouverts et git ne valent pas reprise.
- Ne pas citer « la dernière fois », ni continuer une branche ou une PR d'une
  autre session.
- Les préférences globales et `memory/machine/` restent utilisables.

## En reprise

1. Identifier quel projet reprendre si ce n'est pas clair.
2. Alors seulement, lire `~/.agents/memory/projets/<projet>/` et les fichiers
   désignés par l'auteur.
3. Résumer en deux ou trois lignes l'état repris avant d'agir.
