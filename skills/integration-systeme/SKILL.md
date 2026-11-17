---
name: integration-systeme
description: >-
  Intégration d'un OS hobby : contrats versionnés, build reproductible, preuves par paliers, clé USB (ecrire-image). Use when assembling boot, kernel and drivers, or testing on real hardware.
---

# Intégration système

Un OS, c'est un chargeur, un noyau, des pilotes, des applis et des formats
qui doivent tenir ensemble sur des machines qu'on ne contrôle pas. Chaque
étage prouve ce qu'il fait, chaque interface a un contrat écrit et testé,
chaque binaire se retrouve et se reconstruit.

Voisins : osdev-c (boot, `make test`), pilotes-materiel (écrire un
pilote), os-efficience (`make mesure`), os-confidentialite (charte),
tests-locaux, make, linker-scripts.

Mode coach (AGENTS.md) : l'échafaudage (Makefile, harness de test,
scripts, fiche matériel) revient à l'agent ; le cœur reste à l'auteur.

## Contrats entre couches

- Interfaces à contrat : chargeur vers noyau (infos de boot), cœur vers
  arch (`kernel/arch.h`), noyau vers pilotes, noyau vers applis (appels
  système, format VELUMAPP), formats sur disque.
- Format binaire : magic, version, taille de la structure (pour l'étendre
  sans casser), champs réservés à zéro et vérifiés. En-tête commun inclus
  des deux côtés, `_Static_assert` sur la taille et les offsets.
- Compatibilité : on ajoute à la fin ; on ne réutilise jamais un numéro
  d'appel système ni un bit de permission ; on déprécie au lieu de changer
  le sens. Rupture = version majeure, et le noyau refuse une version
  inconnue avec un message.
- Convention d'appel système écrite par arch (registre du numéro, des
  arguments, du retour ; erreur en code négatif).
- Numéro d'ABI entier incrémenté à chaque changement visible (idée de
  `__FreeBSD_version`), affiché au boot et porté par chaque binaire dans
  une note ELF (idée de `NT_FREEBSD_ABI_TAG`) ; le noyau refuse un binaire
  plus récent que lui. Chaque interface a un statut écrit : stable, en
  test, obsolète, retirée (idée de `Documentation/ABI/` de Linux).
  Conception d'un nouvel appel : unix-freebsd-linux.
- Tests des deux côtés : une fixture binaire de référence
  (`tests/fixtures/*.bin`) produite par l'outil qui fabrique les applis et
  lue par le chargeur du noyau.

## Build reproductible

- Versions épinglées : toolchain, Limine, QEMU (le comportement change
  d'une version à l'autre), firmwares OVMF, notées avec le projet.
  Téléchargements vérifiés par sha256 dans le Makefile, jamais de
  `curl | sh`.
- Rien qui dépend du poste : `-ffile-prefix-map=$(CURDIR)=.`,
  `SOURCE_DATE_EPOCH` pour les dates (ISO, en-têtes), sources triées
  (`$(sort $(wildcard ...))`), `LC_ALL=C`, archives `ar` déterministes.
- Preuve : `make repro` construit deux fois dans deux dossiers de `build/`
  et compare les sha256. Un écart est un bug.
- Identité : `-Wl,--build-id`, affiché au démarrage avec la version et
  `git describe --dirty`. L'ELF avec symboles est gardé par build-id dans
  `build/` pour passer un crash venu d'une vraie machine dans `addr2line`.
- Une commande par cible (`make ARCH=x86_64`, `make test-all`). Tout
  réglage du poste nécessaire au build est écrit (Makefile ou
  `memory/machine/toolchain.md`).

## Preuves par paliers

Chaque étape descend les paliers dans l'ordre ; on ne passe au suivant
qu'avec le précédent vert.

| Palier | Ce qu'on prouve | Comment |
|--------|-----------------|---------|
| 1. Hôte | logique pure : allocateurs, printf, parseurs ACPI, DTB, ELF, FAT, VELUMAPP | tests + `-fsanitize=address,undefined` ; parseurs nourris d'entrées tronquées et corrompues (libFuzzer ou AFL++ si présents) |
| 2. Faux matériel | séquences de pilote, erreurs, timeouts | modèle de registres sur l'hôte (pilotes-materiel) |
| 3. QEMU par arch | boot et étapes sur chaque cible | `make test-all`, sans écran, timeout, marqueurs série |
| 4. QEMU variantes | ce qui change d'une machine à l'autre | voir liste plus bas |
| 5. Bochs (x86) | descripteurs, changements de mode | plus strict que QEMU |
| 6. Vraie machine | firmware réel, délais, quirks | clé USB, fiche matériel |

