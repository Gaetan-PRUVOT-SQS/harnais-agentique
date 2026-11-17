---
name: systeme-maison
description: >-
  Construire son propre système sans licences tierces : dépendances, REUSE, licences-tierces, clean room, composants maison. Use when adding a dependency, porting code or planning your OS userland.
---

# Son propre système, sans licence tierce

But : chaque ligne livrée est écrite pour le projet, ou bien déclarée et
choisie en connaissance de cause. VelumOS est sous GPL-2.0-or-later (choix
de l'auteur) ; les mêmes règles valent pour tout projet perso.

Voisins : shell-maison, scripts-shell, osdev-c, osdev-asm, os-confidentialite
(firmwares séparés), integration-systeme (ABI versionnée), gestion-memoire
(malloc de la libc), unix-freebsd-linux (pratiques d'Unix, FreeBSD et
Linux à reprendre, sans leur code).

## Ce qui compte comme dépendance

- Livré dans l'image ou le binaire : chargeur, firmware, police, libc,
  helpers du compilateur, code copié ou porté, tables générées. C'est là
  qu'une licence tierce s'impose.
- Outils de build et de test (gcc, binutils, QEMU, OVMF, shellcheck,
  reuse, bats) : leur licence ne passe pas au produit, tant que leur code
  n'est pas embarqué.
- libgcc est embarquée quand elle est liée (GPL-3.0-or-later avec GCC
  Runtime Library Exception) : permis, mais c'est du code tiers.
  L'indépendance complète demande d'écrire soi-même les quelques helpers
  (`__udivdi3`, `__umoddi3`, `__divdi3`, `__moddi3` en 32 bits).
- Une spec (POSIX, ELF, System V ABI, Multiboot, ACPI, UEFI, Devicetree)
  s'implémente librement : on dépend du texte, pas d'un code. Vérifier les
  conditions de la spec et d'éventuels brevets avant un format
  propriétaire.

## Inventaire : REUSE

- `REUSE.toml` à la racine et textes dans `LICENSES/` (`reuse download
  GPL-2.0-or-later`). Les licences sont déclarées sans commentaire dans
  les fichiers : compatible avec la règle « pas de commentaires ».
  Exemple vérifié conforme : `exemples/projet-reuse/`.
- Copyright au nom de « Les contributeurs de <projet> », jamais un nom ni
  un email (AGENTS.md).
- Code tiers dans son dossier (`tiers/<composant>/`), annotation REUSE
  (licence, auteur amont, `precedence = "override"`) ; source et version
  notées dans `docs/licences.md` (local).
- `REUSE.toml` et `LICENSES/` font partie du livrable public : une notice
  de licence est une obligation, pas une doc personnelle.

## Audit : licences-tierces

```bash
licences-tierces --licence-projet GPL-2.0-or-later          # objectif : zéro code tiers
licences-tierces --licence-projet GPL-2.0-or-later --autorisees MIT,BSD-2-Clause
```

- Lance `reuse lint`, liste le code maison et le code tiers par licence.
  Code 1 si le projet n'est pas conforme REUSE, si une licence n'est pas
  autorisée, ou si un texte de licence (« GNU General Public License »,
  « Permission is hereby granted », SPDX, « Copyright (c) »...) apparaît
  dans une source déclarée maison. `reuse` seul ne voit pas ce dernier cas :
  vérifié, il déclare conforme un projet qui contient une copie GPL.
- Sans `--autorisees`, tout code tiers fait échouer. Chaque exception est
  une décision écrite dans la justification.
- Faux positif (un outil maison qui cherche des notices et contient donc
  leurs marqueurs comme données) : le déclarer dans
  `licences-exceptions.toml` à la racine, jamais découper la chaîne pour
  tromper le scanner. Une table `[[exception]]` par fichier avec
  `chemin`, `marqueurs` (reconnus par l'outil) et `raison`. Seuls ces
  marqueurs sont tolérés dans ce fichier, l'exception est affichée à
  chaque passage, et une exception qui ne sert plus fait échouer.
  `--exceptions FICHIER` pour un autre emplacement.
- `reuse lint` lit aussi les étiquettes SPDX dans le texte : un fichier
  qui contient `SPDX-License-Identifier:` comme donnée se déclare dans
  `REUSE.toml` avec `precedence = "override"` (vérifié : le contenu n'est
  alors plus lu).
- Cible `make licences` du projet, lancée avant chaque livraison.

## Clean room

- Écrire depuis la spec, la doc et le comportement observé (tests
  différentiels contre l'outil existant sur l'hôte), jamais en recopiant ni
  en paraphrasant du code. Même un code BSD ou MIT copié impose sa notice :
  c'est une dépendance.
- Lire un code tiers pour comprendre une idée (KolibriOS, Linux, dash,
  xv6) : noter la source dans la justification, fermer le fichier, réécrire
  à partir de sa compréhension ; en cas de doute, repartir de la spec.
- Code proposé par l'agent : écrit pour le projet. S'il reprend la forme
  d'un code connu, il le dit, et on repart de la spec.
- Pas de sortie brute de générateur sous licence restrictive : parser
  écrit à la main plutôt qu'un squelette de générateur.

## Nom et marques

- UNIX est une marque de The Open Group : dire « de type Unix » ou
  « inspiré d'Unix », jamais « un Unix ». POSIX est une marque de l'IEEE :
  « compatible avec un sous-ensemble de POSIX », sans certification.
- Ni le nom ni le logo d'un autre projet (KolibriOS) dans l'identité du
  système.

## Composants à écrire soi-même

| Composant | Tiers habituel (licence) | Version maison | Quand |
|-----------|--------------------------|----------------|-------|
| Helpers du compilateur | libgcc (GPL-3.0 + exception) | divisions 64 bits en 32 bits, testées contre libgcc sur l'hôte | dès qu'on veut lier sans `-lgcc` |
| libc et crt0 | newlib (licences BSD), musl (MIT) | `_start` vers `main(argc, argv, envp)` puis `exit`, stubs d'appels système, chaînes, mémoire, stdio tamponné, `malloc` (gestion-memoire), `errno` | avant les premières applis C |
| Shell | bash (GPL-3.0), dash (BSD-3-Clause) | shell-maison | après processus et fichiers |
| Outils de base | coreutils (GPL-3.0), busybox (GPL-2.0), toybox (0BSD) | `ls`, `cat`, `echo`, `cp`, `mv`, `rm`, `mkdir`, `ps`, `kill`, un binaire chacun ou multi-appel | avec le shell |
| init | systemd, sysvinit (GPL) | premier processus : lance le shell ou le bureau, récupère les zombies ; services à dépendances déclarées (idée de `rcorder`) | avec les processus |
| Pages de manuel | mandoc (ISC), man-db (GPL) | pages mdoc écrites pour le projet, afficheur réduit maison ; `mandoc -T lint` sur l'hôte seulement | avec les outils |
| Police | Terminus (OFL-1.1), Unifont (GPL ou OFL) | police bitmap 8×16 dessinée soi-même, outil de conversion maison | dès la console framebuffer |
| Chargeur | GRUB (GPL-3.0), Limine (BSD-2-Clause) | secteur de boot et appli UEFI (osdev-asm) ; Limine déclaré en attendant | tard, le noyau d'abord |
| ACPI (AML) | ACPICA (double licence), uACPI (MIT) | interpréteur AML maison, très gros | décision consciente : limiter les besoins ou accepter une dépendance déclarée |
| Firmwares (Wi-Fi, GPU, Pi) | propriétaires | aucun dans l'image de base (os-confidentialite) | option de l'utilisateur |

- Chaque composant maison se teste contre son équivalent de l'hôte :
  même entrée, même comportement (compare-shells pour le shell, même idée
  pour la libc et les outils).
- Système de base à la FreeBSD : noyau, libc, outils, manuels et tests
  dans un seul dépôt, construits par une commande, une version pour le
  tout ; ce que l'utilisateur ajoute vit à part (`/usr/local` chez
  FreeBSD), et les valeurs par défaut livrées sont séparées des réglages
  locaux (unix-freebsd-linux).

## Gabarit Unix-like i686

`templates/unix-like-i686/` : point de départ d'un système de type Unix,
toute la chaîne prouvée par `make test` (vérifié le 2026-09-29 : environ
10 s, deux démarrages BIOS et deux UEFI sous KVM) :

- `kernel/` : noyau durci repris d'osdev-c, qui vérifie que l'initrd
  (module Multiboot) arrive et commence par le magic cpio, puis `PASS`.
- `abi/` : numéros d'appels (`syscall.h`), liste des erreurs et types
  POSIX (`types.liste`, 64 bits pour `off_t`, `time_t`, `ino_t`), source
  unique du noyau et de la libc ; `outils/genere-errno` et
  `outils/genere-types` écrivent les en-têtes dans `build/`.
- `libc/` : `crt0`, appel système `int 0x80`, `write`, `getpid`, `_exit`,
  `exit`, `strlen`, `errno`, canari ; `libc.a` déterministe.
- `user/init.c` : `/init` lié sans libgcc à 0x400000, trois segments
  (`-z separate-code`), build-id ; `nm -u` vide vérifié.
- `racine/` : contenu de la partition ext2.
- `make test` : debug et release, programmes vérifiés, image démarrée en
  BIOS (i386) et UEFI (x86_64) par `qemu-test`, puis `make posix`
  (`verifier-posix` : noms d'erreurs et prototypes de la libc face à
  POSIX.1-2024, skill posix) et `licences-tierces`.

Le noyau n'exécute pas encore `/init` : mode utilisateur, appels système
et chargeur ELF sont le cœur à écrire (processus-unix, mode coach).
Justification : `docs/justifications/gabarit-unix-like.md`.

## Unix-like ou autre

- Unix-like : fichiers comme interface (`open`, `read`, `write`, `close`,
  descripteurs), processus (`fork`/`exec` ou `spawn`), tuyaux, signaux,
  environnement. Gain : outils et scripts portables, POSIX comme spec.
- Autre (VelumOS façon KolibriOS) : appels système numérotés, applis
  pilotées par événements, format maison. Une couche POSIX réduite peut
  venir plus tard pour porter des outils.
- Le choix est écrit dans la justification, et l'ABI est versionnée
  (integration-systeme).

## Prouver l'indépendance

- `make licences` : zéro code tiers non déclaré, et zéro tout court pour
  l'objectif « tout maison ».
- Lien sans libc de l'hôte ni libgcc : `-nostdlib -ffreestanding`, puis
  `nm -u` sur le binaire final doit être vide. Vérifié sur le gabarit
  osdev-c (vide) ; une division 64 bits en i686 fait apparaître
  `__udivdi3`.
- Image livrée : `strings` à la recherche de notices oubliées
  (« Copyright », « GNU », « BSD »).

## Références

- REUSE : reuse.software ; liste SPDX : spdx.org/licenses.
- POSIX.1-2024 : pubs.opengroup.org/onlinepubs/9799919799
- System V ABI (i386, x86-64) : gitlab.com/x86-psABIs ; spécification
  ELF (TIS) ; Multiboot ; Devicetree Specification.
