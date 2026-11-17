---
name: gestion-memoire
description: >-
  Mémoire d'un OS hobby et de son C : budget mesuré (os-mesure ram), carte RAM, allocateurs, mémoire virtuelle, fautes de page, tas. Use when designing or debugging memory, an allocator or a leak.
---

# Gestion de la mémoire

La RAM est ce que VelumOS promet d'économiser (Fast) et l'endroit où une
fuite de données casse la promesse Private. Chaque octet a un
propriétaire, une raison d'être et un budget.

Voisins : noyau-conception (couches, poison, pages de garde, `kassert`),
noyau-securite (W^X, NX, tas durci), os-confidentialite (pages à zéro),
os-efficience (mesures, budgets de taille), pilotes-materiel (carte du
firmware, DMA, MMIO), c-bas-niveau, valgrind, sanitizers.

Mode coach (AGENTS.md) : allocateur physique, paging et tas sont écrits par
L'auteur. L'agent explique, relit, prépare les tests hôte, les auto-tests et
les mesures.

## Principes

- Chaque allocation a un propriétaire (sous-système ou appli) et entre dans
  ses compteurs.
- Connu à la compilation : statique. Dépend de la machine : découvert.
  Dépend de l'appli : déclaré dans son en-tête et plafonné.
- Toute allocation peut échouer ; son chemin d'échec est testé.
- On mesure avec des compteurs, pas à l'impression.

## Budget mémoire

`docs/budget-memoire.md` du projet (local) : une ligne par poste, avec le
budget, la mesure, la date et le commit.

| Poste | Comment le chiffrer |
|-------|---------------------|
| Image noyau (text, rodata, data, bss) | `os-mesure taille kernel.elf --budget OCTETS` |
| RAM minimale pour démarrer | `os-mesure ram kernel.elf --budget MIO` (dichotomie sur `-m`) |
| Structures de l'allocateur physique | bitmap : RAM / 4096 / 8 octets (32 Kio pour 1 Gio) |
| Tables de pages | une table de 4 Kio par 4 Mio mappés en i686 sans PAE, compter selon la carte |
| Framebuffer | largeur × hauteur × octets par pixel : 1024 × 768 × 4 = 3 Mio, plus que tout le gabarit noyau ; double tampon compris |
| Piles | par tâche (4 à 16 Kio) + page de garde |
| Tas noyau au repos | compteur du tas après le boot |
| Applis | ce qu'elles déclarent, plafonné |

- Le noyau publie une ligne série stable, au boot et à la demande :
  `[mem] total=... libre=... noyau=... tables=... tas=... fb=...` (en Kio).
  Le harness de test peut la comparer aux budgets.
- Dépassement : visible au test, relevé seulement avec le chiffre et la
  raison dans la justification (os-efficience).
- Repère : KolibriOS annonce 8 Mo minimum ; le gabarit osdev-c démarre avec
  2 Mio (mesuré le 2026-09-29 par `os-mesure ram`).

## RAM physique

- Sources : Multiboot 1 et 2, Limine memmap, UEFI `GetMemoryMap`, DTB
  (`/memory`, `/reserved-memory`, `/memreserve/`). Normaliser (trier,
  fusionner, arrondir à 4 Kio vers l'intérieur) comme dans
  pilotes-materiel.
- Types : utilisable ; réservé ; ACPI reclaimable (après lecture des
  tables) ; ACPI NVS (jamais) ; RAM défectueuse (jamais) ; mémoire du
  chargeur (bootloader-reclaimable de Limine, BootServices d'UEFI après
  `ExitBootServices`) ; framebuffer ; modules. Ne rendre libre que ce qui
  est prouvé libre.
- Déjà occupé au boot : l'image du noyau, sa pile, les modules, les infos
  du chargeur. Copier ce qui sert avant de réutiliser leur mémoire.
- Allocateur de démarrage : simple pointeur qui avance dans une zone libre,
  le temps de construire les structures de l'allocateur physique, puis
  hors service.
- Allocateur physique :
  - pile de frames : O(1), très simple, pas de blocs contigus ;
  - bitmap : 1 bit par frame, blocs contigus possibles, recherche
    linéaire (garder un indice de départ) ;
  - buddy : blocs de 2^n pages, fusion rapide, plus de code.
  Partir simple, passer au buddy quand le DMA contigu ou les grandes pages
  l'exigent.
- Zones : sous 1 Mio (trampoline de démarrage des autres cœurs x86 : en
  réserver une page), sous 16 Mio (DMA ISA), sous 4 Gio (DMA 32 bits), le
  reste. Servir d'en haut pour garder le bas, qui est rare.
- Une frame se manipule par son numéro (PFN) ; la conversion physique vers
  virtuel est à un seul endroit.
- En debug : libres + utilisées = total, vérifié par `kassert`.

## Mémoire virtuelle

- Carte d'adresses écrite par arch, en constantes d'un en-tête `layout.h`
  et dans la justification : applis en bas (page 0 exclue), noyau en haut,
  puis image, carte directe de la RAM ou fenêtres, tas noyau, MMIO, piles
  avec gardes, framebuffer.
- i686 : 2 niveaux, pages de 4 Kio, PSE en 4 Mio ; PAE en 3 niveaux
  (entrées 64 bits, NX). 1 Gio pour le noyau : pas de carte directe de
  toute la RAM au-delà d'environ 900 Mio, donc des fenêtres temporaires.
  Sans PAE, la RAM au-dessus de 4 Gio est hors d'atteinte : l'annoncer.
- x86-64 : 4 niveaux (48 bits), 5 avec LA57 ; adresses canoniques ;
  carte directe fournie par le HHDM de Limine.
- arm64 : granule 4 Kio, 4 niveaux, TTBR0 pour les applis et TTBR1 pour
  le noyau, attributs par MAIR.
- RISC-V : Sv39 (3 niveaux) ou Sv48, registre `satp`. Certains cœurs ne
  gèrent pas les bits A et D : les poser à la création de l'entrée pour
  éviter des fautes.
- Tables de pages prises dans l'allocateur physique, mises à zéro, comptées
  dans le budget. Une seule façon d'y accéder (mappage récursif en 32 bits
  ou carte directe en 64 bits), cachée derrière quelques fonctions.
