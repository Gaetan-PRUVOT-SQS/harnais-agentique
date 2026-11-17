---
name: posix
description: >-
  Appliquer et vérifier POSIX.1-2024 (Issue 8) : lire la norme, C système portable (EINTR, signaux), sh et utilitaires portables, verifier-posix. Use when writing portable C or sh, or checking POSIX.
---

# POSIX.1-2024

POSIX.1-2024, c'est IEEE Std 1003.1-2024, aussi publié comme The Open
Group Base Specifications Issue 8, lisible gratuitement en ligne. C'est la
spec de nos scripts `#!/bin/sh`, du shell maison, de la libc maison et du
noyau de type Unix. Ce skill dit comment la lire, ce qui a changé en 2024
et comment le vérifier.

Voisins : scripts-shell, shell-maison, libc-maison, processus-unix,
fichiers-unix, terminal-unix, unix-freebsd-linux (lecture comparée avec
FreeBSD et Linux), systeme-maison (marque), iso-29119 (les ERRORS
deviennent des cas), make.

## Lire la norme

- pubs.opengroup.org/onlinepubs/9799919799, quatre volumes : XBD
  (définitions, en-têtes), XSH (interfaces système), XCU (shell et
  utilitaires), XRAT (raisons, informatif).
- Une page : SYNOPSIS, DESCRIPTION, RETURN VALUE, ERRORS (« shall fail »
  obligatoire, « may fail » permis), APPLICATION USAGE, RATIONALE, FUTURE
  DIRECTIONS, CHANGE HISTORY (nouveau, obsolescent, retiré).
- Vocabulaire (XBD 1.2 et 1.6) : shall, should, may ;
  implementation-defined, que l'implémentation doit documenter ;
  unspecified, valide mais non documenté ; undefined, rien de garanti. Un
  programme portable ne s'appuie ni sur l'un ni sur l'autre.
- Codes en marge : `[OB]` obsolescent (jamais dans du code neuf), `[XSI]`,
  `[CX]` (extension au C), options comme `[SPN]` (posix_spawn) ou `[SD]`
  (outils de dev, dont make).
- Chercher un mot dans une longue page (l'outil de lecture web tronque) :
  `curl -fsSL URL | sed 's/<[^>]*>//g' | grep -n -i mot`.

## Conformité

- Une implémentation conforme fournit un document de conformité (XBD
  2.1.2) : options prises en charge, valeurs et comportements
  implementation-defined. Côté applis (XBD 2.2) : strictement conforme,
  conforme, conforme avec extensions.
- Macros : `-D_POSIX_C_SOURCE=202405L` (ou `_XOPEN_SOURCE=800` pour XSI).
  glibc les reconnaît depuis 2.43 (celle du poste), sans y rattacher toutes
  les nouveautés : `strlcpy` n'est pas déclaré sous
  `_POSIX_C_SOURCE=202405L` seul (vérifié), et `getconf _POSIX_VERSION`
  rend encore 200809.
- POSIX.1-2024 s'appuie sur C17 : `-std=c17` (l'utilitaire `c17`
  remplace `c99`).
- Options testées à la compilation (`_POSIX_THREADS`, `_POSIX_SPAWN`...) et
  à l'exécution (`sysconf`).
- « POSIX » est une marque de l'IEEE ; seul un produit certifié peut s'en
  réclamer, et la certification actuelle porte sur 1003.1-2016
  (VSX-PCTS2016, VSC-PCTS2016). Chez nous : « compatible avec un
  sous-ensemble de POSIX.1-2024 » (systeme-maison).

## C système

- Retours : chaque appel est testé. `errno` n'a de sens qu'après un échec
  signalé, aucune fonction ne le remet à 0, et sa valeur après un succès
  est non spécifiée : le sauver avant d'appeler autre chose (message).
- Entrées et sorties : `read` et `write` peuvent transférer moins que
  demandé ; un signal avant tout transfert rend -1 et `EINTR`, après un
  transfert rend le compte partiel ; donc une boucle. `EAGAIN` en non
  bloquant remonte à l'appelant. Une écriture de `PIPE_BUF` octets au plus
  n'est pas entrelacée sur un tube ; au-delà de `SSIZE_MAX`, le résultat
  est implementation-defined, donc refusé. Exemple vérifié : `exemples/`
  (6 cas scriptés, 4 Mio sur un vrai tube interrompu par un timer POSIX
  toutes les millisecondes, environ 84 reprises par passage, ASan et
  UBSan, gcc et clang).
