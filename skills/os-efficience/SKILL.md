---
name: os-efficience
description: >-
  Frugalité et optimisation mesurées d'un OS hobby : budgets taille et RAM, CPU au repos, profil QEMU, chemins noyau, C ou asm selon la mesure. Use when optimizing or when a change may slow the OS.
---

# OS frugal : optimiser en mesurant

Notre OS s'inspire de KolibriOS pour sa légèreté : petite image, peu de
RAM, CPU au repos quand rien ne se passe, réactivité. « Optimisation
maximale » veut dire **chaque gain mesuré avant et après**, jamais une
réécriture « parce que l'asm c'est plus rapide ». Outils : skills
asm-x86-dev (tests asm contre C, uops.info, llvm-mca), c-bas-niveau,
osdev-c, osdev-asm.

## Ce que fait KolibriOS (lu dans ses sources)

- Inactivité : un thread idle qui fait `hlt` (ou `mwait` si dispo) avec
  les interruptions actives, jamais une boucle d'attente
  (`kernel/trunk/kernel.asm`, `idle_thread`).
- Applis pilotées par événements : elles dorment dans « attendre un
  événement » (fonction 10) et ne redessinent que sur l'événement 1.
- Dessin direct dans le framebuffer, sans pile graphique lourde.
- Noyau et applis compressés en LZMA (kerpack, kpack) : l'image tient sur
  une disquette de 1,44 Mo avec un bureau complet.
- Tout en asm FASM. Nous : C ou asm, choisi par la mesure.

## Les mesures : `os-mesure` (vérifié ici)

Script `scripts/os-mesure` (lien `~/.local/bin/os-mesure`), plugins QEMU
compilés dans `~/.local/src/qemu-plugins` (hotblocks patché pour accepter
`limit=`).

- `os-mesure taille kernel.elf --budget N` : sections chargées, total en
  RAM, taille du fichier ; code 1 si budget dépassé.
- `os-mesure profil kernel.elf [--iso os.iso]` : instructions exécutées
  **dans le noyau** (hors BIOS et GRUB) et fonctions les plus chaudes,
  sous TCG avec `-icount` (reproductible : même chiffre à chaque
  lancement). Arrêt une seconde après le marqueur série `kmain OK`. Via
  ISO, GRUB met environ 17 s sous `-icount`.
- `os-mesure repos kernel.elf|os.iso` : CPU hôte de la VM au repos (KVM).
  Doit rester proche de 0 % ; 100 % = une boucle active quelque part.
- `os-mesure ram kernel.elf|os.iso --budget MIO` : plus petite RAM
  (`-m`) avec laquelle le marqueur série apparaît, par dichotomie de 64
  Mio vers le bas (`--max` pour changer) ; code 1 si le budget est
  dépassé. Gabarit osdev-c : 2 Mio, 7 démarrages (2026-09-29).
- Limite du profil : sous émulation, chaque tour de `rep stos/movs`
  compte comme une instruction. Exemple mesuré : remplissage 1024x768,
  boucle naïve 11,3 M instructions contre 0,93 M avec `rep stosd` (x12),
  mais sur l'hôte le vrai gain est x4,1 (361 µs contre 88 µs). Le profil
  trouve les points chauds ; le gain réel se chiffre sur l'hôte (banc C
  avec `clock_gettime`, ou `perf stat -e cycles:u` : perf installé,
  espace utilisateur seulement sans root).

## Méthode pour chaque optimisation

1. Mesurer l'état actuel (`make mesure` du projet : taille, profil,
   repos, ligne ajoutée à `mesures.tsv`).
2. Garder la version simple comme **référence** : en C, testée.
3. Écrire la version optimisée (C mieux écrit, ou asm) et la tester
   contre la référence (résultat identique, cas limites, registres
   préservés : `checked_call` du skill asm-x86-dev).
4. Remesurer. Garder seulement si le gain est net ; noter le chiffre
   avant/après dans le commit ou la justification.
5. Ne jamais optimiser une fonction absente du haut du profil.

## C ou asm

- C par défaut : plus court à écrire et à relire, gcc `-O2` fait déjà
  très bien sur le code ordinaire.
- Asm quand la mesure le justifie : boucles de copie et de remplissage
  (`rep movsd`, `rep stosd`), blitting, routines appelées des milliers de
  fois, code où la taille compte (boot, stubs), ou instructions que le C
  n'exprime pas.
- Chaque routine asm garde sa version C de référence dans les tests.
- Regarder ce que produit gcc avant d'écrire à la main :
  `i686-elf-objdump -d -M intel -S`.

## Techniques qui paient dans un OS façon Kolibri

- CPU : `hlt` dans l'idle, jamais de polling ; tout par interruption
  (clavier, souris, timer). Timer à la fréquence utile, pas plus.
