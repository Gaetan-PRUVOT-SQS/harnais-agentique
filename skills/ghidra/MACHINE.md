# Harnais local

Ce fichier prime sur le reste du skill. `~/.agents/AGENTS.md` prime sur ce fichier.

Pratiques communes : `skills/reverse-engineer-anything/MACHINE.md`.

Source : https://github.com/mitsuhiko/agent-stuff, commit `0865c849befd2021490679f96a8dee58c84ac857`, licence Apache-2.0 (`LICENSE`). Dossier amont : `skills/ghidra`.

## Place

Dossier canonique : `~/.agents/skills/ghidra`. Grok lit `~/.agents/skills` directement.

Les scripts `scripts/ghidra-analyze.sh` et `scripts/find-ghidra.sh` sont adaptés : arguments en tableau, projet sous le dossier de sortie, séparateur de `--script-path` en `:`, pas de parcours de tout le home. Les `.java` sont ceux du commit épinglé.

## Quand

Décompiler un binaire local déjà nommé. Ghidra 12.2 est dans `~/.local/opt/ghidra` (lien `current`). Une copie 12.1.4 est à côté pour REA seulement. `find-ghidra.sh` prend `current` avant une autre version du même dossier. Ne pas déplacer `current`, ne pas réinstaller 12.2, ne pas changer le Java par défaut du poste. S'il manque vraiment, le dire et continuer avec `file`, `strings`, `objdump`, `readelf`.

`~/.bashrc` exporte `GHIDRA_HOME` vers `current`. Sans cette variable, `find-ghidra.sh` cherche `$HOME/.local/opt/ghidra` avant `$HOME/ghidra`. Il ne balaie pas le home entier. Le JDK 25.0.5+8 de cette installation est épinglé dans `support/launch.properties`. Le tas headless par défaut est 2G (`GHIDRA_HEADLESS_MAXMEM`). `GHIDRA_MAXMEM` couvre aussi l'interface.

## Cible

La cible est un fichier nommé dans la demande. Le script ne l'exécute pas : il le passe à `-import`.

Pas de choix de binaire à la place de l'auteur, pas de machine distante.

## Preuves

La sortie et le projet Ghidra vont dans le dossier nommé dans la demande, ou `~/rea-evidence/<cible>/`. Le défaut du script est `<sortie>/ghidra-project`. `/tmp` et `/var/tmp` sont refusés.

Ghidra 12.2 refuse un projet dont un élément du chemin commence par un point (`GhidraURL.checkValidProjectPath`). `~/.agents` et `~/.local` ne peuvent pas porter le projet. Le cache interne de Ghidra, lui, se pose dans `/var/tmp/$USER-ghidra`.

Dans un dépôt git, seulement un dossier choisi et ignoré par git. Les essais du wrapper, avec un faux `analyzeHeadless`, restent dans `skills/ghidra/build/`, ignoré. Une vraie analyse ne s'y lance pas.

## Écriture

Un seul écrivain. Pas de workers parallèles, pas de worktree, pas de copie du dépôt. Le skill ne commit pas.

## Délégation

Lecture d'un rapport : `explorateur` ou `chercheur`, un seul niveau. Le parent garde les conclusions et les fichiers.
