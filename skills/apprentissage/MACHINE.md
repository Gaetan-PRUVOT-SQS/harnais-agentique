# Harnais local

Ce fichier prime sur le reste du skill. `~/.agents/AGENTS.md` prime sur ce fichier.

## Source

Doc Hermes lue le 2026-10-30.

- https://hermes-agent.nousresearch.com/docs/user-guide/features/skills
- https://hermes-agent.nousresearch.com/docs/user-guide/features/memory
- https://hermes-agent.nousresearch.com/docs/user-guide/features/curator

Mémoire agent : 2 200 caractères. Profil : 1 375. Curateur, bloc `config.yaml` : `stale_after_days` 14, `archive_after_days` 30, `interval_hours` 168, `min_idle_hours` 2, `consolidate` faux, pas d'effacement automatique. La même page dit aussi 30 puis 90 jours : on suit le bloc de config, pas cette phrase.

Le dépôt Hermes n'est pas cloné. Le script `install.sh` n'a pas tourné. Pas de gateway, pas de Honcho, pas de GEPA.

## Place

Code : `skills/apprentissage/boucle.py`. Brouillons : `skills/apprentissage/journal/`, ignoré par git. Faits : `memory/global/apprentissage.md`, créé à la première entrée.

## Quand lancer

À la fin d'une feature, si une leçon tient en un fait ou en une procédure. Le module se lance dans le dépôt, avec un dossier de sortie qui est le projet ou `build/`. Jamais `/tmp`.

`deposer(..., approuve=False)` ne crée pas de dossier dans `skills/` hors de ce skill. `approuve=True` seulement si l'auteur a accordé cette skill, ou si la demande en cours le dit.

Le curateur est une fonction. On ne la branche pas sur un minuteur. La consolidation par modèle reste éteinte.

## Écriture

Un seul écrivain. La boucle ne commit pas. Elle ne modifie pas `AGENTS.md`. Elle n'archive pas une skill dont `created_by` n'est pas `agent`.
