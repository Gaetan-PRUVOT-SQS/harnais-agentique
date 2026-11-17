---
name: libc-maison
description: >-
  Écrire sa libc et son crt0 pour un système maison en C : _start, appels système, errno, malloc, stdio, setjmp, sysroot. Use when writing or debugging a user-space libc for your OS.
---

# Sa propre libc

La libc est le contrat entre les programmes et le noyau : elle traduit
POSIX et C en appels système. On n'écrit que ce dont les programmes du
système ont besoin (shell, init, outils), et chaque fonction se compare à
la glibc de l'hôte.

Voisins : processus-unix (ABI, pile initiale), systeme-maison (pas de copie
de musl ni de newlib), gestion-memoire (malloc), shell-maison,
abi-and-calling-conventions (setjmp), c-bas-niveau, unix-freebsd-linux (interfaces sûres, ABI).

## Ordre

1. `_start` et deux appels système (`write`, `exit`) : un « bonjour »
   statique qui tourne en mode utilisateur.
2. Mémoire et chaînes : `memcpy`, `memmove`, `memset`, `memcmp`, `strlen`,
   `strcmp`, `strncmp`, `strchr`, `strrchr`, `strdup`.
3. `malloc`, `free`, `calloc`, `realloc`.
4. stdio : `FILE`, tampons, `fopen`, `fread`, `fwrite`, `fgets`, `fputs`,
   `snprintf` puis `printf` et `fprintf`, `fflush`.
5. Le reste à la demande des programmes : `getenv`, `strtol`, `atoi`,
   `qsort`, `ctype.h`, `setjmp`, `sigaction`, `opendir`, `readdir`, `time`,
   `getopt` (syntaxe des utilitaires POSIX, unix-freebsd-linux).

## Interfaces sûres d'abord

- Venues des BSD et entrées dans POSIX.1-2024 : `strlcpy` et `strlcat`
  (taille du tampon passée, résultat toujours terminé, retour comparé à la
  taille pour voir la troncature), `reallocarray` (produit vérifié),
  `getentropy` (aléa sans descripteur à ouvrir). Aussi nouveaux dans
  POSIX.1-2024 : `pipe2`, `dup3`, `accept4`, `memmem`, `qsort_r`,
  `posix_getdents`. Hors POSIX mais utiles : `explicit_bzero`
  (effacement que le compilateur ne supprime pas), `arc4random`,
  `closefrom`.
- `O_CLOEXEC` posé par défaut dans ce que la libc ouvre pour elle-même ;
  `fopen` accepte `e` comme la glibc et FreeBSD.
- `time_t` (exigé par POSIX.1-2024), `off_t` et `ino_t` sur 64 bits dès
  le premier en-tête, même en i686.
- Bibliothèques partagées plus tard : versionnement des symboles (idée des
  `Symbol.map` de FreeBSD), un ancien binaire garde l'ancienne version
  d'une fonction dont le comportement change.

## crt0

- Exemple vérifié : `systeme-maison/templates/unix-like-i686/libc/`
  (`crt0.S`, `appel_systeme.c`, `unistd.c`, `errno`, canari).
- Canari des programmes : valeur fixe au départ, puis tirée des 16
  octets d'`AT_RANDOM` par `_start` avant tout appel protégé.
- `_start` en asm court, un par arch : lire argc, argv et envp sur la pile
  (disposition dans processus-unix), aligner la pile sur 16, appeler
  `__libc_init(argc, argv, envp)` (qui pose `environ`), puis
  `exit(main(argc, argv, envp))`. `_start` ne retourne jamais.

## Appels système

- Un stub par arch, avec l'ABI du projet (registres dans processus-unix),
  en asm étendu (c-bas-niveau) ou un seul stub asm générique.
- Retour négatif : `errno = -r` et `-1`. Un seul fil au début ; errno par
  thread (TLS) plus tard.

## errno

Dispositif vérifié dans `exemples/` :

- `errno.liste` : nom, numéro, message. Source unique pour le noyau et la
  libc.
- `genere-errno LISTE build/include` (sh POSIX, propre sous shellcheck,
  checkbashisms, shfmt -fn) écrit `errno.h` (libc, avec `extern int
  errno`), `errno_noyau.h` (les seuls numéros) et `errno_messages.c`. Ce
  sont des fichiers générés dans `build/`, que les contrôles ignorent.
- `errno.S` définit le symbole `errno` en asm, comme `__stack_chk_guard`.
- Le C de la libc (`erreur.c`) ne fait qu'utiliser `errno` ; l'objet
  final n'a aucun symbole indéfini.
- Même méthode pour `environ` et tout nom imposé par C ou POSIX.
- Les types et structures de POSIX (`ssize_t`, `pid_t`, `off_t`, `FILE`,
  `struct stat`, `struct termios`) se génèrent comme `errno.h` depuis une
  liste (fichiers générés dans `build/`). Le gabarit
  `systeme-maison/templates/unix-like-i686` le fait : `abi/types.liste` et
  `outils/genere-types` écrivent `sys/types.h` dans `build/` (tailles
  vérifiées par `_Static_assert`), et `unistd.h` déclare `ssize_t write`
  et `pid_t getpid`.