- Signaux : `sigaction` (la page de `signal` le recommande ; les effets de
  `signal` sont en partie implementation-defined), `sa_mask`, choix écrit
  de `SA_RESTART`. Dans un handler, seulement les fonctions
  async-signal-safe de XSH 2.4.3 (`write`, `read`, `_exit`, `kill`,
  `waitpid`...), jamais `printf`, `malloc` ni `exit`. En 2024, `fork` sort
  de la liste et `_Fork` y entre. Le handler pose un `volatile
  sig_atomic_t` ou écrit dans un tube.
- Processus : `posix_spawn` (option `[SPN]` ; 2024 ajoute
  `posix_spawn_file_actions_addchdir`, `addfchdir` et
  `POSIX_SPAWN_SETSID`) ou `fork` puis `exec`. Après un `exec` raté,
  l'enfant appelle `_exit`, pas `exit` (tampons stdio vidés deux fois).
  `waitpid` en boucle sur `EINTR`, chaque enfant récupéré, `O_CLOEXEC` et
  `O_CLOFORK` (2024).
- Threads : XSH 2.9.1 liste les fonctions non thread-safe (`strtok`,
  `strerror`, `localtime`, `getopt`, `rand`, `setenv`, `unsetenv`,
  `readdir` sur un même flux...) : variante `_r` ou verrou. Après un
  `fork` dans un processus à threads, rien que de l'async-signal-safe
  avant `exec`.
- Limites : `PATH_MAX` et `NAME_MAX` manquent dans `<limits.h>` quand ils
  dépendent du fichier ; `pathconf` ou `fpathconf` (-1 sans toucher `errno`
  s'il n'y a pas de limite), `sysconf`, `confstr`, `getconf` en shell.
- Chaînes et nombres : `strtol` avec `errno` à 0, `endptr` et `ERANGE` ;
  `<ctype.h>` avec un `(unsigned char)` ; `snprintf` rend la taille
  voulue (troncature si elle atteint la taille du tampon) ; `getline` pour
  les lignes longues ; `strlcpy` et `strlcat` (2024).
- Temps : `clock_gettime(CLOCK_MONOTONIC)` pour mesurer, `nanosleep` ou
  `clock_nanosleep` pour attendre ; `time_t` d'au moins 64 bits exigé.
- Fichiers : `O_CREAT | O_EXCL` pour créer sans écraser, `mkstemp`,
  fonctions `*at`, `rename` atomique, `fsync`. Noms portables : XBD 3.265
  (`A-Z a-z 0-9 . _ -`, pas de tiret en tête) ; `open` doit échouer avec
  `EILSEQ` si le dernier composant n'est pas un nom portable et ne peut
  pas être créé, et est encouragé à refuser un saut de ligne. Un code
  robuste accepte pourtant tout octet sauf `/` et NUL.
- Retiré en 2024, à ne plus utiliser : `gets`, `gettimeofday`,
  `getitimer`, `setitimer`, `ioctl`, `isascii`, `toascii`, `rand_r`,
  `utime`, `ftw` (prendre `nftw`), `tempnam`, `ulimit`, `sighold`,
  `sigignore`, `sigpause`, `sigrelse`, `sigset`, `siginterrupt`,
  `setpgrp`, `_longjmp`, `_setjmp`, `asctime_r`, `ctime_r`. Retiré dès
  2008 : `bzero`, `bcopy`, `bcmp`, `index`, `rindex`, `usleep`, `ualarm`,
  `vfork`, `mktemp`, `getcontext`. Obsolescent : `asctime`, `ctime`,
  `tmpnam`, `inet_addr`, `inet_ntoa`.
- Locale : aucune locale UTF-8 n'est exigée ; la locale POSIX est la
  locale C, à octets. `LC_ALL=C` pour un tri et des messages
  reproductibles.

## Shell et utilitaires (XCU)

- Nouveau en 2024 : `set -o pipefail` (Austin Group Defect 789, dash
  depuis 0.5.13, bash) ; `$'...'` (XCU 2.2.4) ; `read -d` ; `;&` dans
  `case` ; `trap -p` ; `cd -e` ; `test` perd `-a`, `-o` et les
  parenthèses (écrire `[ a ] && [ b ]`) et gagne `-ef`, `<`, `>` ;
  `xargs -0` et `-r` ; `find -print0`, `-iname`, `-mount` ; `sed -E` et
  `s///i` ; `printf` avec `%n$` ; utilitaires `readlink`, `realpath`,
  `timeout`, `gettext`, `ngettext`, `msgfmt`, `xgettext`, `c17`.
- Toujours hors POSIX : `which` (prendre `command -v`), `sed -i`,
  `grep -o`, `find -maxdepth` et `-mindepth`, l'utilitaire `mktemp`,
  `local`, `source`, `declare`, `typeset`, `shopt` (résultat non spécifié,
  XCU 2.9.1.4), `echo` avec option ou antislash (prendre `printf`).
