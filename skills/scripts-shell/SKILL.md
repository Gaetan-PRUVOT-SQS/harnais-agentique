---
name: scripts-shell
description: >-
  Scripts shell sûrs et portables (bash, sh POSIX) : mode strict, guillemets, erreurs, trap, shellcheck, shfmt, bats, dash. Use when writing or fixing a .sh script, a hook or a Makefile recipe.
---

# Scripts shell

Le shell sert de colle : enchaîner des outils, lancer un build, un test,
une mesure. Il pardonne peu : une variable sans guillemets ou une erreur
avalée au milieu d'un tuyau suffit à effacer le mauvais dossier.

Voisins : norme-cybersecurite (injection, secrets), tests-locaux,
make, linux-serveur, shell-maison (écrire un interpréteur), posix (ce qui
est POSIX.1-2024 ou pas).

## Shell ou autre chose

- Shell pour enchaîner des commandes. Au-delà d'une centaine de lignes, de
  structures de données, de JSON ou de calculs : Python (comme
  `os-mesure`, `ecrire-image`, `licences-tierces`).
- `#!/bin/sh` (POSIX) si le script doit tourner partout : dash, busybox,
  un futur shell maison. `#!/usr/bin/env bash` si l'on veut tableaux,
  `[[ ]]`, `pipefail`. Le shebang le dit toujours.

## Mode strict

- `set -eu` en sh, `set -euo pipefail` en bash (plus
  `shopt -s inherit_errexit` pour que `$(...)` hérite de `-e`).
- `pipefail` est entré dans POSIX.1-2024 (dash depuis 0.5.13). En sh, on
  l'active quand le shell le fournit ; shellcheck 0.11 le croit encore
  hors POSIX, d'où la directive (vérifié, `posix/exemples/pipefail.sh`) :
  `# shellcheck disable=SC3040` puis
  `if (set -o pipefail) 2>/dev/null; then set -o pipefail; fi`.
- Limites de `-e` : ignoré dans une condition (`if f`, `f || g`, `! f`) et
  dans une fonction appelée depuis une condition. Un code de retour qui
  compte se teste explicitement.
- `LC_ALL=C` pour un tri ou une regex reproductible ; `umask 077` si le
  script crée des fichiers privés.

## Variables et guillemets

- Toujours `"$var"`, `"$@"`, `"$(cmd)"`. Sans guillemets : découpage et
  globbing (SC2086), l'erreur shell numéro un. `rm -rf "${dir:?}"/*` :
  `:?` arrête le script si `dir` est vide au lieu de viser `/*`.
- Bash : listes d'arguments en tableau (`opts=(-O2 -g)` puis
  `"${opts[@]}"`), jamais une chaîne découpée. `local` dans les fonctions.
- Minuscules pour les variables du script, majuscules pour l'environnement
  exporté.
