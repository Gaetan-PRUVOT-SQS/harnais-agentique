---
name: c-bas-niveau
description: >-
  C systèmes et bas niveau : freestanding, volatile et MMIO, alignement, UB, asm inline. Use when writing C for a kernel, driver, allocator or raw memory, or when C works only at -O0.
---

# C bas niveau

Le C d'un noyau ou d'un pilote n'a pas de filet : pas de libc, pas de
segfault propre, un UB peut faire un triple fault trois fichiers plus loin.
Écrire simple, vérifier chaque hypothèse, lire l'assembleur produit en cas
de doute. Outils déjà dans la pile : gcc, gdb, sanitizers, static-analysis,
assembly-x86, elf-inspection, linker-scripts. Pilote face à un vrai
périphérique (largeur d'accès, W1C, barrières par arch, DMA, timeouts) :
skill pilotes-materiel.

## Règles de base

- Types : `<stdint.h>` et `<stddef.h>` (fournis même en freestanding, avec
  `<stdbool.h>`, `<stdarg.h>`, `<limits.h>`, `<float.h>`, `<stdalign.h>`,
  `<stdnoreturn.h>`). Jamais `int` pour une adresse : `uintptr_t`.
  Taille d'objet : `size_t`. Registres : `uint8_t` à `uint64_t`.
- Standard fixé dans le Makefile : `-std=c11` ou `-std=c17` (gnu11 si on
  utilise `__attribute__` et l'asm GNU, c'est le cas d'un noyau).
- Warnings : `-Wall -Wextra -Werror -Wshadow -Wpointer-arith -Wcast-align
  -Wstrict-prototypes -Wmissing-prototypes -Wconversion` (`-Wconversion`
  peut être bruyant, l'activer au moins en CI).
- `_Static_assert(sizeof(struct gdt_entry) == 8, "gdt_entry");` pour toute
  structure lue par le matériel (GDT, IDT, TSS, tables de pages, en-têtes
  de boot).
- Structures matérielles : `__attribute__((packed))` seulement quand le
  format l'exige, et vérifier la taille avec un static assert. Ne jamais
  prendre l'adresse d'un champ packed mal aligné.
- Champs de bits C : l'ordre dépend du compilateur. Pour un registre ou une
  entrée de table, préférer des masques et décalages explicites
  (`#define PTE_PRESENT (1ull << 0)`).

## Formes courantes

Formes vérifiées avec `gcc -m32 -ffreestanding`, voir `exemples/gdt.h` et
`exemples/mmio.c` :

- asm étendu : `__asm__ volatile ("outb %0, %1" : : "a" (val), "Nd" (port) : "memory");`
- structure matérielle : `typedef struct __attribute__((packed)) s_gdt_entry { ... }	t_gdt_entry;`
  puis `_Static_assert(sizeof(t_gdt_entry) == 8, "t_gdt_entry");`
- `__attribute__((noreturn)) void	halt(void)`, `*(volatile uint32_t *)addr = val;`
- lire EFLAGS par un builtin (`__builtin_ia32_readeflags_u32()`) plutôt
  que par de l'asm étendu
- un fichier par pilote ou par table (gdt, idt, pic, serial), helpers
  `static` regroupés

## Mémoire et matériel

- MMIO : pointeur `volatile` (`volatile uint32_t *reg`). `volatile` empêche
  l'optimisation des accès, il ne fait ni atomicité ni ordre entre CPU.
- Ports x86 et instructions spéciales : fonctions `static inline` avec asm
  étendu (`inb`, `outb`, `lidt`, `invlpg`, `cli`, `sti`, `hlt`).
- Asm étendu : déclarer toutes les sorties, entrées et clobbers. Ajouter
  `"memory"` dès que l'instruction lit ou écrit la mémoire ou sert de
  barrière (`cli`, `lgdt`, écriture de CR3). `__asm__ volatile` si
  l'instruction a un effet de bord.
- Barrière compilateur : `__asm__ volatile("" ::: "memory")`. Partage entre
  CPU ou entre interruption et code normal : `_Atomic` / `__atomic_*` ou
  désactiver les interruptions autour de la section critique.
- Variable modifiée dans un handler d'interruption et lue ailleurs :
  `volatile` au minimum, atomique si plus d'un mot.
- Pas de VLA ni de gros tableaux locaux : la pile noyau est petite (souvent
  4 à 16 Kio), un débordement écrase silencieusement autre chose.
- Aligner ce que le matériel exige : tables de pages sur 4096
  (`__attribute__((aligned(4096)))`), pile sur 16.
- Attente d'un bit matériel : toujours bornée par un timeout en temps
  réel, jamais une boucle nue (pilotes-materiel).

## UB à traquer

- Dépassement d'entier signé, décalage >= largeur du type ou d'un négatif,
  `1 << 31` sur `int` (écrire `1u << 31`), aliasing de types (passer par
  `memcpy` ou une union), pointeur hors objet, lecture non initialisée,
  pointeur nul déréférencé (en noyau l'adresse 0 peut être mappée : le bug
  ne crashe pas).
- Le compilateur génère des appels à `memcpy`, `memset`, `memmove`,
  `memcmp` même en `-ffreestanding` : les fournir soi-même.
- Code qui marche en `-O0` et casse en `-O2` : presque toujours un
  `volatile` manquant, un clobber oublié ou un UB. Tester les deux niveaux.

## Vérifier

- Tout ce qui ne touche pas le matériel (allocateur, bitmap, parsing ELF,
  structures de données, printf maison) se teste aussi sur l'hôte, compilé
  avec `-fsanitize=address,undefined` (skill sanitizers), avant d'entrer
  dans le noyau.
- Analyse statique : `cppcheck` ou `clang-tidy` (skill static-analysis).
- Lire le code généré en cas de doute :
  `objdump -d -M intel -S fichier.o`.

## Références

- SEI CERT C Coding Standard : wiki.sei.cmu.edu/confluence/display/c
- GCC, extended asm : gcc.gnu.org/onlinedocs/gcc/Extended-Asm.html
- ABI System V i386 et x86-64 : gitlab.com/x86-psABIs
- OSDev wiki, Inline Assembly/Examples : wiki.osdev.org/Inline_Assembly/Examples
