---
name: noyau-conception
description: >-
  Conception d'un noyau hobby en C : invariants et kassert, profils debug et release, verrous, SMP, mémoire, pointeurs user. Use when designing a kernel subsystem or on a deadlock or hang.
---

# Conception du noyau

Un noyau tient par ses invariants. Chaque structure dit ce qui doit rester
vrai, le code le vérifie, et un bug se voit tout de suite au lieu de
corrompre trois sous-systèmes plus loin.

Voisins : osdev-c (roadmap, boot, gabarit), c-bas-niveau (volatile, asm,
UB), noyau-securite (durcissement), os-efficience (performance),
os-confidentialite (isolation), pilotes-materiel, integration-systeme,
unix-freebsd-linux (équivalents FreeBSD et Linux de chaque outil).

Mode coach (AGENTS.md) : mémoire, ordonnanceur et appels système sont
écrits par l'auteur. Ce skill sert à expliquer, relire et déboguer ;
l'agent écrit les tests, les auto-tests et l'échafaudage.

## Invariants et assertions

- Chaque sous-système écrit ses invariants dans sa justification : frame
  jamais dans deux listes, compteur égal au nombre d'éléments, tâche
  courante à l'état « en cours », verrou tenu pendant telle opération.
- `kassert(condition, "pmm: frame deja libre")` est une fonction et non
  une macro à paramètres, donc pas de `__FILE__` ni `__LINE__`. La fonction
  (non inline) passe `__builtin_return_address(0)` à la panique, et
  `addr2line -e kernel.elf ADRESSE` donne le fichier et la ligne
  (`exemples/kassert.c`).
- Vérifications bon marché gardées en release : une panique vaut mieux
  qu'une corruption silencieuse. Vérifications coûteuses (parcourir une
  liste entière) seulement en debug, derrière une constante
  `PROFIL_DEBUG` posée par le Makefile.
- Panique : message, registres, build-id, pile d'appels en suivant la
  chaîne des frame pointers (`-fno-omit-frame-pointer`, EBP ou RBP
  jusqu'à 0), puis arrêt. Double fault sur sa propre pile (noyau-securite).

## Profils

- debug : UBSan en mode piège, vérifications coûteuses, poison mémoire,
  journaux bavards, injection de fautes possible.
- release : même durcissement, vérifications bon marché, journaux coupés.
- `make test` construit et teste les deux (gabarit osdev-c).

## Erreurs

- Trois familles, trois réponses :
  - entrée d'une appli (argument, fichier, format) : code d'erreur,
    jamais de panique ;
  - matériel absent ou en panne : pilote désactivé, message, on continue ;
  - invariant du noyau cassé : panique, c'est un bug du noyau.
- Nuance reprise de Linux, qui déconseille `BUG_ON` : si le dégât reste
  local (un objet, un processus), avertir une fois, refuser l'opération ou
  tuer le processus fautif, et garder la machine en vie. Panique seulement
  quand continuer corromprait le noyau.
- Codes d'erreur négatifs nommés (`E_NOMEM`, `E_INVAL`, `E_PERM`,
  `E_FAULT`), un seul enum partagé avec l'ABI.
- Toute allocation peut échouer et son chemin d'échec se teste : en debug,
  un allocateur qui échoue à la N-ième demande (injection de fautes).
- Pas de `goto` : une fonction par étape d'initialisation et une
  fonction qui défait, dans l'ordre inverse, les étapes réussies.

## Concurrence

- Même sur un seul CPU, une interruption est un second fil d'exécution.
- Chaque donnée partagée a son verrou, nommé d'après elle
  (`g_frames_verrou`), et c'est écrit dans la justification.
- Spinlock noyau : lire EFLAGS, `cli`, prendre le verrou
  (`__atomic_test_and_set` en acquire, `pause` dans la boucle) ; rendre en
  release, puis remettre IF seulement s'il était mis. Jamais un `sti`
  aveugle : l'appelant était peut-être déjà sous `cli`
  (`exemples/verrou.c`, i686).
- Sous spinlock : pas de sommeil, pas de cession du CPU, pas d'allocation
  qui peut attendre, pas de sortie série lente. Une donnée touchée par un
  handler se protège interruptions coupées, sinon le handler attend un
  verrou que le code interrompu ne rendra jamais.
- Ordre global des verrous écrit (par exemple processus, puis espace
  mémoire, puis frames). En debug, chaque verrou a un niveau et prendre un
  niveau plus bas que celui tenu déclenche `kassert` (version réduite de
  `WITNESS` chez FreeBSD et de lockdep chez Linux).
- Deux sortes de verrous, comme `MTX_SPIN` et `MTX_DEF` chez FreeBSD,
  `spinlock_t` et `struct mutex` chez Linux : spin (interruptions coupées,
  section très courte) et dormant (le détenteur peut céder le CPU, jamais
  en interruption). Le verrou dormant arrive avec le premier sommeil qui
  doit tenir un verrou.
- Toute fonction qui peut dormir commence par `kassert` « pas sous
  spinlock, pas en interruption » (idée de `might_sleep` chez Linux) : le
  bug se voit au premier appel, pas au premier blocage.