- `printf '%s\n' "$x"` plutôt que `echo` (options et `\` non portables).
- `read -r` ; fichiers : `find ... -print0 | xargs -0` ou
  `while IFS= read -r f`, jamais `for f in $(ls)`.
- `$(...)` plutôt que les backticks, `$((...))` pour l'arithmétique ;
  `[ ]` avec `=` en sh, `[[ ]]` en bash. `-a`, `-o` et les parenthèses de
  `test` sont retirés de POSIX.1-2024 : `[ a ] && [ b ]`.
- En sh, seulement des options POSIX : ni `which` (`command -v`), ni
  `sed -i`, ni `grep -o`, ni `find -maxdepth`, ni `echo -n` (`printf`).
  `find -print0 | xargs -0` est POSIX depuis 2024 ; `$'...'` aussi, mais
  checkbashisms le refuse et les shells d'avant 2024 ne le lisent pas :
  `printf` reste plus portable.

## Arguments et erreurs

- Arguments validés au début ; usage sur stderr ; code 2 pour un mauvais
  usage, 1 pour un échec, 127 pour un outil absent.
- Messages d'erreur sur stderr, préfixés du nom du script (`${0##*/}`).
- `--` avant les noms venus de l'utilisateur (`rm -- "$f"`,
  `grep -- "$motif"`) : un nom qui commence par `-` n'est pas une option.
- Dépendance : `command -v outil >/dev/null 2>&1 || { ...; exit 127; }`.
- `cd "$d" || exit 1`, ou un sous-shell `( cd "$d" && ... )`.

## Nettoyage et fichiers

- `trap nettoyer EXIT` (plus `INT TERM` si besoin) pour tuer les processus
  fils et rendre les ressources.
- Fichiers de travail dans le dossier de build du projet (`build/...`,
  ou `mktemp -p build` en bash, `mktemp` n'étant pas un utilitaire
  POSIX), jamais `/tmp` pour du dev ou des tests
  (AGENTS.md). Écriture atomique : `fichier.part` puis `mv`.
- Processus lancés en arrière-plan : attendus (`wait`) ou tués au trap.

## Sécurité

- Jamais `eval` sur une entrée, jamais `curl | sh`, jamais une commande
  construite par concaténation : tableau d'arguments ou `case`.
- Secrets : jamais en argument (visible dans `ps`), jamais sous `set -x`,
  lus depuis un fichier protégé ou un descripteur.
- Droits : `sudo` ou `pkexec` pour la seule commande qui en a besoin.
  Script lancé en root : `PATH` fixé ou chemins absolus.
- Entrée à format attendu : `case` en sh, `[[ $x =~ ^[0-9]+$ ]]` en bash.

## Style

- `shfmt -fn` : tabulations, accolade de fonction à la ligne. C'est le
  style des hooks existants (vérifié par `shfmt -d -fn`).
- Fonctions courtes nommées par un verbe ; `main "$@"` en fin de script
  long.
- Pas de commentaires (règle permanente) : l'usage `-h` documente, les
  raisons vont dans la justification. Seule exception : une directive
  `# shellcheck disable=SCxxxx` sur la ligne concernée, raison écrite
  dans la justification, jamais désactivée pour tout le fichier.

## Contrôles

- Hook : tout `.sh`, `.bash` ou fichier à shebang sh, bash ou dash écrit
  dans un projet passe `shellcheck -S info -x -e SC1091` (SC1091 : source
  dont le chemin vient d'une variable, pas un bug). `SHELLCHECK KO` se
  corrige avant de livrer. Interrupteur : `~/.agents/hooks/disable-shellcheck`.
- Le même hook passe tout `#!/bin/sh` (ou dash) à `checkbashisms -p`
  (mode POSIX strict, sans les tolérances Debian comme `local` ou
  `echo -n`) : `POSIX KO` se corrige, ou le script passe en bash s'il en
  a vraiment besoin.
- À lancer à la main : `shfmt -d -fn`, `shfmt -ln posix` (analyse en
  grammaire POSIX), puis le script sous `dash` et `bash --posix`.
- Tests bats pour un script qui a de la logique (`bats tests/`) : cas
  nominal, mauvais usage, outil absent, noms avec espaces et tirets.
  `bats_require_minimum_version 1.5.0` et `run -127` pour un code attendu
  (exemple complet : `shell-maison/scripts/tests/compare-shells.bats`).

## Makefile

- Recettes avec tuyaux : `SHELL := bash` et
  `.SHELLFLAGS := -eu -o pipefail -c`, sinon l'échec du début d'un tuyau
  passe inaperçu.
- `$(VAR)` pour make, `$$var` pour le shell de la recette.
- Une recette longue devient un script du projet, testé et vérifié par
  shellcheck.

## Références

- POSIX.1-2024, Shell Command Language : pubs.opengroup.org/onlinepubs/9799919799
- ShellCheck wiki (shellcheck.net/wiki), BashPitfalls
  (mywiki.wooledge.org/BashPitfalls), bats-core (bats-core.readthedocs.io).
