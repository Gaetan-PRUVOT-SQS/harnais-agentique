# Feature : gabarit Unix-like i686

Date : 2026-09-29

## Métier

- Besoin : partir d'un squelette qui tient déjà toute la chaîne d'un
  système de type Unix (noyau, libc, programme utilisateur, initrd, disque,
  chargeur), prouvée par `make test`, pour que l'auteur écrive le cœur
  (mémoire, processus, appels système) sans refaire l'outillage.
- Qui est concerné : L'auteur au démarrage d'un Unix-like (VelumOS ou un
  nouveau projet, décision encore ouverte), l'agent qui en écrit
  l'échafaudage.
- Impact si on ne le fait pas : chaque projet recommence la même plomberie,
  et la première preuve de bout en bout arrive tard.

## Ce qu'on fait

- Comportement visible : `make test` construit, pour les profils debug et
  release, le noyau durci, la libc (`libc.a`, `crt0.o`), `/init` lié sans
  libgcc, l'initrd cpio et l'image disque ; vérifie que les programmes n'ont
  aucun symbole indéfini ; démarre l'image en BIOS (i386) et en UEFI
  (x86_64) jusqu'à `PASS` (série, initrd reçu et reconnu) ; lance
  `make posix` (verifier-posix), puis `licences-tierces`. Environ 10 s
  avec la toolchain déjà construite.
- Le noyau n'exécute pas encore `/init` : mode utilisateur, appels système
  et chargeur ELF sont le cœur à écrire (mode coach), guidés par
  processus-unix.
- Fichiers : `templates/unix-like-i686/` (kernel, libc, abi, user, racine,
  outils, REUSE.toml, LICENSES, Makefile).

## Choix techniques

| Choix | Pourquoi | Alternative rejetée | Impact métier |
|-------|----------|---------------------|---------------|
| Gabarit dans un skill, pas un projet dans `~/Bureau` | VelumOS ou nouveau projet : décision de l'auteur pas encore prise | créer un projet | rien n'est imposé, tout est prêt |
| i686 et Multiboot 1 par Limine | toolchain et gabarit osdev-c déjà vérifiés, démarre en BIOS et en UEFI | x86_64 d'abord | premier Unix sur la cible la plus simple |
| Noyau repris du gabarit osdev-c, plus `initrd.c` | même durcissement, preuve que l'initrd arrive (magic cpio) | noyau vide | la chaîne disque, chargeur, noyau, initrd est prouvée |
| `abi/` partagé (numéros d'appels, liste des erreurs) | une seule source pour noyau et libc | deux copies | l'ABI ne diverge pas |
| `errno` généré, défini en asm | une seule définition du symbole, sans dépendre du compilateur ; valeurs et messages viennent de `abi/errno.liste` | définition en C, listes d'erreurs séparées pour noyau et libc | noyau et libc partagent les mêmes codes |
| Types POSIX générés depuis `abi/types.liste` (`outils/genere-types`, 2026-09-29) | une seule liste pour les types POSIX : comme `errno.h`, ils sont générés dans `build/`, et les prototypes gardent les vrais types (`ssize_t write`, `pid_t getpid`) ; `off_t`, `time_t`, `ino_t`, `dev_t` et `nlink_t` sur 64 bits dès le départ, tailles vérifiées par `_Static_assert` | prototypes en `long` et `int`, ou types écrits à la main | libc conforme aux signatures POSIX, vérifiée par `make posix` (verifier-posix) |
| Appel système `int 0x80`, 4 paramètres | quatre paramètres suffisent pour write, exit, getpid | 6 paramètres | à étendre par une structure quand un appel en demandera plus |
| Programmes liés sans `-lgcc`, `nm -u` vérifié | preuve d'indépendance (systeme-maison) | lier libgcc | toute dépendance cachée casse le test |
| Canari aussi en espace utilisateur (`ssp.c`, `ssp_garde.S`) | les programmes sont compilés durcis comme le noyau | durcir le noyau seul | même niveau partout ; aléa par `AT_RANDOM` plus tard |
| `-z separate-code` pour les programmes | sinon `.rodata` est dans le segment exécutable | laisser le défaut | code, lecture seule et données dans trois segments |
| Build-id dans sa propre section du linker script | sinon la note est jetée (avertissement du linker) | pas de build-id | chaque binaire se retrouve |
| `-nostdinc -isystem libc/include -isystem $(gcc -print-file-name=include)` | nos en-têtes, plus `stddef.h` et `stdint.h` du compilateur | `--sysroot` seul | pas d'en-tête de l'hôte |
| REUSE.toml et LICENSES (GPL-2.0-or-later) | licence de VelumOS ; à changer si le projet en choisit une autre | pas de licence déclarée | `licences-tierces` passe dès le départ |

## Traçabilité

| Fichier | Bloc | Justifié par |
|---------|------|--------------|
| `kernel/initrd.c`, `kernel/multiboot.h` | `initrd_verifier`, structures Multiboot | noyau repris, plus `initrd.c` |
| `abi/syscall.h`, `abi/errno.liste`, `outils/genere-errno` | numéros, erreurs | `abi/` partagé, `errno` généré |
| `libc/errno.S` | symbole `errno` | `errno` généré, défini en asm |
| `abi/types.liste`, `outils/genere-types`, `libc/include/unistd.h` | types POSIX, `ssize_t write`, `pid_t getpid` | types POSIX générés |
| `Makefile` | cible `posix` | types POSIX générés |
| `libc/arch/i686/appel_systeme.c` | `int 0x80` | appel système, 4 paramètres |
| `libc/arch/i686/crt0.S` | `_start` | pile initiale, alignement 16 |
| `libc/ssp.c`, `libc/arch/i686/ssp_garde.S` | canari user | canari en espace utilisateur |
| `user/linker.ld` | base 0x400000, `.note.gnu.build-id` | build-id |
| `Makefile` | `verif-user`, `demarre-bios`, `demarre-uefi`, `licences`, `test` | preuves de `make test` |
| `Makefile` | `-z separate-code`, `-nostdinc` | segments, en-têtes |
