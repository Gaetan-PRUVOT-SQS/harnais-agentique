---
name: shell-maison
description: >-
  Écrire son propre shell en C : lexer, parser AST, expansions POSIX, fork/exec, tuyaux, redirections, builtins, signaux, compare-shells. Use when writing your own shell in C.
---

# Écrire son shell

Un shell est un petit compilateur (texte, tokens, arbre) collé à un
gestionnaire de processus. Chaque étage se teste seul, et le comportement
se prouve en comparant à un shell de référence.

Voisins :
scripts-shell, systeme-maison (userland sans licence tierce),
noyau-conception (appels système du côté noyau), gestion-memoire (arènes).

Mode coach (AGENTS.md) : l'agent explique, relit, débogue et écrit le banc
de test et les cas ; la logique du shell suit la répartition d'AGENTS.md.

## Choisir son langage

- Sous-ensemble de POSIX : les scripts existants tournent, la spec se lit
  librement (POSIX.1-2024, Shell Command Language), dash sert de référence.
- Langage à soi : plus simple, taillé pour un OS qui n'est pas un Unix
  (VelumOS façon KolibriOS). Il faut alors écrire sa grammaire et ses
  propres cas de test.
- Grammaire du sous-ensemble écrite en EBNF dans la justification avant le
  code.
- Paliers : 1. commandes simples, quotes `'` et `"`, variables, `$?`,
  `<` `>` `>>`, tuyaux, `;` `&&` `||`, builtins `cd` `exit` `export`
  `unset` `pwd`. 2. `if`, `while`, `for`, `case`, fonctions, `$(...)`,
  here-docs. 3. contrôle des tâches, édition de ligne, historique,
  complétion.
- Nouveautés de POSIX.1-2024 à placer dans les paliers : `set -o
  pipefail`, `$'...'`, `read -d`, `;&` dans `case`, `test` sans `-a` ni
  `-o`, recherche de commande avec « utilitaires intrinsèques » (XCU
  2.9.1.4). dash 0.5.13 gère `pipefail` et `$'...'` mais pas `read -d` ni
  `;&` (vérifié) : pour ces deux-là, la référence est bash ou le texte de
  POSIX (skill posix).

## Architecture

Lecture de ligne, lexer, parser, expansions, exécution. Chaque étape a son
entrée et sa sortie testables sans lancer de processus.

- Lexer (POSIX 2.3) : opérateurs, mots, délimiteurs de here-doc. Il garde
  pour chaque caractère s'il était quoté : les expansions en ont besoin.
- Parser : descente récursive, une fonction par règle (liste, and-or,
  pipeline, commande, redirection), grammaire POSIX 2.10 comme source.
  Erreur de syntaxe : message, `$?` à 2, jamais de crash.
- AST : nœuds typés (enum + structure). Tout ce qui sert à une ligne vit
  dans une arène libérée d'un coup après exécution : pas de fuite, pas de
  libération nœud par nœud (gestion-memoire).
- Expansions dans l'ordre POSIX (2.6) : tilde, paramètres, substitution de
  commande, arithmétique ; puis découpage par `IFS` des seuls résultats non
  quotés ; puis globbing ; puis retrait des quotes. La plupart des bugs
  viennent d'un ordre changé ou d'une information de quoting perdue.
- Exécution :
  - builtins spéciaux (`cd`, `exit`, `export`, `unset`, `.`) dans le
    processus du shell, sinon ils n'ont aucun effet ;
  - commande externe : recherche dans `PATH` (fichier exécutable), puis
    `fork` + `execve` sur un Unix. Sur un OS maison, un appel `spawn`
    (chemin, argv, env, descripteurs) est bien plus simple à fournir côté
    noyau et suffit à un shell ;
  - tuyaux : créer les pipes, fermer chaque extrémité inutile dans le
    parent et dans chaque enfant (sinon la fin de fichier n'arrive jamais
    et tout se bloque), attendre tous les enfants, `$?` vient du dernier ;
  - redirections dans l'enfant ; pour un builtin, sauver les descripteurs
    (`dup`), rediriger, puis restaurer ;
  - codes : 127 introuvable, 126 non exécutable, 128 + n tué par le
    signal n, 2 erreur de syntaxe.
- Environnement : tableau `char **` tenu par le shell, variables exportées
  séparées des variables locales, passé à `execve`.
- Mode non interactif (`shell fichier.sh`, `shell -c "..."`) : le même
  code, et c'est lui qui rend les tests possibles.

## Signaux, tâches, terminal

- Interactif : le shell ignore SIGINT et SIGQUIT pour lui-même et remet
  l'action par défaut dans chaque enfant avant `execve`. Ctrl-C au prompt
  donne une nouvelle ligne.
- Handler : une seule globale `volatile sig_atomic_t g_signal`, et
  seulement des appels sûrs en signal (`write`, pas `printf` ni `malloc`).
- Contrôle des tâches : un groupe de processus par pipeline (`setpgid`
  dans le parent et dans l'enfant, pour éviter la course), `tcsetpgrp`
  pour le premier plan, `waitpid` avec `WUNTRACED`, SIGTSTP et SIGCONT.
- Terminal : mode brut (`termios`) seulement pendant l'édition de ligne,
  mode d'origine rendu avant chaque commande et à la sortie. Sur un OS
  maison, la discipline de ligne vit dans le noyau ou dans l'appli
  terminal : le décider.

## Robustesse

- Une fonction par règle de grammaire, une structure de contexte passée
  par pointeur.
- Toute allocation vérifiée ; zéro fuite prouvée (valgrind, ou ASan et
  LSan) ; lignes très longues et entrée coupée (Ctrl-D) gérées.

## Tester

- `compare-shells ./monshell tests/cas [dash]` : chaque `*.sh` passe dans
  les deux shells ; sortie standard, code de retour et présence d'erreurs
  comparés (le texte d'erreur diffère d'un shell à l'autre). Dix cas de
  départ dans `scripts/cas/`, dont `pipefail` et `$'...'` de 2024 ; le
  banc a ses propres tests bats.
- Un cas par piège : quotes imbriquées, `"$@"` vide, `IFS` modifié,
  `'$HOME'`, variable vide non quotée, `2>&1 >f` contre `>f 2>&1`, tuyau de
  cent commandes (descripteurs), commande introuvable dans un tuyau,
  here-doc avec variable et avec délimiteur quoté, `exit` avec code.
- Lexer et parser testés sans processus : chaîne en entrée, AST imprimé
  comparé à l'attendu.
- Fuzz du lexer et du parser sous ASan : entrées aléatoires, jamais de
  crash ni de fuite.
- Un bug trouvé devient un cas dans `tests/cas/`.

## Références

- POSIX.1-2024, Shell Command Language (2.3 tokens, 2.6 expansions, 2.10
  grammaire) : pubs.opengroup.org/onlinepubs/9799919799
- Stevens et Rago, « Advanced Programming in the UNIX Environment »
  (processus, signaux, contrôle des tâches) ; manuel de la glibc,
  « Implementing a Job Control Shell ».
- Sources de dash : à lire pour comprendre, pas à copier (systeme-maison).
