---
name: processus-unix
description: >-
  Processus d'un noyau de type Unix : mode utilisateur, ABI des appels système, chargement ELF, fork, exec, wait, signaux, ordonnanceur. Use when implementing processes or syscalls in your kernel.
---

# Processus de type Unix

Un processus, c'est un espace d'adresses, un fil d'exécution, des
descripteurs et un parent. Tout le reste (shell, tuyaux, signaux) se
construit dessus. Chaque étape se prouve par un programme de test en mode
utilisateur lancé dans QEMU.

Voisins : noyau-conception (verrous, erreurs), noyau-securite (entrée
d'appel système, copies user), gestion-memoire (espaces, copie à
l'écriture), fichiers-unix (descripteurs), terminal-unix (sessions),
libc-maison (côté utilisateur), integration-systeme (`qemu-test`),
unix-freebsd-linux (ce que FreeBSD et Linux ont appris).

Mode coach (AGENTS.md) : ordonnanceur et appels système sont écrits par
L'auteur ; l'agent explique, relit, débogue et écrit les programmes de test.

Point de départ : `systeme-maison/templates/unix-like-i686` (noyau qui
reçoit l'initrd, libc avec `int 0x80`, `/init` prêt dans l'initrd, numéros
d'appels dans `abi/syscall.h`).

## Ordre de construction

1. Tâches noyau et bascule de contexte, ordonnanceur coopératif puis
   préemptif sur le timer.
2. Un espace d'adresses par processus, passage en mode utilisateur d'un
   code de test.
3. Appels système : entrée, table, retour ; `write` et `exit` d'abord.
4. Chargeur ELF statique et pile initiale : `/init` lancé depuis l'initrd.
5. `fork` (ou `spawn`), `execve`, `waitpid`, `exit`, zombies, orphelins
   confiés à init.
6. Descripteurs, tuyaux, `dup2` (fichiers-unix) : le shell tourne.
7. Signaux, groupes, sessions, terminal de contrôle.

## Structure de processus

- pid, état (en cours, prêt, bloqué, zombie), parent et enfants, code de
  sortie, espace d'adresses, pile noyau avec garde, contexte sauvé, table
  des descripteurs, dossier courant, uid et gid, masque de signaux,
  signaux en attente, actions, pgid, sid, terminal de contrôle.
- pid croissant qui boucle en sautant ceux en usage ; pid 1 est init.
- Table des processus sous verrou ; ordre des verrous écrit.

## Mode utilisateur par arch

| Arch | Entrée noyau | Retour user | À ne pas oublier |
|------|--------------|-------------|------------------|
| i686 | `int 0x80` (porte DPL 3) ou `sysenter` | `iret` (EIP, CS, EFLAGS avec IF, ESP, SS) | `esp0` et `ss0` du TSS mis à jour à chaque bascule, segments user DPL 3 |
| x86-64 | `syscall` (MSR STAR, LSTAR, SFMASK, EFER.SCE) | `sysret`, ou `iretq` au premier passage | `rsp0` du TSS, `swapgs` si GS porte les données par CPU, RIP canonique avant `sysret` |
| aarch64 | `svc #0`, vecteurs dans `VBAR_EL1` | `eret` (`ELR_EL1`, `SPSR_EL1`) | pile user dans `SP_EL0` |
| riscv64 | `ecall`, `stvec` | `sret` (`sepc`, `sstatus.SPP` à 0) | `sscratch` pour retrouver la pile noyau |

- Tous les registres user sont sauvés dans une trame sur la pile noyau ;
  au retour, aucun registre ne garde une valeur du noyau (noyau-securite).

## ABI des appels système

- Registres (même répartition que Linux, écrite dans l'ABI du projet) :
  i686 `int 0x80` : EAX numéro, EBX ECX EDX ESI EDI EBP, retour EAX ;
  x86-64 `syscall` : RAX, RDI RSI RDX R10 R8 R9 (R10 car `syscall`
  écrase RCX), retour RAX ; aarch64 : x8, x0 à x5, retour x0 ; riscv64 :
  a7, a0 à a5, retour a0.
- Erreur : `-errno`, converti par la libc. Numéros d'appels et d'erreurs
  dans une source unique partagée (libc-maison, `genere-errno`).
- Numéros propres au projet, jamais réutilisés (integration-systeme) ;
  table indexée après borne et masque anti-spéculation (noyau-securite).
- Liste minimale, dans l'ordre d'arrivée : `exit`, `write`, `read`,
  `open`, `close`, `getpid`, `brk` ou `mmap` anonyme, `fork` ou `spawn`,
  `execve`, `waitpid`, `pipe`, `dup2`, `chdir`, `getcwd`, `fstat`,
  `lseek`, `getdents`, `mkdir`, `unlink`, `kill`, `sigaction`,
  `sigprocmask`, `sigreturn`, `setpgid`, `setsid`, `ioctl` (terminal,
  appel interne : la libc expose `tcgetattr` et `tcgetwinsize`),
  `nanosleep`, `clock_gettime`, `uname`.
- Chaque nouvel appel suit les leçons de Linux et FreeBSD
  (unix-freebsd-linux) : argument `drapeaux` avec `EINVAL` sur tout bit
  inconnu, ou structure extensible passée avec sa taille ; `O_CLOEXEC`
  pour tout appel qui crée un descripteur ; forme `*at` pour les chemins.
- Types 64 bits dès le départ, même en i686 : `time_t` (2038, exigé par
  POSIX.1-2024), `off_t`, `ino_t`, `dev_t`. Les élargir plus tard casse
  l'ABI.

## Charger un programme

- ELF statique `ET_EXEC` d'abord : magic, classe, machine, en-têtes
  contenus dans le fichier, segments `PT_LOAD` dans l'espace user, alignés,
  `p_filesz <= p_memsz`, aucun débordement. Chaque segment mappé avec ses
  droits, jamais W et X ensemble ; `.bss` mis à zéro ; entrée `e_entry`.
- Pile initiale (System V ABI), des adresses hautes vers les basses :
  chaînes d'argv et d'envp, 16 octets d'aléa pour `AT_RANDOM`, alignement ;
  puis auxv (paires terminées par `AT_NULL` : `AT_PHDR` 3, `AT_PHNUM` 5,
  `AT_PAGESZ` 6, `AT_ENTRY` 9, `AT_RANDOM` 25), `NULL`, pointeurs envp,
  `NULL`, pointeurs argv, et argc à l'adresse du pointeur de pile, aligné
  sur 16.
- `execve` : construire le nouvel espace à côté et ne détruire l'ancien
  qu'une fois le chargement réussi, sinon l'appelant perd son image sans
  recevoir l'erreur. argv et envp copiés et bornés (`ARG_MAX`) avant.
  Descripteurs `FD_CLOEXEC` fermés, handlers remis à l'action par défaut,
  pid, parent et autres descripteurs gardés.

- Plus tard, bibliothèques partagées : ELF `ET_DYN`, segment
  `PT_INTERP` qui désigne le chargeur dynamique (un programme en espace
  utilisateur), relocations, puis PIE et ASLR (noyau-securite). Tout
  statique d'abord : plus simple, plus sûr, et suffisant.

## fork, exec, wait, exit

- `fork` : copie de l'espace (copie immédiate d'abord, copie à l'écriture
  ensuite : pages partagées en lecture seule, compteur par frame, copie à
  la faute d'écriture), même table de descripteurs (mêmes fichiers
  ouverts, compteurs incrémentés), mêmes masque et actions. 0 pour
  l'enfant, le pid pour le parent.
- `spawn` à la place de `fork` : noyau plus simple, mais il faut passer les
  redirections sous forme de liste d'actions (idée de `posix_spawn`).
  `fork` coûte cher avec un gros espace ou des fils (« A fork() in the
  road », HotOS 2019, qui propose un `spawn` de haut niveau) : `spawn`
  d'abord, `fork` pour la compatibilité.
- Poignée de processus : `spawn` (ou un appel à part) rend un descripteur
  qui désigne l'enfant, idée de `pdfork` (FreeBSD) et des pidfd (Linux).
  Attendre ou tuer par ce descripteur évite la course d'un pid réutilisé.
- Avant `exec`, tout ce qui n'est pas voulu est fermé : `O_CLOEXEC` par
  défaut dans la libc, `closefrom` ou `close_range` pour le reste.
- `exit` : fermer les descripteurs, rendre l'espace, passer zombie avec le
  code, confier les enfants à init, réveiller le parent, SIGCHLD.
- `waitpid` : zombie trouvé, code rendu et structure libérée ; aucun enfant,
  `ECHILD` ; `WNOHANG` ; statut encodé (fin normale, signal, arrêt).
- init ne meurt jamais et récupère les zombies en boucle. Un superviseur
  de services peut devenir « reaper » de ses descendants (idée de
  `PROC_REAP_ACQUIRE` chez FreeBSD, `PR_SET_CHILD_SUBREAPER` chez Linux).
- Sommeil : file d'attente par événement, condition revérifiée en boucle
  après chaque réveil, jamais de sommeil sous spinlock.

## Signaux

- Par processus : masque, signaux en attente, action par signal (défaut,
  ignorer, handler avec masque et `SA_RESTART`).
- Livrés au retour vers le mode utilisateur : premier signal en attente non
  bloqué, action par défaut (terminer, arrêter, continuer, ignorer) ou
  handler.
- Handler : contexte user (registres, masque) sauvé dans une trame sur la
  pile user, retour vers le stub `sa_restorer` qui appelle `sigreturn`.
  `sigreturn` valide la trame avant de la restaurer : une appli ne doit pas
  s'offrir IOPL 3 ni un segment noyau par ce chemin.
- Appel bloquant interrompu : `EINTR`, ou reprise si `SA_RESTART`.
- SIGKILL et SIGSTOP : ni bloqués ni capturés. Faute d'une appli : SIGSEGV,
  SIGILL ou SIGFPE à l'appli ; faute en mode noyau : panique.
- Côté libc (POSIX.1-2024, XSH 2.4.3) : `sigaction` plutôt que `signal`,
  et dans un handler seulement des fonctions async-signal-safe ; `fork`
  n'en fait plus partie, `_Fork` si (skill posix).

## Groupes et sessions

- `setpgid`, `setsid`, terminal de contrôle de la session ; le groupe au
  premier plan reçoit les signaux du clavier ; un groupe en arrière-plan
  qui lit le terminal reçoit SIGTTIN (terminal-unix).

## Ordonnanceur

- Tourniquet avec quantum sur le timer ; priorités plus tard ; tâche idle
  avec `hlt` (os-efficience) ; préemption seulement à des points sûrs au
  début.

## Tester

- Programmes de test user dans l'initrd, lancés par `/init`, chacun écrit
  `[ok] nom` ou `[ko] nom : raison`, puis `PASS` ou `FAIL` ; `qemu-test`
  juge.
- Cas : `fork` mille fois sans fuite de frames (compteurs de
  gestion-memoire), limite de processus, `exec` d'un ELF tronqué
  (`ENOEXEC`, appelant intact), `wait` sans enfant, zombies récupérés,
  orphelins adoptés par init, signal pendant `read` (`EINTR`), trame de
  signal modifiée (refusée), accès à une adresse noyau (SIGSEGV).
- Les mêmes programmes compilés pour Linux sur l'hôte donnent la sortie
  attendue (test différentiel).

## Références

- xv6-riscv et son livre : `proc.c`, `trap.c`, `exec.c`, `syscall.c`
  (licence MIT : lire, ne pas copier).
- System V ABI (pile initiale, auxv) ; POSIX.1-2024 (fork, exec, wait,
  signaux) ; Stevens et Rago, APUE.
- Intel SDM vol. 3 (TSS, SYSCALL et SYSRET), ARM ARM (exceptions),
  RISC-V Privileged (traps).
