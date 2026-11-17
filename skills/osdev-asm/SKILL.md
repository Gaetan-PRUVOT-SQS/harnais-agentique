---
name: osdev-asm
description: >-
  OS x86 en assembleur : secteur de boot, modes réel, protégé et long, FASM/NASM/GAS, applis KolibriOS. Use when writing a boot sector, a mode switch, an ISR stub or a KolibriOS app.
---

# OS en assembleur

Priorité au C (skill osdev-c). L'asm sert là où le C ne peut rien faire :
premier code de boot, changement de mode, stubs d'interruption, bascule de
contexte, instructions privilégiées. Exception : un projet qui est en asm
par choix (KolibriOS, MenuetOS, BareMetal OS), où l'on suit le code existant.
Registres, ABI et asm inline GCC : skill assembly-x86.

## Choisir l'assembleur

- NASM : projet perso lié à du C (`nasm -f elf32` ou `-f elf64`), binaire
  plat avec `-f bin`. Syntaxe Intel, c'est celle des tutos OSDev.
- FASM : imposé par KolibriOS et Menuet (binaire plat direct, macros
  `macros.inc`, `proc32.inc`). fasm2 et fasmg existent, mais KolibriOS
  embarque fasm 1.73 dans `programs/develop/fasm/1.73`.
- GAS (`.S` passé par gcc, `.intel_syntax noprefix` si besoin) : quand on
  veut rester dans la chaîne GCC/clang et utiliser le préprocesseur C.
- Un seul assembleur par projet, sauf code existant.

## Règles d'écriture

- Mode explicite en tête de chaque fichier ou bloc : `bits 16/32/64`
  (NASM), `use16/use32/use64` (FASM), `.code16/.code32/.code64` (GAS).
  Un octet mal décodé dans le mauvais mode donne un crash sans rapport.
- Pas de commentaires, ou très minimalistes (règle permanente) : labels
  et constantes nommés ; entrées, sorties et registres détruits décrits
  dans `docs/justifications/`.
- Appelée depuis le C ou appelant du C : respecter l'ABI.
  cdecl 32 bits : arguments sur la pile de droite à gauche, l'appelant
  nettoie, retour dans EAX, EAX/ECX/EDX détruits, EBX/ESI/EDI/EBP/ESP
  préservés. System V x86-64 : RDI, RSI, RDX, RCX, R8, R9, retour RAX,
  RBX/RBP/R12-R15 préservés, RSP aligné sur 16 avant le `call`.
- Symboles : `global` pour ce que le C appelle, `extern` pour ce que l'asm
  appelle. Sections `.text`, `.data`, `.rodata`, `.bss` ; ne pas mettre de
  données dans `.text` sauf binaire plat voulu.
- Pile : poser ESP/RSP sur une pile à soi avant tout `call` au boot.
- Constantes nommées (`equ`) plutôt que nombres magiques pour ports,
  sélecteurs et bits de CR0/CR4/EFER.

## Boot et changements de mode

- BIOS : 512 octets chargés à 0x7C00, mode réel 16 bits, lecteur dans DL,
  signature 0x55 0xAA aux octets 510 et 511 (`times 510-($-$$) db 0` puis
  `dw 0xAA55` en NASM). Ne pas supposer CS:IP = 0000:7C00 : faire un far
  jump pour normaliser, poser DS/ES/SS.
- Mode protégé : `cli`, GDT chargée (`lgdt`), A20 active, CR0.PE = 1, far
  jump vers le sélecteur code pour recharger CS, puis recharger les
  segments de données et la pile.
- Mode long : en plus, PAE (CR4.PAE), tables de pages avec au moins
  l'identité sur le code en cours, CR3, EFER.LME via `wrmsr` sur 0xC0000080,
  CR0.PG, far jump vers un segment code 64 bits.
- Un bootloader maison est un bon exercice ; pour avancer sur le noyau,
  prendre Limine ou GRUB (multiboot) et garder l'asm pour le reste.

## KolibriOS

Référence pour notre OS inspiré de Kolibri (skill osdev-c, section
variante) : on y regarde comment c'est fait, on ne développe pas
KolibriOS et on n'en copie pas de code (GPL-2.0).