- `pipefail` portable (vérifié sous dash 0.5.13.1 et `bash --posix`,
  `exemples/pipefail.sh`) ; shellcheck 0.11 ne connaît pas encore
  `pipefail` en sh (SC3040), d'où la directive :

```sh
#!/bin/sh
set -eu
# shellcheck disable=SC3040
if (set -o pipefail) 2>/dev/null; then set -o pipefail; fi
```

- Contrôles : le hook lance shellcheck (dialecte du shebang) puis
  `checkbashisms -p` sur tout `#!/bin/sh` (`POSIX KO`). À la main :
  `shfmt -ln posix -fn -d`, `dash -n`, exécution sous `dash` et
  `bash --posix`. Audit du 2026-09-29 : les 13 scripts sh du workflow
  passent les cinq contrôles.
- Limites des outils du poste : shellcheck 0.11 signale `pipefail` en sh
  (SC3040) et checkbashisms 2.26.5 signale `$'...'` ; ils vérifient au
  fond « POSIX d'avant 2024 », ce qui reste un bon critère de portabilité.
  dash 0.5.13 n'a ni `read -d` ni `;&` : un script qui en a besoin passe
  en bash.

## make

- `.POSIX:` en première ligne non commentaire pour demander le
  comportement POSIX. 2024 ajoute `::=`, `:::=`, `?=`, `+=`, `!=`,
  `.PHONY`, `.NOTPARALLEL`, `.WAIT`, `-include`, `$^`, `$+`, `-j` et
  `CURDIR`. Nos Makefile restent en GNU make ; un Makefile qui doit tourner
  partout se limite à ce sous-ensemble.

## POSIX comme spec de son shell et de son OS

- Sous-ensemble choisi et écrit : page `standards(7)` du projet (idée de
  FreeBSD), section STANDARDS dans chaque page de manuel, options et
  valeurs implementation-defined : c'est le document de conformité.
- Pour chaque interface, les « shall fail » de ERRORS deviennent des cas
  de test obligatoires et les « may fail » un choix écrit (base de test,
  iso-29119).
- Signatures et noms d'erreurs vérifiés par `verifier-posix` ; comportement
  comparé à l'hôte (glibc, dash) ; `open_posix_testsuite` de LTP (GPLv2)
  peut servir de banc externe, jamais copié dans le système.
- Shell maison : grammaire de XCU 2.10, expansions dans l'ordre de 2.6,
  recherche de commande de 2.9.1.4 (builtins spéciaux, fonctions,
  utilitaires intrinsèques, puis `PATH`) ; `pipefail`, `$'...'` et
  `read -d` sont à prévoir ; `compare-shells` contre dash 0.5.13.
- Noyau et libc : le terminal passe par `tcgetattr`, `tcsetattr`,
  `tcgetwinsize` et `tcsetwinsize` (2024) ; `ioctl` peut rester l'appel
  système interne, il n'est plus l'interface POSIX.

## verifier-posix

```bash
verifier-posix errno abi/errno.liste [--complet]
verifier-posix entetes libc/include build/include
```

- `errno` : valeurs positives et distinctes (sauf `EAGAIN` et
  `EWOULDBLOCK`, `ENOTSUP` et `EOPNOTSUPP`), noms dans l'espace
  `E[A-Z0-9]*`, extensions listées ; `--complet` exige les 78 noms de
  `<errno.h>` d'Issue 8.
- `entetes` : chaque fonction déclarée dans les `.h` est comparée à la
  référence (en-tête, type de retour, types des paramètres ; noms,
  `restrict` et attributs ignorés, tableau en paramètre lu comme pointeur,
  `unsigned` égal à `unsigned int`). Code 1 sur tout écart.
- Référence : `scripts/reference/errno.txt` (78 noms, page `errno.h`) et
  `scripts/reference/interfaces.tsv` (120 prototypes). Un test compile la
  référence contre la glibc 2.43 du poste avec `__builtin_types_compatible_p` :
  118 confirmés ; `tcgetwinsize` et `tcsetwinsize` manquent à la glibc et
  viennent du texte de POSIX. Ajouter une fonction : une ligne tirée de
  son SYNOPSIS, puis `pytest`.
- Outil lié dans `~/.local/bin`, 11 tests pytest, ruff et mypy strict.
- Gabarit `systeme-maison/templates/unix-like-i686` : `make posix` dans
  `make test`, 0 écart depuis le passage aux types générés (`ssize_t
  write`, `pid_t getpid`).

## Références

- POSIX.1-2024 : pubs.opengroup.org/onlinepubs/9799919799 ; XRAT B.1.1
  (nouvelles fonctions) et A.14 ; austingroupbugs.net.
- dash : git.kernel.org/pub/scm/utils/dash/dash.git ; glibc :
  `include/features.h`.
- Stevens et Rago, *Advanced Programming in the UNIX Environment*.
