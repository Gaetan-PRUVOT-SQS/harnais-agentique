# Harnais local

Ce fichier prime sur le reste du skill. `~/.agents/AGENTS.md` prime sur ce fichier.

Pratiques communes : `skills/reverse-engineer-anything/MACHINE.md`.

Source : https://github.com/hackersifu/reverse-engineering-skills, commit `5e675640e0ec94372298c57bb335ecf047360688`, licence MIT (`LICENSE`). Dossier amont : `.agents/skills/re-ioc-extraction`.

## Place

Dossier canonique : `~/.agents/skills/re-ioc-extraction`. Grok lit `~/.agents/skills` directement.

## Quand

Des preuves sont déjà là : sortie de `strings`, journaux, notes de rétro-ingénierie, condensats. Le skill en tire un tableau et une liste YAML. Chaque indicateur a un extrait verbatim.

Un dépôt source se lit sans ce skill.

## Preuves

Pas d'exécution de l'échantillon. Pas de résolution DNS, pas de visite d'URL, pas d'indicateur inventé.

Les fichiers de chaînes vont dans le dossier de preuves, jamais dans `/tmp`. Le dossier est celui nommé dans la demande, ou `~/rea-evidence/<cible>/`, hors du dépôt. Dans un dépôt git, seulement un dossier choisi et ignoré par git.

## Écriture

Un seul écrivain. Pas de workers parallèles, pas de worktree, pas de copie du dépôt.

Le skill explique. Il ne commit pas.

## Délégation

Lecture d'un rapport : `explorateur` ou `chercheur`, un seul niveau. Le parent garde les conclusions et les fichiers.