- Dépôt canonique : git.kolibrios.org/KolibriOS/kolibrios (miroir GitHub
  officiel KolibriOS/kolibrios), GPL-2.0, actif en 2026. Noyau dans
  `kernel/trunk` (`kernel.asm`, `boot/`, `core/`, `fs/`, `gui/`,
  `network/`, `video/`), référence des appels système dans
  `kernel/trunk/docs/sysfuncs.txt`.
- Appli : `format binary as ""`, `use32`, `org 0x0`, puis l'en-tête
  `db 'MENUET01'`, `dd 0x01, START, I_END, 0x100000, 0x100000, 0, 0`
  (version, entrée, taille, mémoire, pile, paramètres, chemin).
- Appel système : `int 0x40`, EAX = numéro de fonction, paramètres dans
  EBX, ECX, EDX, ESI, EDI. Macro `mcall` ; quitter avec `mcall -1`.
  Boucle d'événements : 1 redessiner, 2 touche, 3 bouton.
- Compiler une appli seule : `fasm prog.asm prog` (ou `nasm -f bin`).
  Tout le système : Tup (`tup init` puis `tup`), avec `tup.config` tiré de
  `tup.config.template` pour couper les compilateurs absents. Noyau :
  `fasm -m 262144 kernel.asm kernel.mnt` depuis `kernel/trunk` (voir
  `Tupfile.lua` ; `build.sh` crée d'abord `lang.inc` avec
  `lang fix en_US`).