## Conformité POSIX

- `verifier-posix errno` et `verifier-posix entetes` (skill posix)
  comparent la liste d'erreurs et les prototypes des en-têtes à
  POSIX.1-2024 ; `make posix` du gabarit les lance dans `make test`.
- Ne pas écrire ce que 2024 a retiré (`gets`, `gettimeofday`, `ioctl`
  côté applis, `rand_r`, `ftw`, `utime`, `bzero`, `index`...), et
  marquer thread-unsafe ce que XSH 2.9.1 permet (`strtok`, `strerror`,
  `localtime`, `getopt`).
- Programmes de test compilés avec `-std=c17 -D_POSIX_C_SOURCE=202405L`
  sur l'hôte (glibc 2.43 connaît cette valeur).

## Chaînes et mémoire

- Versions C simples et justes d'abord ; versions rapides seulement si la
  mesure le demande (os-efficience), la version C restant la référence.
- gcc peut reconnaître la boucle d'un `memset` et la remplacer par un
  appel à `memset` : récursion infinie. Compiler la libc avec
  `-ffreestanding -fno-builtin -fno-tree-loop-distribute-patterns`.

## malloc

- Sur `brk` (tas contigu) ou `mmap` anonyme : liste libre avec en-têtes,
  fusion des voisins, alignement 16, grosses demandes directement en pages.
- `calloc` vérifie `n * taille` (`__builtin_mul_overflow`) ;
  `realloc(NULL, n)` vaut `malloc(n)` ; `free(NULL)` ne fait rien ;
  `malloc(0)` rend NULL ou un pointeur unique (choisi et écrit).
- En debug : motifs, compteurs, en-têtes vérifiés (double libération),
  comme le tas noyau (gestion-memoire).

## stdio

- `FILE` : descripteur, tampon, mode (plein ; par ligne pour un terminal,
  détecté par `isatty` ; aucun pour stderr), drapeaux erreur et fin.
- `printf` : format analysé une fois (drapeaux, largeur, précision, `*`,
  longueurs `hh h l ll z`, conversions `d i u x X o c s p %`, flottants
  plus tard ou jamais). `vsnprintf` d'abord, dans un tampon borné, les
  autres par-dessus. Retour : nombre de caractères qui auraient été écrits.
- `exit` : fonctions `atexit` en ordre inverse, `fflush` de tous les flux,
  puis l'appel système.

## setjmp, signaux, locale

- `setjmp` et `longjmp` en asm : registres préservés par l'ABI, pointeur de
  pile, adresse de retour.
- `sigaction` passe au noyau `sa_restorer`, un petit stub qui appelle
  `sigreturn` (processus-unix).
- Locale « C » seulement.

## En-têtes, archive, sysroot

- En-têtes écrits pour le projet (`stdio.h`, `string.h`, `stdlib.h`,
  `unistd.h`, `fcntl.h`, `signal.h`, `sys/types.h`...), prototypes suivant
  POSIX, jamais recopiés de la glibc ou de musl (systeme-maison).
- `libc.a` par `ar rcsD` (déterministe), `crt0.o` à part. Lien d'un
  programme : `-nostdlib -static crt0.o prog.o libc.a` plus les helpers
  maison au lieu de libgcc ; `nm -u` vide.
- Sysroot du projet : `sysroot/usr/include` et `sysroot/usr/lib`.
  Compiler avec `-nostdinc -isystem sysroot/usr/include` tant qu'on se
  sert de `i686-elf-gcc`. Plus tard : toolchain propre à l'OS (page OSDev
  « OS Specific Toolchain ») pour qu'un simple `gcc hello.c` marche.

## Tester

- Sur l'hôte, contre la glibc : compiler nos fonctions à part, préfixer
  leurs symboles (`objcopy --prefix-symbols=m_`), puis comparer `m_memmove`
  à `memmove` sur des entrées aléatoires (tailles 0 à 4096, alignements
  variés, chevauchements), avec ASan.
- Dans l'OS : programmes de test en mode utilisateur (processus-unix),
  sortie comparée au même programme compilé pour Linux sur l'hôte.
- Cas : `printf` aux bornes (`INT_MIN`, `LLONG_MAX`, précision 0,
  `%5.3s`, `%%`), `snprintf` tronqué, `malloc` en stress (contenu
  vérifié), `memmove` chevauchant, `strtol` (bases, débordement, `errno`
  à `ERANGE`).

## Références

- POSIX.1-2024 (interfaces et en-têtes) : pubs.opengroup.org/onlinepubs/9799919799
- C17, bibliothèque standard (brouillon N2176 libre) ; System V ABI (pile
  initiale) ; OSDev : Creating a C Library, OS Specific Toolchain.
- musl et newlib : à lire pour comprendre, pas à copier.
