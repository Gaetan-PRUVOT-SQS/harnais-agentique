---
name: unix-freebsd-linux
description: >-
  Pratiques d'Unix, FreeBSD et Linux pour son propre système : outils, ABI stable, descripteurs et Capsicum, débogage noyau. Use when designing a syscall or interface, or asking how BSD or Linux do it.
---

# Unix, FreeBSD et Linux : ce qu'on reprend

Trois lignées, cinquante ans d'erreurs corrigées. Unix a donné les idées
(fichiers, processus, tuyaux, petits outils). FreeBSD montre un système de
base cohérent et des interfaces propres (Capsicum, kqueue, WITNESS). Linux
apporte une discipline d'ABI stricte et un gros outillage de test et de
débogage du noyau. On reprend les idées, lues dans les manuels, la doc et
les livres, jamais le code (clean room, systeme-maison). Le style du projet
remplace style(9) et le coding-style de Linux.

Voisins : processus-unix, fichiers-unix, terminal-unix, libc-maison,
pile-reseau, noyau-conception, noyau-securite, os-confidentialite,
gestion-memoire, integration-systeme, systeme-maison, shell-maison,
scripts-shell, linux-serveur (l'hôte Fedora).

## Méthode

- Avant de concevoir une interface (appel système, format, outil), lire sa
  page FreeBSD (man.freebsd.org) et Linux (man7.org), puis chercher ce que
  chacun a dû corriger ensuite : appel suffixé `2` ou `at`, drapeau
  ajouté, couche de compatibilité. La version corrigée est souvent la
  bonne base : `openat2` plutôt que `open`, `pipe2` plutôt que `pipe`, une
  poignée de processus plutôt qu'un pid nu.
- La justification note ce que font FreeBSD et Linux, ce qu'on garde et
  pourquoi.
- Quand Linux et FreeBSD divergent, POSIX.1-2024 tranche (skill posix) ;
  s'il se tait, on prend le comportement le plus strict et on l'écrit.

## Tradition Unix

- Un programme fait une chose et la fait bien ; les programmes se
  composent par tuyaux ; le texte ligne par ligne est l'interface commune
  (McIlroy, résumé par Salus en 1994 ; ses maximes d'origine sont dans
  l'avant-propos du Bell System Technical Journal de 1978).
- Silence quand tout va bien ; échec tôt et bruyant, avec un code et un
  message (Raymond, Rules of Silence et of Repair).
- Mécanisme dans le noyau, politique dans l'espace utilisateur : le noyau
  fournit le moyen, init et les outils décident (Rule of Separation).
- Moindre surprise : même option, même sens dans tous les outils.
- Mesurer avant d'optimiser, les données avant les algorithmes (Pike).
- Tout passe par un descripteur : fichiers, tuyaux, sockets, terminaux,
  puis processus et événements.

## Outils de base

- Syntaxe des utilitaires POSIX (XBD 12.2) : options d'une lettre après
  `-`, groupables (`-la`), argument d'option obligatoire, `--` termine les
  options, `-` seul désigne l'entrée ou la sortie standard, options avant
  les opérandes. `getopt` dans la libc maison.
- Données sur stdout, diagnostics sur stderr préfixés du nom de l'outil.
- Codes : POSIX demande 0 pour un succès et plus que 0 pour un échec.
  FreeBSD (style(9)) rend 1 pour tout échec, usage compris ; les outils
  GNU et les builtins du shell rendent souvent 2 pour un mauvais usage.
  On choisit une fois pour tout le système et on l'écrit dans `intro(1)`.
  Pas de `sysexits.h` : FreeBSD le garde seulement pour la compatibilité
  et en déconseille l'usage. Le shell rend 126, 127 et 128 + n.
- Erreur d'écriture vérifiée jusqu'à la fermeture de stdout :
  `outil > /dev/full` doit échouer avec un message. Lecteur parti
  (`outil | head -1`) : sortie discrète, sans message.
- Filtre : lit stdin sans fichier en argument, pas de limite arbitraire de
  longueur de ligne.
- Couleurs et questions seulement si la sortie est un terminal (`isatty`).
- Chaque outil testé contre celui de l'hôte : même entrée, même sortie,
  même code (même idée que compare-shells).

## Pages de manuel

- Une page par outil (section 1 ou 8), appel système (2), fonction de la
  libc (3), périphérique (4), format de fichier (5), sujet général (7),
  interface interne du noyau (9), comme chez FreeBSD. Une interface sans
  page n'est pas finie.
- Format mdoc (sémantique : `.Fn`, `.Fa`, `.Er`), vérifié par
  `mandoc -T lint -W style` (paquet `mandoc` installé sur le poste). Les
  pages font partie du système livré, pas des notes personnelles.
- Exemple vérifié : `exemples/ouvrir.2` (lint propre dans `make test`).

## Appels système et ABI

- Linux : on ne casse pas l'espace utilisateur ; une appli qui marchait
  marche encore après la mise à jour du noyau. FreeBSD : anciens appels
  gardés sous `COMPAT_FREEBSDn`, anciens symboles de la libc gardés par le
  versionnement. Chez nous : numéro jamais réutilisé, sens jamais changé,
  un nouvel appel à côté quand il faut, l'ancien retiré seulement à une
  version majeure annoncée (integration-systeme).
- Règles de `Documentation/process/adding-syscalls.rst` :
  - un argument `drapeaux` dès la première version, et tout bit inconnu
    refusé par `EINVAL`, sinon les applis passent déjà n'importe quoi et
    on ne pourra plus jamais ajouter de drapeau ;
  - ou une structure extensible passée avec sa taille (le document cite
    `perf_event_open` ; `copy_struct_from_user`, depuis Linux 5.4, fait
    la même chose pour `clone3`, `openat2` et `sched_setattr`) : plus
    courte que la première version, `EINVAL` ; plus courte que la nôtre,
    complétée par des zéros ; plus longue, acceptée seulement si le
    surplus est nul, sinon `E2BIG` ; taille plafonnée à une page ;
  - un appel qui crée un descripteur accepte `O_CLOEXEC` ;
  - un appel qui prend un chemin a sa forme `*at` (descripteur de dossier)
    dès le départ ;
  - un argument 64 bits sur une arch 32 bits passe dans une paire de
    registres : l'ABI écrite dit laquelle ;
  - tests et page de manuel livrés avec l'appel.
- Exemple vérifié : `exemples/abi_extensible.c` (drapeaux, structure
  extensible, lecture par `copier_depuis_user` dans le vrai noyau),
  `make -C exemples test` sous ASan et UBSan avec gcc et clang.
- Types assez larges dès le premier jour, même en i686 : `time_t` 64 bits,
  que POSIX.1-2024 exige désormais (2038 : Linux 5.1 a dû ajouter des
  appels time64 pour ses arch 32 bits, et FreeBSD a gardé un `time_t`
  32 bits sur i386 jusqu'au retrait de cette plateforme en 15.0), `off_t`,
  `ino_t`, `dev_t` et `nlink_t` 64 bits
  (FreeBSD 12.0 a dû migrer tout cela d'un coup, « ino64 », en gardant
  l'ancien `stat` sous `COMPAT_FREEBSD11`).
- Une source unique décrit les appels, comme `syscalls.master` chez
  FreeBSD : numéro, nom, arguments typés. Elle génère la table du noyau,
  les stubs de la libc et les noms pour le traceur. Même principe que
  `errno.liste` (libc-maison).
- Numéro d'ABI entier, incrémenté à chaque changement visible (comme
  `__FreeBSD_version`), rendu par `uname`, et porté par chaque binaire dans
  une note ELF (comme `NT_FREEBSD_ABI_TAG`) : le noyau refuse un binaire
  plus récent que lui avec un message.
- Chaque interface a un statut : stable, en test, obsolète, retirée (idée
  de `Documentation/ABI/`). L'API interne du noyau reste libre de changer
  (`stable-api-nonsense.rst`) : tout le code du noyau vit dans l'arbre.
- Réglages et introspection : un arbre typé à la `sysctl` (nom
  hiérarchique, type, lecture seule par défaut, écriture réservée et
  bornée) plutôt que des `ioctl` fourre-tout ou du texte à analyser dans
  `/proc`. `ioctl` reste pour les périphériques, avec un numéro qui encode
  le sens et la taille.

## Descripteurs plutôt que noms globaux

- Un pid nu est une course : il peut être réutilisé entre la lecture et
  `kill`. Poignée de processus : `pdfork`, `pdkill` (FreeBSD) ;
  `pidfd_open`, `pidfd_send_signal`, `CLONE_PIDFD`, `waitid(P_PIDFD)`
  (Linux). Chez nous, `spawn` peut rendre une poignée dès le départ.
- `O_CLOEXEC` partout (`pipe2`, `dup3`, `accept4`, `F_DUPFD_CLOEXEC`,
  `SOCK_CLOEXEC`) : sans lui, un fil qui lance `exec` pendant qu'un autre
  ouvre un fichier fait fuir le descripteur dans le programme lancé.
  `pipe2`, `dup3` et `accept4` sont entrés dans POSIX.1-2024, avec
  `O_CLOFORK` (fermé dans l'enfant d'un `fork`). `closefrom` ou
  `close_range` ferment le reste avant `exec`.
- Résolution bornée : `O_RESOLVE_BENEATH` (FreeBSD) ou `openat2` avec
  `RESOLVE_BENEATH`, `RESOLVE_NO_SYMLINKS` (Linux). Le chemin ne sort du
  dossier donné ni par `..`, ni par un chemin absolu, ni par un lien.
- Une seule attente pour tous les événements : `kqueue` et `kevent` chez
  FreeBSD (descripteurs, processus, signaux, timers, événements user,
  enregistrement et attente dans le même appel). Linux y arrive par
  morceaux (`epoll` plus `signalfd`, `timerfd`, `eventfd`, pidfd). Chez
  nous : `poll` d'abord (POSIX), puis une file d'événements unique.

## Moindre privilège

- Capsicum (FreeBSD) : après `cap_enter`, tout appel qui vise un espace
  de noms global (`open` sans descripteur de dossier, un pid) échoue avec
  `ECAPMODE`. Depuis un descripteur de dossier, un chemin absolu ou un
  `..` qui sortirait de l'arbre échoue avec `ENOTCAPABLE`. Chaque
  descripteur porte des droits que `cap_rights_limit`, `cap_ioctls_limit`
  et `cap_fcntls_limit` ne font que réduire ; un usage hors droits rend
  `ENOTCAPABLE`. Ce qui demande un nom global (DNS, mots de passe,
  fichiers passés en argument) passe par un processus aidant (libcasper :
  `system.dns`, `system.fileargs`...). C'est le modèle le plus proche de
  « l'appli n'a que ce qu'on lui donne » (os-confidentialite) : un droit,
  un descripteur.
- Linux : `no_new_privs` (plus rien ne regagne de droits, même un
  setuid), seccomp (filtre d'appels système), Landlock (restriction de
  fichiers et de réseau posée par un processus sans privilège), espaces de
  noms et cgroups, root découpé en capabilities(7). FreeBSD : jails,
  `securelevel`, framework MAC.
- Chez nous : capacités sur descripteurs à la Capsicum, masque de
  permissions déclaré par l'appli, pas de setuid, et un root découpé en
  droits nommés plutôt qu'un uid 0 tout-puissant.
- Service qui parle au réseau : séparation des privilèges (idée
  d'OpenSSH), un petit processus privilégié, un gros processus sans droits,
  un protocole étroit entre les deux.

## Noyau : outils de débogage

| Besoin | FreeBSD | Linux | Chez nous |
|--------|---------|-------|-----------|
| Assertions | `KASSERT` sous `options INVARIANTS` | `WARN_ON`, `BUG_ON` déconseillé | `kassert`, profil debug (noyau-conception) |
| Ordre des verrous | `WITNESS` | lockdep (`CONFIG_PROVE_LOCKING`) | niveau par verrou, `kassert` en debug |
| Dormir au mauvais endroit | `WITNESS` | `might_sleep` (`CONFIG_DEBUG_ATOMIC_SLEEP`) | `kassert` « peut dormir » en tête de toute fonction bloquante |
| Mémoire | memguard(9), redzone(9) | KASAN, KFENCE, kmemleak | poison, zones témoins, échantillon sur page gardée (gestion-memoire) |
| Injection de fautes | fail(9) | failslab, fail_page_alloc | allocateur qui échoue à la N-ième demande |
| Débogueur | ddb(4) | kdb, kgdb | gdb par QEMU, rien dans une image livrée |
| Traçage | ktrace, truss, DTrace | strace, ftrace, eBPF | traceur d'appels système généré depuis la source unique |
| Fuzz | syzkaller | syzkaller, syzbot | fuzzer d'appels (noyau-securite) |
| Tests | ATF et Kyua, `/usr/tests` | kselftest, KUnit | programmes user jugés par `qemu-test`, auto-tests au boot |

- KFENCE montre l'idée à reprendre en release : une allocation sur N part
  sur une page gardée, coût presque nul, les débordements des vraies
  machines se voient quand même.

## Noyau : conception

| Idée | FreeBSD | Linux | Où chez nous |
|------|---------|-------|--------------|
| Allocation qui dit si elle peut attendre | `M_WAITOK`, `M_NOWAIT` | `GFP_KERNEL`, `GFP_ATOMIC` | gestion-memoire |
| Allocations typées et comptées | `MALLOC_DEFINE` et `vmstat -m`, zones UMA et `vmstat -z` | `/proc/slabinfo` | gestion-memoire |
| Verrou spin ou dormant | `MTX_SPIN`, `MTX_DEF` (propagation de priorité), `sx` si on dort en le tenant | `spinlock_t`, `struct mutex` | noyau-conception |
| Travail hors du handler | ithreads, `taskqueue(9)` | `request_threaded_irq`, workqueues | noyau-conception |
| Statistiques chaudes, références | `counter(9)`, `refcount(9)` | variables par CPU, `refcount_t` saturant | noyau-conception, noyau-securite |
| Lectures fréquentes, écritures rares | `epoch(9)` | RCU | plus tard, si la mesure montre un verrou disputé |
| Ressources d'un pilote | méthodes `attach` et `detach` de newbus | `devm_*` rendues au détachement | pilotes-materiel |
| Échec local | `KASSERT` actif seulement sous `INVARIANTS` | `WARN_ON_ONCE` plutôt que `BUG_ON` | noyau-conception |
| Durcissement | ASLR, `securelevel` | `VMAP_STACK`, `RANDOMIZE_KSTACK_OFFSET`, `INIT_ON_ALLOC_DEFAULT_ON`, `HARDENED_USERCOPY` | noyau-securite |

- Récupérer plutôt que paniquer quand le dégât est local : Linux
  déconseille `BUG_ON` (`deprecated.rst`). Avertir une fois, refuser
  l'opération ou tuer le processus fautif ; panique seulement si continuer
  corrompt le noyau.
- Aucune adresse noyau en clair hors du noyau : `%p` haché chez Linux,
  `kernel.kptr_restrict`, `kernel.dmesg_restrict`.
- Chaînes et tailles (`deprecated.rst`) : copie bornée qui signale la
  troncature (`strscpy` rend `-E2BIG`) ; ni `strcpy`, ni `strncpy` sur une
  chaîne terminée ; `strlcpy` écarté dans le noyau Linux car il lit toute
  la source (il reste utile dans la libc) ; produits de tailles vérifiés
  (`size_mul`, `struct_size`) ; pas de VLA ; tableau flexible `[]` plutôt
  que `[0]` ou `[1]`.

## Système de base

- FreeBSD : noyau, libc, outils, manuels et tests dans un seul arbre,
  construits ensemble (`make buildworld buildkernel`), une version pour
  le tout. Chez nous : un dépôt, une commande, une image. Linux ne livre
  que le noyau et laisse les distributions assembler ; son ABI rigide vient
  de là.
- Arborescence (`hier(7)` chez FreeBSD, FHS chez Linux) : ce qui est livré
  avec le système reste séparé de ce que l'utilisateur ajoute
  (`/usr/local` chez FreeBSD) ; réglages dans `/etc`, données variables
  dans `/var`, temporaire vidé au démarrage. Mettre à jour le système ne
  touche pas aux ajouts. L'arborescence du projet a sa page `hier(7)`.
- Valeurs par défaut séparées des réglages : FreeBSD livre
  `/etc/defaults/rc.conf`, et `/etc/rc.conf` ne contient que les écarts ;
  systemd livre ses unités dans `/usr/lib` et les surcharges vont dans
  `/etc`. Une mise à jour ne demande aucune fusion de fichier de réglages.
- init et services : dépendances déclarées (`PROVIDE`, `REQUIRE`,
  `BEFORE`, triées par `rcorder`) plutôt qu'un ordre numéroté ; un service
  s'active par une ligne (`sshd_enable="YES"`). init récupère les zombies ;
  un superviseur devient « reaper » de ses descendants
  (`procctl(PROC_REAP_ACQUIRE)`, `PR_SET_CHILD_SUBREAPER`).
- Rien n'écoute au premier démarrage : chaque service réseau s'active
  par un choix de l'utilisateur (os-confidentialite).

## Fichiers et durabilité

- Remplacer un fichier sans risque : écrire `nom.tmp` dans le même
  dossier, `fsync`, `rename` vers `nom`, puis `fsync` du dossier. Un
  lecteur voit l'ancien ou le nouveau contenu, jamais un mélange.
- Erreur d'écriture différée : elle arrive après `write`. Depuis 4.13,
  Linux la garde (`errseq_t`) et la rend une fois à chaque fichier ouvert
  au moment de l'erreur (un `dup` partage ce rapport) ; depuis 4.17, une
  erreur jamais vue est aussi rendue au premier fichier ouvert après
  coup. Leçon de « fsyncgate » (PostgreSQL, 2018) : une erreur rendue une
  fois puis oubliée perd des données en silence. Chez nous, l'erreur reste
  sur l'inode et chaque fichier ouvert la reçoit.
- Couche bloc empilable : GEOM chez FreeBSD (fournisseurs et
  consommateurs ; partitions, chiffrement, miroir s'empilent avec la même
  interface), device-mapper chez Linux. Chez nous, une partition est un
  périphérique bloc qui en enveloppe un autre (fichiers-unix).

## Façon de travailler

- Un changement logique par commit ; chaque commit construit et passe les
  tests, pour que la bisection marche (`submitting-patches.rst`).
- Toutes les arch à chaque changement : `make universe` ou `make
  tinderbox` chez FreeBSD (ce dernier résume les échecs et sort en
  erreur), `make test-all` chez nous.
- Une régression est un bug prioritaire (règle « no regressions » de
  Linux) : un test qui passait bloque la livraison tant qu'il échoue.
- Une fonctionnalité arrive avec ses tests et sa page de manuel.
- Tests installés dans l'image (`/usr/tests` et `kyua` chez FreeBSD, qui
  accepte des tests ATF, « plain » ou TAP) : on vérifie un système
  installé, pas seulement l'arbre de build.
- Un seul style pour tout l'arbre : style(9) chez FreeBSD, coding-style
  chez Linux, celui du projet ici.

## Ce qu'on ne reprend pas

- `goto` de nettoyage, macros à paramètres (`container_of`, `KASSERT`),
  habitudes de typedef de Linux : on garde les idées, écrites en
  fonctions (noyau-conception).
- Surengagement mémoire et OOM killer de Linux (gestion-memoire).
- setuid comme mécanisme courant, `ioctl` fourre-tout, `/proc` en texte à
  analyser pour des données structurées.
- `fork` comme seul moyen de lancer un programme : coûteux et piégeux avec
  des fils et de gros espaces d'adresses. « A fork() in the road »
  (HotOS 2019) propose un `spawn` de haut niveau plus des opérations
  bas niveau sur un processus enfant. `spawn` d'abord, `fork` pour la
  compatibilité (processus-unix).

## Références

- FreeBSD : man.freebsd.org, notamment capsicum(4), pdfork(2), kqueue(2),
  witness(4), KASSERT(9), malloc(9), mutex(9), sysctl(9), hier(7),
  rc.subr(8), rcorder(8), style(9), mdoc(7) ; FreeBSD Developers'
  Handbook ; McKusick, Neville-Neil et Watson, *The Design and
  Implementation of the FreeBSD Operating System*, 2e éd., 2014.
- Linux : docs.kernel.org, notamment process/adding-syscalls,
  process/deprecated, process/handling-regressions,
  process/stable-api-nonsense, ABI/, locking/lockdep-design,
  dev-tools/kasan, dev-tools/kfence, dev-tools/kselftest, dev-tools/kunit ;
  man7.org : openat2(2), pidfd_open(2), close_range(2), landlock(7),
  seccomp(2).
- Unix : POSIX.1-2024, XBD 12 « Utility Conventions » ; Kernighan et
  Pike, *The Unix Programming Environment* ; Raymond, *The Art of Unix
  Programming* ; Pike, « Notes on Programming in C » ; Stevens et Rago,
  APUE ; Baumann et al., « A fork() in the road », HotOS 2019.
