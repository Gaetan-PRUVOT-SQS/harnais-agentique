# Harnais local

Ce fichier prime sur le reste du skill. `~/.agents/AGENTS.md` prime sur ce fichier.

Pratiques communes : `skills/reverse-engineer-anything/MACHINE.md`.

Source : https://github.com/hackersifu/reverse-engineering-skills, commit `5e675640e0ec94372298c57bb335ecf047360688`, licence MIT (`LICENSE`). Dossier amont : `.agents/skills/re-unpacker`.

## Place

Dossier canonique : `~/.agents/skills/re-unpacker`. Grok lit `~/.agents/skills` directement.

Les marqueurs de citation vides du texte amont ont été retirés.

## Quand

Triage statique d'un binaire qui semble empaqueté : `file`, `strings`, `objdump`, condensats. Le plan dynamique attend une demande qui nomme la cible et l'exécution.

Pas de création de logiciel malveillant, pas de contournement de détection.

## Outils

`file`, `strings` et `objdump` sont déjà sur la machine. Ne pas installer `upx`, `diec`, `capa`, `floss` ou `yara` tant que la demande ne le dit pas. Le passage amont qui propose `apt` ne s'applique pas tout seul.

`upx -d` seulement si les preuves montrent UPX, et seulement sur une copie dans le dossier de preuves.

## Cible

La cible est un fichier nommé dans la demande. Pas d'exécution sur l'hôte. Pas de bac à sable inventé à la place de l'auteur.

## Preuves

Dossier nommé dans la demande, ou `~/rea-evidence/<cible>/`, hors du dépôt. Jamais `/tmp`. Dans un dépôt git, seulement un dossier choisi et ignoré par git.

## Écriture

Un seul écrivain. Pas de workers parallèles, pas de worktree, pas de copie du dépôt. Le skill ne commit pas.

## Délégation

Lecture d'un rapport : `explorateur` ou `chercheur`, un seul niveau. Le parent garde les conclusions et les fichiers.
