---
name: osdev-c
description: >-
  OS hobby en C (x86 32/64, RISC-V) : toolchain croisée, GRUB ou Limine, série, GDT, IDT, paging, tests QEMU. Use when extending a kernel or driver, or on a triple fault, reboot loop or no output.
---

# OS from scratch en C

Le C est le langage principal du noyau ; l'asm reste dans quelques fichiers
courts (skill osdev-asm). Pour les détails C (volatile, asm inline, UB) :
skill c-bas-niveau. Pour les outils : gdb, elf-inspection, binutils,
linker-scripts. Conception du noyau (verrous, mémoire, erreurs,
assertions) : noyau-conception ; mémoire physique et virtuelle, budget
RAM : gestion-memoire ; durcissement : noyau-securite ;
optimisation : os-efficience. Pilotes et matériel réel : pilotes-materiel. Contrats
entre couches, build reproductible, preuves par paliers et vraie machine :
integration-systeme.

## Mise en place d'un projet

1. Fichier vide `.mode-side-project` à la racine (active `make test` en
   fin de tour), ajouté à `.git/info/exclude`.
2. Départ recommandé : copier `templates/i686-multiboot/` de ce skill
   (boot.S, kernel.c, serial.c, panic.c, verif.c, linker.ld,
   Makefile). Deux profils : `PROFIL=debug` (défaut, UBSan en mode
   piège) et `PROFIL=release` ; durcissement commun (canari de pile,
   variables locales à zéro, registres effacés au retour) détaillé dans
   noyau-securite. Sorties dans `build/<profil>-v<VERIF>/kernel.elf`, avec
   build-id. Vérifié sur Fedora (2026-09-29), i686-elf-gcc 15.3 (défaut)
   et clang 23 (`TOOLCHAIN=llvm`) : `make test` démarre les deux profils
   sans écran (« kmain OK » sur COM1), prouve que le canari déclenche la
   panique (`VERIF=1`) et que le piège UBSan lève un `#UD` (`VERIF=2`,
   v=06 dans le journal QEMU) ; `grub2-file --is-x86-multiboot` passe
   (`grub-file` sur Debian) ; deux builds successifs donnent le même
   sha256. Le hook de fin de tour lance ce `make test` tout seul sur un
   projet marqué `.mode-side-project`. `make debug-batch GDB_CMDS="-ex
   'bt'"` : gdb sans interaction, à utiliser par l'agent (`make debug`
   reste pour l'auteur dans un terminal).
3. Fixer un but final et une roadmap (plus bas) avant d'écrire du code :
   c'est la première erreur de débutant citée par OSDev.

## Toolchain

- La compilation qui décide : le code C se compile avec gcc -Wall -Wextra -Werror. Un gcc croisé (`i686-elf-gcc`, `x86_64-elf-gcc`, et les autres noms qui finissent par `gcc`) reste gcc. `TOOLCHAIN=llvm` est un second profil documenté. Il ne remplace pas cette compilation.
- Ne jamais compiler le noyau avec le gcc de l'hôte tel quel : il vise
  Linux, amène ses en-têtes et sa libgcc. Sur cette machine :
  - Par défaut (`TOOLCHAIN=gcc` du gabarit) : `i686-elf-gcc` 15.3.0 +
    binutils 2.47, construits dans `~/.local/opt/cross`, liés dans
    `~/.local/bin`. Lier avec `i686-elf-gcc -T linker.ld -nostdlib ...
    -lgcc`. Vérifié : une division 64 bits en 32 bits appelle
    `__udivdi3` de libgcc et le noyau démarre.
  - Secours (`TOOLCHAIN=clang`) : `clang --target=i686-elf` + `ld -m
    elf_i386`. Pas de libgcc : la même division 64 bits échoue au lien.
  - 64 bits : `x86_64-elf-gcc` 15.3.0 au même endroit (2026-09-29), avec
    une seconde libgcc sans red zone (`-print-multi-lib` affiche
    `no-red-zone;@mno-red-zone`), choisie toute seule avec `-mno-red-zone`.
    Vérifié : noyau en `-mcmodel=kernel` à 0xffffffff80000000 qui tire
    `__udivti3` de `no-red-zone/libgcc.a`.
  - ARM64 et RISC-V : `aarch64-linux-gnu-gcc` et `riscv64-linux-gnu-gcc`
    16.2.1 (paquets Fedora, libgcc comprise), en `-ffreestanding
    -nostdlib` ; ARM 32 bits : `arm-none-eabi-gcc`.
  - Reconstruire : `~/.local/src/cross/build.sh` (`TARGET=x86_64-elf`
    gère la libgcc sans red zone ; archives gardées et vérifiées, hors
    ligne). La toolchain installée contient le chemin du home : ne jamais
    la publier telle quelle. Version publique : dépôt
    `<compte GitHub>/i686-elf-gcc`, clone dans `~/Bureau/i686-elf-gcc`,
    archives des deux cibles construites par GitHub Actions à chaque tag
    `v*` (v1.1.0, glibc 2.38 ou plus récente).