Variantes QEMU utiles (vérifiées sur QEMU 10.2) : `-machine pc` et `q35` ;
`-machine pc,hpet=off` et `acpi=off` pour les chemins sans HPET ni ACPI ;
`-cpu 486`, `pentium`, `pentium3`, `core2duo`, `max` ; `-smp 1` et `4` ;
`-m` au minimum (`RAM_MIN`) ; BIOS et UEFI (OVMF) ; ARM `virt` avec
`gic-version=2` et `3`. QEMU ne garantit pas de faire fauter une
instruction absente du CPU choisi : pour viser les Pentium, chercher
`cmov` dans `objdump -d`.

## Image disque et lancement

```bash
image-disque --noyau build/kernel.elf --racine racine/ --initrd initrd/ \
             --sortie build/disque.img [--protocole multiboot1|multiboot2|limine]
qemu-test --disque build/disque.img --arch x86_64 [--uefi] \
          --attendu PASS --echec FAIL --delai 60
```

- `image-disque` : GPT, partition 1 ESP en FAT (Limine BIOS et UEFI,
  `limine.conf`, noyau, `initrd.cpio`), partition 2 racine en ext2
  remplie depuis un dossier, partition 3 de démarrage BIOS (sans elle,
  Limine refuse de s'installer en BIOS sur GPT). Sans root : écriture aux
  décalages par mtools et `mkfs.ext2 -E offset=`. Les fichiers de la
  racine gardent l'uid de l'hôte (1000) : l'OS l'ignore ou s'en sert
  comme utilisateur par défaut.
- Lire l'image sans la monter : `mdir -i img@@2M -/ ::`, `debugfs -R
  'ls -l /' 'img?offset=35651584'` (racine à 34 Mio avec l'ESP par défaut).
- `qemu-test` : série dans `build/qemu-test/serie.log`, séquences ANSI
  retirées (Limine en UEFI en met partout), le premier marqueur rencontré
  décide, KVM pour x86 si possible. Mesuré sur le gabarit Unix-like,
  machine au repos : BIOS i386 1 s, UEFI x86_64 1,6 s avec KVM et 4,6 s
  sans. Les mêmes démarrages montent à 7 ou 8 s quand la machine compile
  en parallèle : garder un délai large (60 s), jamais 5 s.
- Justification : `docs/justifications/image-disque-et-qemu-test.md`.

## Protocole de sortie des tests

- Marqueurs série stables, un par étape (`[ok] gdt`, `[ko] idt: ...`),
  dernière ligne `PASS` ou `FAIL <raison>`. Le harness échoue sur `FAIL`,
  sur absence de `PASS` et sur timeout.
- Sortie de QEMU avec un code :
  - x86 : `-device isa-debug-exit,iobase=0xf4,iosize=0x04`, QEMU sort
    avec `(v << 1) | 1`.
  - RISC-V `virt` : `sifive_test` à 0x100000 (vu dans `info mtree`) ;
    écrire 0x5555 pour réussir, `(code << 16) | 0x3333` pour échouer.
  - ARM `virt` : PSCI `SYSTEM_OFF` (0x84000008), conduit `hvc` ou `smc`
    lu dans le nœud `/psci` du DTB ; ou semihosting (`-semihosting`).
- Panic : registres, build-id et dernière étape sur la série et à l'écran,
  puis arrêt (`cli` + `hlt` en boucle sur x86). Jamais de reboot
  silencieux.

## Vraie machine

### Avant

- Inventaire : démarrer un Linux live sur la machine cible et relever
  `lspci -nn`, `lsusb`, `/proc/cpuinfo`, `dmidecode -t system,bios`
  (root) et, si possible, `acpidump`. C'est la liste des pilotes à écrire
  et la base de la fiche.
- Machine de test sans données personnelles, jamais le poste de dev.
- Firmware : Secure Boot coupé (des clés à soi plus tard), CSM ou Legacy
  pour tester le chemin BIOS quand il existe, touche du menu de boot notée.
  Pas de mise à jour ni de flash du firmware pour faire marcher l'OS.
- Image hybride, démarrable en CD et en clé (`grub2-mkrescue`,
  `limine bios-install`).

### Écrire la clé

```bash
ecrire-image build/velumos.iso /dev/disk/by-id/usb-...        # simulation
ecrire-image build/velumos.iso /dev/disk/by-id/usb-... --ecrire
```

Le script refuse tout sauf une clé USB ou une carte SD (l'eMMC interne
est refusée), rien de monté, 256 Gio au plus (`--taille-max`). Il affiche
modèle, série et taille, écrit avec `dd conv=fsync`, vide le cache puis
relit la clé et la compare à l'image. `pkexec` demande le mot de passe si
le nœud n'est pas inscriptible. La garde des hooks demande confirmation
pour `--ecrire` et pour toute écriture directe sur un disque : pas de `dd`
à la main vers `/dev/sdX`. Clé montée par le bureau : `udisksctl unmount
-b /dev/sdX1`. Justification : `docs/justifications/materiel-sans-risque.md`.

### Voir ce qui se passe

- Série : port COM ou carte série PCIe sur un fixe, câble null-modem et
  adaptateur USB, 115200 8N1. Côté poste : `tio -b 115200 -L --log-file
  build/materiel/<machine>-<date>.log /dev/ttyUSB0` (tio installé,
  utilisateur dans le groupe dialout).
- Sans série (portables) : console framebuffer dès le début, code
  d'étape sur le port 0x80 (lisible avec une carte POST), photo de
  l'écran au crash. Plus tard : xHCI Debug Capability (câble USB 3 A-A de
  debug) ou journal réseau.

### Cartes ARM et RISC-V

- UART en 3,3 V : adaptateur USB-TTL 3,3 V, TX vers RX, masse commune.
  Jamais de RS-232 (±12 V) ni de 5 V sur les broches.
- Brancher hors tension, une seule alimentation, se décharger sur une
  masse avant de toucher la carte.
- Firmware propriétaire (Raspberry Pi) sur sa partition, séparé de
  l'image (os-confidentialite).

### Jamais

- Écrire sur un disque interne avant que le pilote ait passé tous ses
  tests sur image dans QEMU ; ensuite seulement sur une machine de test
  sauvegardée. Pilote disque en lecture seule par défaut, écriture
  derrière une option de build.
- Flasher le firmware, écrire des variables EFI ou changer l'ordre de
  boot depuis l'OS en développement (des portables Samsung ont été rendus
  inutilisables en 2013 par des écritures de variables EFI).
- Laisser tourner une machine qui chauffe anormalement.

## Fiche matériel

`docs/materiel.md` du projet (local, jamais poussé) : une ligne par essai.
Date, commit et build-id, machine (modèle, CPU, RAM, BIOS ou UEFI et
version), mode de boot, résultat par étape (boot, série, écran, clavier,
timer, disque), quirks vus, chemin du journal. C'est la matrice de
compatibilité et la source des quirks (pilotes-materiel).

## Régressions

- Chaque commit construit et passe `make test` : `git bisect run make
  test-all` trouve seul le commit fautif. Un changement logique par
  commit, comme le demandent Linux et FreeBSD ; `make test-all` joue le
  rôle du `make universe` de FreeBSD.
- Règle « no regressions » de Linux : une appli ou un test qui marchait
  et ne marche plus bloque la livraison, même si le changement est
  « plus juste ».
- Un bug vu sur vraie machine devient un test : même configuration dans
  QEMU si elle le reproduit, sinon la table ou le descripteur fautif
  rejoué en fixture sur l'hôte.
- CI si l'auteur la veut : la même `make test-all` en matrice d'arch,
  toolchain en cache. Les tests restent d'abord lancés ici (tests-locaux).

## Références

- reproducible-builds.org (SOURCE_DATE_EPOCH, bonnes pratiques).
- Doc QEMU : invocation, `-device help`, `-trace help`, `info mtree`.
- OSDev wiki : Serial Ports, Detecting Memory (x86), Bochs, QEMU.