- Dessin : remplir par lignes (`rep stosd`), copier par lignes
  (`rep movsd`) ; ne jamais lire la mémoire vidéo (très lente) ; redessiner
  seulement les rectangles modifiés (dirty rectangles) ; une police
  bitmap en table plutôt que du calcul par pixel ; pas de flottants dans
  le noyau.
- Framebuffer en write-combining (PAT ou MTRR) : gros gain d'écriture sur
  vrai matériel, à mesurer sur la machine réelle (QEMU ne le montre pas) ;
  chiffre noté dans la fiche matériel (integration-systeme).
- Mémoire : allocations statiques quand la taille est connue, bitmap ou
  pile de frames pour la mémoire physique, tas simple ; pas de fuites
  (compteur d'allocations affiché en debug).
- Taille : `-Os` à comparer avec `-O2` (mesurer les deux), `-ffunction-
  sections -fdata-sections` + `--gc-sections`, pas de tables d'unwind
  (`-fno-asynchronous-unwind-tables`), `strip` de l'image livrée (garder
  l'ELF avec symboles pour gdb), compression LZMA à la kpack plus tard.
- Boot : pas d'attentes inutiles, initialiser seulement ce qui sert.
- Applis : boucle d'événements bloquante, redessin sur demande, format
  binaire plat sans relocations.

## Optimisations propres au noyau

Même méthode : mesurer, garder la référence, remesurer. Le durcissement de
noyau-securite a lui aussi son chiffre ; on ne l'enlève pas pour un gain
marginal.

- Appel système : `int 0x40` reste l'ABI simple ; `sysenter` (i686) et
  `syscall` (x86-64) coûtent bien moins cher. Mesurer un appel vide
  (`rdtsc` autour d'un million d'appels) avant d'ajouter un second chemin ;
  ne sauver que ce que l'ABI exige.
- TLB : pages globales (CR4.PGE et bit G) pour le noyau, présent dans tous
  les espaces ; PCID en x86-64, ASID sur ARM et RISC-V, pour garder les
  entrées d'une tâche à l'autre ; `invlpg` d'une page plutôt qu'un
  rechargement de CR3 ; grandes pages (4 Mio en PSE sur i686, 2 Mio en
  x86-64) pour la RAM mappée par le noyau et le framebuffer.
- Caches : structures chaudes alignées sur 64 octets, champs chauds
  ensemble, données par CPU séparées (pas de faux partage) ;
  `__builtin_expect` sur les chemins d'erreur, `__attribute__((cold))` sur
  la panique et les erreurs.
- Allocations : cache slab par type d'objet fréquent, préallocation au
  boot de ce qui a une taille connue, pas de `kmalloc` dans l'IRQ ni dans
  l'ordonnanceur.
- Ordonnanceur : choix en O(1) (bitmap de priorités, `__builtin_ctz`),
  bascule de contexte en asm court qui ne sauve que les registres
  préservés.
- Repos sans tick : quand tout dort, programmer le timer sur le prochain
  événement (APIC en one-shot, TSC-deadline) au lieu d'un 100 Hz fixe.
  `os-mesure repos` doit rester proche de 0 %.
- Copies et remplissages : `rep movsb` et `rep stosb` rapides si ERMSB
  (CPUID leaf 7 EBX bit 9), `rep movsd` sur les vieux CPU ; choix fait au
  boot par CPUID, chacun mesuré et testé contre la version C.
- Pages données aux applis : effacées (obligatoire, os-confidentialite),
  coût compté dans le profil.
- Interruptions : handler court, travail différé, MSI plutôt qu'une ligne
  partagée qui oblige à interroger chaque périphérique.
- FPU et SIMD : jamais dans le noyau ; sauvegarde des applis par XSAVEOPT
  si présent, à chaque bascule (noyau-securite).
- Mesurer dans le noyau : `lfence; rdtsc` autour d'un chemin ; compteurs
  d'appels système, d'IRQ, de fautes de page et de bascules affichés en
  debug ; compteurs PMU (`rdpmc`) plus tard.
- LTO, `-Os` ou `-O2` : tranchés par la taille et le profil, pas par
  principe.

## RAM

- Garde-fou : `make test` redémarre les cibles à port série avec
  `RAM_MIN` Mo (4 dans VelumOS, mesuré 2). Relever `RAM_MIN` seulement
  pour une fonctionnalité qui le justifie, avec le chiffre dans la
  justification. KolibriOS annonce 8 Mo minimum. La valeur se mesure avec
  `os-mesure ram`, jamais au jugé ; le budget poste par poste (image,
  tables, tas, framebuffer, piles, applis) est dans gestion-memoire.
- Chaque architecture garde son chemin rapide (`arch_fill_row` : `rep
  stos` sur x86, boucle C ailleurs) testé contre la même référence.

## Budgets

Fixer dans le Makefile un budget de taille (`BUDGET`) et le relever
consciemment quand une fonctionnalité le justifie, jamais en silence.
`mesures.tsv` garde l'historique (date, commit, taille, instructions de
boot, CPU au repos) pour voir une régression d'un coup d'œil.