- Avec un vrai cross-compilateur, éviter `-m32`, `-nostdinc`,
  `-fno-builtin` : inutiles ou nuisibles.
- Garde utile dans un en-tête : `#if defined(__linux__)` puis `#error`,
  pour refuser le compilateur de l'hôte.

## Flags

- Communs : `-ffreestanding -nostdlib -fno-pic -static -std=gnu11 -O2 -g
  -fno-omit-frame-pointer -Wall -Wextra -Werror`, plus les drapeaux de
  durcissement vérifiés de noyau-securite (le canari demande
  `__stack_chk_guard` et `__stack_chk_fail`, fournis par le gabarit).
  `-ffreestanding` n'empêche pas le compilateur d'appeler `memcpy`,
  `memset`, `memmove`, `memcmp` : les écrire.
- 32 bits : `-mno-sse -mno-mmx -mno-80387` tant que la FPU n'est pas
  initialisée.
- 64 bits : en plus `-mno-red-zone` (une interruption écraserait les 128
  octets sous RSP), `-mno-sse -mno-sse2 -mno-mmx -mno-80387` ou
  `-mgeneral-regs-only`, `-mcmodel=kernel` pour un noyau à
  0xffffffff80000000.
- Lien : `-T linker.ld -nostdlib -static -z max-page-size=0x1000
  -z noexecstack --build-id=sha1` (garder `.note.gnu.build-id` dans sa
  propre section du linker script, sinon readelf la voit alignée sur 4 Kio),
  `--gc-sections` avec `-ffunction-sections -fdata-sections` si on veut.

## Boot

- 32 bits : Multiboot 1. En-tête dans les 8 premiers Kio, aligné sur 4.
  Test rapide `qemu-system-i386 -kernel kernel.elf`, ISO avec
  `grub2-mkrescue -o os.iso isodir` sur Fedora (xorriso et
  grub2-pc-modules) ; `grub-mkrescue` et grub-pc-bin sur Debian.
  `-kernel` de QEMU ne charge pas un ELF 64 bits.
- 64 bits : Limine (BIOS et UEFI, noyau higher half, requêtes `volatile`
  dans la section `.limine_requests`). Partir du template officiel
  github.com/Limine-Bootloader/limine-c-template (0BSD), qui gère aussi
  aarch64 et riscv64. Vérifié sur l'ancien poste Debian (clone
  `~/Bureau/osdev/limine-c-template`, absent sur Fedora) :
  `make TOOLCHAIN=llvm all` (clang + ld.lld, télécharge Limine et ses
  dépendances) produit une ISO qui démarre en BIOS
  (`qemu-system-x86_64 -M q35 -cdrom ... -boot d`) et en UEFI. UEFI sur
  Fedora : `-drive if=pflash,format=raw,readonly=on,
  file=/usr/share/edk2/ovmf/OVMF_CODE.fd -drive
  if=pflash,format=raw,file=vars.fd` (copie locale de `OVMF_VARS.fd`).
  Le noyau dessine un dégradé dans le framebuffer : preuve par
  `screendump` du moniteur QEMU.
