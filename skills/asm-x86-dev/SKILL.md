---
name: asm-x86-dev
description: >-
  Écrire, tester et optimiser du .asm x86-64 (NASM, FASM, GAS) : ABI System V, syscalls Linux, test contre une référence C. Use when writing a .asm/.s file or when asm corrupts the caller.
---

# Assembleur x86-64 : pratiques de dev

L'asm vit dans des fichiers `.asm` séparés, testés depuis le C. Pas d'asm
inline pour une vraie fonction (réservé aux instructions isolées : skill
c-bas-niveau). Registres et lecture de la sortie du compilateur :
assembly-x86 ; tableaux d'ABI : abi-and-calling-conventions ; intrinsics :
simd-intrinsics ; OS et boot : osdev-asm. Si un sujet impose la syntaxe ou des règles
(libasm…), il prime sur ce skill.

Gabarit vérifié : `templates/nasm-c-test/` (`make test`) avec une fonction
testée contre `strlen`, un vérificateur de registres préservés
(`checked_call`), une fonction fautive qu'il doit attraper, et un
programme `_start` sans libc.

## Structure d'un fichier

- `default rel` en tête (NASM) : adresses RIP-relatives, compatible PIE.
  `lea rsi, [msg]`, jamais `mov rsi, msg` dans un binaire PIE.
- Sections `.text`, `.rodata`, `.data`, `.bss`. Finir chaque fichier par
  `section .note.GNU-stack noalloc noexec nowrite progbits`, sinon ld
  suppose une pile exécutable.
- Symboles exportés avec type et taille :
  `global f:function (f.end - f)` et un label `.end:` après le `ret`
  (visible dans `readelf -s`, utile à gdb et perf). Données :
  `global v:data 4`.
- Labels locaux `.loop`, `.done` sous chaque fonction.
- Pas de commentaires, ou très minimalistes (règle permanente) : noms de
  labels et de constantes parlants (`equ`, `%define`), prototype et
  registres détruits décrits dans `docs/justifications/`. Instructions en
  minuscules, MAJUSCULES pour les macros.
- Assembler avec `-Werror` et `-g -F dwarf` pour avoir les lignes dans gdb.

## ABI System V et pièges

- Arguments : rdi, rsi, rdx, rcx, r8, r9 (flottants xmm0-7), retour rax.
  À préserver : rbx, rbp, r12-r15 (et rsp). Libres : rax, rcx, rdx, rsi,
  rdi, r8-r11, tous les xmm.
- Pile alignée sur 16 juste avant chaque `call` (à l'entrée, rsp vaut
  8 mod 16). Compter les `push` et ajuster avec `sub rsp, 8`.
- Écrire `eax` met à zéro le haut de `rax` ; écrire `al` ou `ax` ne le
  fait pas (reste des anciennes valeurs, fausses dépendances).
- Appel système Linux : numéro dans rax, arguments rdi, rsi, rdx, **r10**,
  r8, r9, retour rax (négatif = -errno). `syscall` détruit rcx et r11.
  Numéros : write 1, exit 60, exit_group 231 (table
  `arch/x86/entry/syscalls/syscall_64.tbl` du noyau).
- Appeler une fonction de la libc depuis l'asm en PIE : `call
  malloc wrt ..plt`, et `extern malloc`.
- SIMD : `movdqa`/`movaps`/`mova` exigent une adresse alignée (sinon
  crash), `movdqu`/`movu` non. `vzeroupper` avant de rendre la main après
  de l'AVX, `emms` après du MMX.

## Tester

- Toujours une référence en C (ou la libc) et une boucle qui compare sur
  des cas limites : vide, 1 élément, tailles non multiples du pas SIMD,
  grosses entrées, octets 0x00, 0x80, 0xFF, adresses non alignées.
- Compiler le test avec `-fsanitize=address,undefined` : une lecture hors
  buffer dans l'asm finit souvent en erreur ASan côté C.
- Vérifier les registres préservés : `checked_call` du gabarit, ou pour un
  vrai projet la bibliothèque checkasm (code.videolan.org/videolan/checkasm,
  BSD-2, issue de dav1d et FFmpeg) qui contrôle aussi pile, vzeroupper et
  état FPU, avec buffers aléatoires, graines multiples et benchmark.
- C'est `make test` qui lance tout (le hook de fin de tour le relance sur
  un projet marqué `.mode-side-project`).

## Performance

- Mesurer avant d'optimiser : `perf stat`, benchmark sur des tailles
  réalistes, comparer à `gcc -O2`/`-O3` de la version C (souvent aussi
  bon hors SIMD).
- Latence et débit par instruction et par CPU : uops.info ; analyse d'un
  bloc de boucle : uiCA (uica.uops.info) ou `llvm-mca -mcpu=<cpu>
  -timeline` (llvm-mca lit la syntaxe LLVM, pas NASM : lui passer la
  sortie de `clang -S -masm=intel`) ; manuels d'Agner Fog.
- Idées courantes : boucle à compteur qui descend (`dec` + `jnz`),
  offset négatif qui sert à la fois d'index et de compteur, `lea` pour
  calculer sans toucher aux flags, `xor eax, eax` pour zéro, éviter les
  écritures partielles de registres.
- Lire ce que fait le compilateur : Compiler Explorer (godbolt.org) ou
  `gcc -O2 -S -masm=intel -fverbose-asm`.

## Déboguer

- `gdb ./prog` puis `layout asm`, `layout regs`, `si`/`ni`,
  `info registers rax rdi`, `x/16xb $rdi`, `p $rsp % 16`.
- `objdump -d -M intel -S prog`, `ndisasm -b 64` sur un binaire plat,
  `readelf -s` pour vérifier types et tailles des symboles.
- Crash au `call` d'une fonction C ou en SSE : alignement de pile.
  Le C appelant plante au retour : registre préservé écrasé.

## FASM et GAS

- FASM : `format ELF64` puis `public f` / `extrn g`, `section '.text'
  executable`, et `section '.note.GNU-stack'` à la fin (vérifié : pile
  non exécutable). Même logique, macros plus puissantes ; imposé par
  KolibriOS (skill osdev-asm).
- GAS : fichiers `.S` passés par gcc (préprocesseur C disponible),
  `.intel_syntax noprefix` si on préfère Intel, `.type f, @function` et
  `.size f, .-f` pour type et taille.

## Apprendre

- Ed Jorgensen, x86-64 Assembly Language Programming with Ubuntu, gratuit
  (egr.unlv.edu/~ed/x86.html), bases Linux en yasm/NASM.
- FFmpeg asm-lessons (github.com/FFmpeg/asm-lessons, existe en français) :
  SIMD en NASM avec x86inc.asm, style de FFmpeg et dav1d.
- Kusswurm, Modern X86 Assembly Language Programming 3e (NASM sous
  Linux, AVX à AVX-512) ; Bartlett, Learn to Program with Assembly (GAS
  AT&T, Linux) ; CS:APP chap. 3 pour lire l'asm de gcc.
- Références : Intel SDM, felixcloutier.com/x86, manuel NASM
  (nasm.us/docs, chap. 13 pour x86-64), doc noyau Linux
  « asm-annotations » pour annoter les fonctions asm proprement.