- TLB invalidée après chaque changement (`invlpg`, `tlbi`, `sfence.vma`),
  et sur les autres cœurs en SMP (noyau-conception).
- Attributs par zone : text RX, rodata R, data RW sans exécution, MMIO non
  cacheable, framebuffer en write-combining, pages d'applis avec U/S.

## Fautes de page

- Lire l'adresse (CR2, `FAR_EL1`, `stval`) et la cause, puis trancher :
  - accès noyau illégal : panique avec l'adresse et l'instruction ;
  - accès d'appli illégal : l'appli est arrêtée, le noyau continue ;
  - page légale pas encore là (allocation paresseuse) : allouer, mettre à
    zéro, mapper, reprendre.
- Commencer par tout mapper au chargement, plus simple. Allocation
  paresseuse, copie à l'écriture et fichiers mappés viennent ensuite, si la
  mesure le justifie.
- Faute pendant une copie user : table d'exceptions (noyau-securite).

## Tas noyau

- Caches slab pour les objets fréquents (tâche, fenêtre, table de pages),
  `kmalloc` en classes de taille (16, 32, jusqu'à 2048) au-dessus, pages
  entières au-delà. Alignement d'au moins 16.
- Objets à longue et courte durée de vie dans des caches séparés ;
  fragmentation mesurée (plus grand bloc libre sur libre total).
- Pas d'allocation dans un handler d'IRQ, ou un pool préalloué.
- Chaque demande dit si elle peut attendre, comme `M_WAITOK` et
  `M_NOWAIT` chez FreeBSD, `GFP_KERNEL` et `GFP_ATOMIC` chez Linux. Avec
  attente : interdit sous spinlock et en interruption. Sans attente : peut
  échouer, et ce chemin est testé.
- Chaque demande porte un type nommé par propriétaire (idée de
  `MALLOC_DEFINE`) ; une commande à la `vmstat -m` affiche octets et
  nombre d'objets par type. C'est la preuve du budget poste par poste.
- Debug : poison, zones témoins avant et après chaque bloc vérifiées à la
  libération, compteurs par cache, liste des blocs vivants avec l'appelant
  (`__builtin_return_address`) pour retrouver une fuite.
- Release : échantillonnage à la KFENCE (Linux) ; une allocation sur N part
  seule sur une page encadrée de pages de garde. Coût presque nul, et un
  débordement sur une vraie machine donne une faute nette.

## Mémoire des applis

- L'en-tête d'appli déclare sa mémoire et sa pile (idée des champs de
  MENUET01 chez KolibriOS). Le noyau plafonne, compte par appli et reprend
  tout à la sortie.
- Espace d'adresses décrit par une liste de régions (code, données, tas,
  pile, partagé) ; pile avec page de garde.