- Preuve visuelle sans écran (framebuffer, GUI) : `(sleep 10; echo
  "screendump s.ppm"; sleep 1; echo quit) | qemu-system-... -display none
  -monitor stdio`, convertir en PNG (Pillow) et relire l'image.
- Pile : 16 Kio alignés sur 16 dans `.bss`, ESP posé avant le `call kmain`.

## Variante VelumOS (projet de l'auteur, inspiré de KolibriOS)

Notre OS libre, pas KolibriOS : ses sources (`~/Bureau/osdev/kolibrios`)
servent à voir comment une idée est faite, jamais à copier (GPL-2.0).
Détail et état : `memory/projets/velumos.md` et `docs/` du projet.

- Cibles : x86 32 bits (GRUB Multiboot, BIOS et UEFI), x86-64, ARM64,
  RISC-V 64 (Limine 12.9.1 épinglé), ARM 32 bits ARMv7 (QEMU `virt`,
  noyau ELF direct). Vérifié : `make test-all` dans `~/Bureau/VelumOS`
  (dossier absent depuis le passage à Fedora : à recloner avant de
  s'y fier).
- Structure : cœur portable en C dans `kernel/` (n'utilise que
  `kernel/arch.h` : `arch_early_init`, `arch_putc`, `arch_fill_row`,
  `arch_idle`) ; tout le spécifique, asm compris, dans `arch/<arch>/`.
  Une fonctionnalité portable ne met jamais de `#ifdef` d'architecture
  dans `kernel/`.
- Démarrage 64 bits sous Limine : l'UART MMIO n'est pas mappé (pas
  d'identité ni de HHDM pour les périphériques) ; test par capture
  d'écran (`tests/check_shot.py`) tant que le noyau n'a pas son paging.
- RAM : `make test` redémarre chaque cible à port série avec
  `RAM_MIN` (4 Mo ; mesuré 2 Mo). En UEFI c'est le firmware qui réclame
  environ 80 Mo, pas le noyau.
- API système à la Kolibri (`int 0x40` sur x86, équivalent `svc`/`ecall`
  ailleurs), applis VELUMAPP v1 (format maison), interface graphique
  dans le noyau, disque RAM FAT12 : ordre des étapes ci-dessous.

Ordre conseillé pour VelumOS : 1. série + framebuffer (fait : pixel,
rectangle) ; 2. police bitmap et `kprintf` à l'écran ; 3. affichage ARM
32 bits (ramfb ou mailbox Raspberry Pi) ; 4. interruptions et timer par
architecture ; 5. clavier et souris (PS/2, puis USB HID pour les PC
récents) ; 6. mémoire physique, paging, tas ; 7. fenêtres dans le noyau ;
8. tâches et ordonnanceur ; 9. mode user et appels système ; 10. disque
RAM et chargeur VELUMAPP ; 11. premières applis et SDK.

## Roadmap conseillée

Une étape à la fois, chacune prouvée dans QEMU avant la suivante.

1. Boot + sortie série COM1 (0x3F8 : DLAB, diviseur 3, 8N1, FIFO, test
   loopback) puis texte VGA 0xB8000 ou framebuffer. Un `kprintf` minimal.
2. GDT : entrée 0 nulle, code et données noyau, plus tard code et données
   user et TSS. Recharger CS par far jump.
3. IDT de 256 entrées + stubs asm pour les 32 exceptions. Les exceptions
   8, 10 à 14, 17, 21, 29 et 30 poussent un code d'erreur, les autres non : stub
   commun qui pousse un faux code pour garder la même pile. Passer un
   pointeur vers la structure des registres au handler C, jamais la
   structure par valeur.
4. PIC 8259 remappé hors de 0x00-0x1F (0x20 et 0x28), EOI 0x20 à la fin
   de chaque IRQ. PIT à 100 Hz derrière une petite API timer. Plus tard
   APIC.
5. Clavier PS/2 par IRQ 1.
6. Carte mémoire (Multiboot ou Limine), allocateur physique (bitmap ou
   pile de frames).
7. Paging : tables alignées sur 4 Kio, identité puis higher half,
   permissions par section (text RX, rodata R, data RW, NX en 64 bits).
8. Tas noyau : liste chaînée simple d'abord, kmalloc aligné.
9. Tâches et bascule de contexte (asm court), ordonnanceur round robin.
10. Mode user, TSS, appels système.
11. Pilote disque, système de fichiers simple, chargeur ELF.

## Déboguer

- Triple fault ou reboot en boucle : `-d int,cpu_reset,guest_errors
  -no-reboot -no-shutdown -D qemu.log`, lire la dernière exception
  (v=0d GPF, v=0e page fault avec CR2, v=08 double fault).
- `-monitor stdio` : `info registers`, `info mem`, `info tlb`.
- gdb : `qemu ... -s -S` puis `gdb -ex 'file kernel.elf' -ex
  'target remote :1234' -ex 'break kmain' -ex c` (`make debug` du
  gabarit). Un agent ne peut pas piloter gdb en interactif : toujours
  `gdb -batch` avec des `-ex` (`make debug-batch`), QEMU tué à la fin. Adresse d'un crash vers la source : `addr2line -e kernel.elf
  -f 0x...`.
- Sortie de secours : `outb(0xE9, c)` avec `-debugcon stdio` (QEMU et
  Bochs).
- Bochs pour les changements de mode et les descripteurs.
- Avant de chercher plus loin, localiser la faute avec gdb ou des prints,
  sans deviner la cause.
- Marche dans QEMU, pas sur la vraie machine : suspecter d'abord une
  adresse ou une IRQ supposée au lieu d'être découverte, une attente sans
  timeout, un cache ou une barrière (pilotes-materiel) ; voir ce qui se
  passe sans port série : integration-systeme.

## Tests

- Code sans matériel (allocateurs, bitmap, printf, parsing ELF, FS) :
  compilé aussi sur l'hôte avec tests unitaires et
  `-fsanitize=address,undefined`.
- Noyau : QEMU sans écran avec timeout, résultat lu sur la série
  (`make test`). Pour un code de sortie propre : `-device
  isa-debug-exit,iobase=0xf4,iosize=0x04`, une écriture de `v` sur le port
  0xf4 fait quitter QEMU avec `(v << 1) | 1`.
- Auto-tests au démarrage : allouer, libérer, réallouer ; vérifier que le
  compteur de ticks avance. Afficher le nom du test avant de le lancer.
- Tester en `-O0` et `-O2`.
- Au-delà de QEMU : variantes de machine (`q35`, `hpet=off`, `-cpu 486`,
  `-smp 4`), Bochs, puis vraie machine avec la clé écrite par
  `ecrire-image` et le résultat dans la fiche matériel
  (integration-systeme).

## Ressources

- OSDev wiki : Required Knowledge, Beginner Mistakes, Bare Bones, Meaty
  Skeleton, Limine Bare Bones, GCC Cross-Compiler, Going Further on x86.
  Le site bloque parfois les robots (Cloudflare) : passer par
  web.archive.org si besoin.
- xv6-riscv et son livre (MIT 6.1810) ; la version x86 n'est plus
  maintenue. OSTEP (pages.cs.wisc.edu/~remzi/OSTEP) pour la théorie.
- Operating System in 1,000 Lines (RISC-V, C, QEMU) :
  operating-system-in-1000-lines.vercel.app
- Intel SDM vol. 3 (programmation système), AMD APM vol. 2, psABI
  System V (gitlab.com/x86-psABIs).
- À éviter comme base : tutoriels JamesM (bugs connus listés par OSDev),
  Bran, BrokenThorn, Nick Blundell et cfenollosa/os-tutorial (gcc hôte,
  binaires plats, abandonnés). Ils servent à lire, pas à copier.