- Glisser un fichier dans l'image disquette : `mcopy -moi kolibri.img
  fichier ::fichier`.
- Lancer : `qemu-system-i386 -m 256 -boot d -cdrom kolibri.iso` ou
  `-fda kolibri.img -boot a`. Les options du wiki (`-soundhw`,
  `-localtime`, `-usbdevice`) sont anciennes : utiliser `-device
  usb-tablet`, `-rtc base=localtime`.

### Vérifié sur l'ancien poste Debian (2026-09-27)

Refait sur le poste Ubuntu le 2026-10-06 : `~/Bureau/osdev`, les sources,
l'image, `kerpack` et le SDK existent, et les deux gabarits KolibriOS
passent `make test`.

- Sources de référence : `~/Bureau/osdev/kolibrios` (clone sans
  historique ; `kernel/trunk/lang.inc` exclu en local). Image nightly :
  `~/Bureau/osdev/kolibri.img`, récupérée sur
  builds.kolibrios.org/en_US/data/data/kolibri.img (l'URL de
  `runtests.py` renvoie 404).
- Noyau : dans `kernel/trunk`, `echo 'lang fix en_US' > lang.inc` puis
  `fasm -m 262144 kernel.asm kernel.mnt` (2 s). Non compressé il ne
  tient pas sur la disquette : `kerpack kernel.mnt kernel.mnt` d'abord
  (`kerpack` et `kpack` compilés depuis
  `programs/other/kpack/kerpack_linux`, installés dans `~/.local/bin`),
  puis `mcopy -o -i img kernel.mnt ::KERNEL.MNT`.
- Appli asm : gabarit `templates/kolibri-app/` (hello.asm + Makefile).
  `INCLUDE=<src>/programs fasm ...` pour trouver `macros.inc` ;
  `make test.img` copie l'image, ajoute l'appli et une ligne dans
  `SETTINGS/AUTORUN.DAT` ; `make run` ouvre QEMU ; `make shot` démarre
  sans écran et produit `shot.png` via `screendump` du moniteur QEMU :
  c'est la preuve visuelle qu'un agent peut relire.
- `-accel kvm` fonctionne ici (accès à /dev/kvm). Pour chasser un bug
  de bas niveau, repasser sans KVM (TCG) : `-d int` n'est fiable qu'en
  TCG.
- En C pour KolibriOS (voie conseillée, C d'abord) : SDK officiel
  git.kolibrios.org/KolibriOS/ports, vérifié ici (2026-09-27) :
  - installé dans `~/Bureau/osdev/kolibrios-ports/sdk` :
    `i586-kolibrios-gcc` 13.2.0 + binutils + newlib (build :
    `source activate-env && cmake -B build && cmake --build build`,
    paquets texinfo, bison, flex et, sur Fedora, gmp-devel mpfr-devel
    libmpc-devel isl-devel) ;
  - le SDK doit être dans le `PATH` (le driver gcc appelle
    `i586-kolibrios-objcopy` par son nom) ; sortie au format `MENUET02` ;
  - `stdout`/`stderr` vont sur la debug board (fonction 63), pas dans une
    fenêtre ; newlib y est sans formats C99 : `%zu` et `%lld` s'affichent
    tels quels, caster vers `unsigned long` ;
  - test automatique : noyau compilé avec `-ddebug_com_base=0x3f8`, qui
    recopie la debug board (journal noyau + stdout des applis) sur COM1,
    puis `qemu ... -serial file:serial.log` et `grep`. Gabarit vérifié
    `templates/kolibri-c-app/` (`make test`, 3/3) ; la disquette étant
    pleine, il retire un jeu de la copie de l'image ;
  - ktcc (`programs/develop/ktcc`) existe aussi, non testé ici.
- Contribuer : fork, branche, PR vers `main`, rebase sans merge commit,
  lignes de commit de 72 caractères. Leur CONTRIBUTING encourage un tag
  `Assisted-by:` quand une IA aide, ce qui heurte la règle de l'auteur sur
  les mentions d'IA : signaler le point à l'auteur avant toute PR, ne pas
  trancher seul.
- MenuetOS 64 bits n'est pas libre (redistribution et désassemblage
  interdits) : ne pas en reprendre de code. BareMetal OS (NASM, x86-64,
  MIT) est un bon exemple lisible d'OS 64 bits en asm.

## Déboguer

- QEMU `-s -S` puis `gdb` : `target remote :1234`. En mode réel :
  `set architecture i8086` et `x/10i $cs*16+$eip`. Ensuite `layout asm`,
  `layout regs`, `si`, `info registers`, `x/8xw $esp`.
- `-d int,cpu_reset -no-reboot` pour voir l'exception qui mène au triple
  fault au lieu d'un reboot en boucle.
- Bochs : débogueur intégré (`r`, `sreg`, `creg`, `u`, `x`), utile pour
  les changements de mode ; `magic_break: enabled=1` et `xchg bx, bx`
  dans le code pour un point d'arrêt. Gabarit vérifié sous Debian :
  `templates/bochs-bootsector/` (`make test`). Sur Fedora, le binaire
  `bochs` est compilé sans débogueur (`-rc` refusé) : installer
  `bochs-debugger`, que le Makefile prend en priorité. Depuis Bochs 3, le
  débogueur ne démarre qu'avec `-debugger` (sinon « Ignoring magic break
  points ») : le Makefile l'ajoute quand le binaire le connaît. Pièges vus ici :
  `BIOS-bochs-latest` du paquet Ubuntu plante dans son rombios32, prendre
  `BIOS-bochs-legacy` ; pas d'affichage `nogui`, et SDL2 hors écran
  panique : utiliser `display_library: rfb, options="timeout=0"` ;
  piloter le débogueur avec `bochs -q -f bochsrc -rc cmds` (un fichier de
  commandes, pas stdin) ; `port_e9_hack: enabled=1` pour la sortie texte.
  Un seul Bochs à la fois (port VNC 5900).
- Vérifier un binaire plat : `ndisasm -b 16 boot.bin | head`, taille
  exacte (`stat -c %s boot.bin` doit donner 512 pour un secteur de boot).

## Références

- Intel SDM (fait foi) : intel.com/sdm ; AMD APM vol. 2 (système).
- felixcloutier.com/x86 : pratique, non officiel, basé sur le SDM de 2023.
- Agner Fog, calling conventions et optimisation : agner.org/optimize
- NASM : nasm.us/docs ; FASM : flatassembler.net/docs.php
- KolibriOS : wiki.kolibrios.org, `build.txt` et `CONTRIBUTING.md` du dépôt.
- PC Assembly Language (Paul Carter) : bases NASM 32 bits, daté (pas de 64
  bits).