- Agrandir le tas : appel système plafonné par le quota, pages à zéro.
- Mémoire partagée (IPC, tampon d'une fenêtre) : comptée chez le créateur,
  droits explicites (os-confidentialite).
- Pas de surengagement : ce qui est promis existe. Mémoire épuisée :
  `E_NOMEM` et l'appli décide. Le noyau garde une petite réserve pour
  pouvoir arrêter une appli et afficher un message.

## Intégration avec le matériel

- Caches x86 : MTRR posés par le firmware (les lire, ne pas les casser),
  PAT pour le write-combining. Jamais la même page physique mappée avec
  deux types de cache différents.
- Trou PCI sous 4 Gio : QEMU `pc` avec `-m 4G` met 3 Gio sous 4 Gio et
  1 Gio au-dessus (vu dans `info mtree -f`). La carte du firmware le dit ;
  le noyau ne suppose jamais une RAM continue.
- DMA : zones et contiguïté (pilotes-materiel).
- TLB : grandes pages pour la carte directe et le framebuffer
  (os-efficience).
- NUMA : ignoré sur un PC de bureau, noté si une machine de test en a.

## Vraie RAM

- Machine instable : tester la RAM avant d'accuser le noyau.
  `ecrire-image /usr/share/memtest86+/memtest86+x64.iso
  /dev/disk/by-id/usb-...` (memtest86+ 8.10, GPL, installé), résultat dans
  la fiche matériel.
- ECC : les erreurs arrivent par Machine Check (`#MC`) sur x86 ; le
  handler affiche la banque et l'adresse au lieu d'un redémarrage muet.
- Contenu de la RAM au démarrage : quelconque, jamais zéro garanti, et il
  survit un peu à un redémarrage (rémanence). Effacer les pages et les
  secrets (os-confidentialite).
- Rowhammer : des accès répétés peuvent faire basculer des bits voisins.
  Hors de portée d'une parade complète ici ; au moins, tables de pages et
  données noyau jamais partagées avec une appli.
- Bande passante et latence : banc C sur l'hôte (grosse copie, parcours
  aléatoire), `perf stat -e cache-misses:u`. Sous QEMU ces chiffres ne
  valent rien.
- Inventaire de la RAM d'une machine cible : `dmidecode -t memory` (root,
  depuis un Linux live) donne type, vitesse et ECC.

## C : ingénierie mémoire

- Propriété écrite : qui alloue libère. Une fonction qui rend de la mémoire
  à libérer le dit dans son nom (`creer_`, `dupliquer_`), avec sa
  `detruire_` symétrique.
- Grouper par durée de vie : arène (pointeur qui avance, remise à zéro
  globale) pour ce qui meurt ensemble ; pool de taille fixe pour les objets
  nombreux ; `malloc` au cas par cas en dernier.
- `size_t` pour les tailles, `__builtin_mul_overflow` avant `n * taille`.
- Disposition : champs du plus grand au plus petit (moins de remplissage,
  `pahole -C nom_struct fichier.o`), tableau de structures ou structure de
  tableaux selon le parcours, données chaudes contiguës.
- Vérifier : ASan et LSan, valgrind memcheck ; profil du tas avec
  `valgrind --tool=massif` puis `ms_print` (pic, qui alloue) ;
  `-Wstack-usage=`.
- Si un sujet ou un brief limite les fonctions permises, il prime ; zéro
  fuite prouvée par valgrind ou `-fsanitize=address`.

## Tester et mesurer

- Hôte avec ASan et UBSan : allocateur physique, buddy, slab, normalisation
  de carte (fixtures de vraies cartes E820 et UEFI, chevauchements et zones
  nulles compris). Propriétés : jamais deux fois la même frame, libres +
  utilisées = total, fusion correcte du buddy.
- Boot : allouer, libérer, réallouer ; compteurs revenus à leur valeur de
  départ ; pages rendues à zéro.
- Épuisement : allouer jusqu'à `E_NOMEM`, tout libérer, recommencer ; même
  total, noyau vivant.
- Tailles de RAM : `make test` avec `RAM_MIN`, puis une grande RAM
  (`-m 4G`, et plus en x86-64) pour la carte avec trou PCI.
- QEMU : `info mem` et `info tlb` (mappages), `info mtree -f` (plan
  physique).

## Références

- OSDev wiki : Detecting Memory (x86), Memory Map (x86), Page Frame
  Allocation, Paging, Higher Half Kernel, Writing A Memory Manager.
- Knuth, TAOCP vol. 1 (buddy) ; Bonwick, « The Slab Allocator » ; Gorman,
  « Understanding the Linux Virtual Memory Manager » (libre en ligne) ;
  Drepper, « What Every Programmer Should Know About Memory ».
- Intel SDM vol. 3 (paging, PAT, MTRR, MCA), ARM ARM (VMSAv8-64), RISC-V
  Privileged (Sv39, Sv48).