- Synchroniser avec `__atomic_*` et un ordre mémoire explicite (acquire,
  release), jamais avec `volatile` seul.
- SMP prévu dès le départ : données par CPU derrière un registre (GS en
  x86-64, `TPIDR_EL1` en arm64, `tp` ou `sscratch` en RISC-V), pas de
  globale « CPU courant ». Démarrage des autres cœurs par INIT-SIPI-SIPI
  (x86), PSCI `CPU_ON` (ARM), SBI HSM (RISC-V). Retirer un mappage
  partagé demande d'invalider la TLB des autres cœurs par IPI.

## Mémoire

Détail (carte RAM, zones, mémoire virtuelle par arch, fautes de page,
budget, applis) : gestion-memoire.

- Couches : frames physiques (bitmap ou pile, buddy pour les blocs
  contigus), paging, tas noyau (caches slab par type d'objet fréquent,
  `kmalloc` générique au-dessus).
- En debug : état de chaque objet (libre, occupé) vérifié à chaque
  opération, poison à la libération (motif 0x6B) contrôlé à la
  réallocation, compteurs par cache. Double libération et use-after-free
  deviennent visibles.
- Une pile noyau par tâche, avec une page de garde non mappée dessous : un
  débordement donne une faute de page claire au lieu d'écraser la
  voisine.
- Taille `n * taille` : `__builtin_mul_overflow` avant d'allouer ; plage
  `adresse + longueur` : `__builtin_add_overflow` (`exemples/uptr.c`).
- Pas de récursion, pas de VLA, frames bornées (`-Wframe-larger-than=1024`
  dans le gabarit).
- Page 0 jamais mappée ; mappage identité seulement pendant le boot.

## Temps

- Compteur monotone 64 bits depuis le boot (ticks ou nanosecondes) ;
  jamais l'heure murale pour mesurer une durée.
- Compteur 32 bits qui boucle : comparer par différence signée,
  `(int32_t)(a - b) < 0`.
- Handler du timer court : il réveille, le travail se fait ailleurs.
  Même règle pour tout handler : acquitter, réveiller un fil noyau (idée
  des ithreads de FreeBSD et des IRQ en thread de Linux) ou poser une
  tâche dans une file (`taskqueue(9)`, workqueues).
- Heure murale : lue une fois au boot dans l'horloge temps réel, puis
  avancée par le compteur monotone (`CLOCK_REALTIME` contre
  `CLOCK_MONOTONIC`). PC : CMOS par les ports 0x70 et 0x71, attendre la fin
  du bit « mise à jour en cours » (registre A), format BCD ou binaire et
  12 ou 24 h selon le registre B, lire deux fois jusqu'à obtenir la même
  valeur. QEMU `virt` : PL031 sur ARM (0x09010000), goldfish-rtc sur
  RISC-V (0x101000), adresses à lire dans le DTB (vu dans `info mtree`).
  Pas de `GetTime` UEFI après le boot.

## Frontière user

- Un pointeur venu d'une appli a son propre type,
  `typedef struct s_uptr { uintptr_t adresse; } t_uptr;` : le compilateur
  refuse de le déréférencer. Seules `copier_depuis_user` et
  `copier_vers_user` l'ouvrent, après `uptr_plage_valide` (même idée que
  l'annotation `__user` de Linux, en C pur ; `exemples/uptr.h`). Le
  détail sécurité (SMAP, fautes pendant la copie, spéculation) est dans
  noyau-securite.
- Un appel système : une fonction, validation au début, un seul point de
  sortie qui rend un code.

## Journaux et blocages

- Niveaux (erreur, avertissement, info, debug), préfixe du sous-système
  (`[pmm]`, `[sched]`), debug coupé en release. Un message qu'une appli
  peut déclencher est limité en débit, sinon elle sature la série.
- Aucune adresse noyau en clair dans un message qu'une appli peut lire
  (idée du `%p` haché de Linux) ; journal du noyau réservé à
  l'administrateur.
- Réglages et compteurs exposés par un arbre typé à la `sysctl`
  (unix-freebsd-linux), pas par des messages à analyser.
- Chien de garde logiciel : le timer vérifie que l'ordonnanceur a tourné
  dans les dernières secondes ; sinon il affiche la tâche courante, EIP et
  les verrous tenus au lieu d'un gel muet.

## Tester

- Logique pure sur l'hôte avec sanitizers : allocateurs, files, timers,
  choix de l'ordonnanceur, parseurs (integration-systeme, palier 1).
- Auto-tests au boot en debug : allouer, libérer, réallouer, vérifier
  compteurs et poison ; ordre des verrous.
- Stress : N tâches qui allouent, libèrent et cèdent le CPU pendant M
  secondes ; compteurs cohérents à la fin, aucun `kassert` déclenché.

## Références

- xv6 et son livre (MIT 6.1810) : verrous, sleep/wakeup, interruptions.
- OSTEP (pages.cs.wisc.edu/~remzi/OSTEP) : concurrence et mémoire.
- Bonwick, « The Slab Allocator » (USENIX 1994).
- Linux `Documentation/locking/` (spinlocks, lockdep) : lire, ne pas
  copier.
- Intel SDM vol. 3, « Multiple-Processor Management ».
