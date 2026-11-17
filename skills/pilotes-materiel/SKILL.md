---
name: pilotes-materiel
description: >-
  Pilotes et vrai matériel en C freestanding : spec, CPUID, ACPI, PCI, device tree, MMIO, IRQ, DMA, timeouts. Use when writing a driver or when it works in QEMU but not on a real machine.
---

# Pilotes et matériel

QEMU émule un matériel propre et bien élevé. Une vraie machine a des
firmwares buggés, des délais, des caches pas toujours cohérents et des
erratas. Un pilote se lit dans la spec, découvre ce qui est là, borne chaque
attente et se teste d'abord sans le matériel.

Voisins : c-bas-niveau (volatile, asm inline, UB), osdev-c (boot, roadmap),
integration-systeme (preuves par paliers, vraie machine, clé USB),
os-confidentialite (DMA et IOMMU), os-efficience (mesures).

Mode coach (AGENTS.md) : l'agent lit la spec avec l'auteur, prépare la table
des registres, le faux périphérique et le banc de test, relit et débogue.
La logique du pilote suit la répartition d'AGENTS.md.

## La spec fait foi

- Ordre de confiance : spec ou datasheet du composant, puis ses erratas,
  puis un code de référence (Linux, BSD, KolibriOS : lire, ne jamais copier
  du GPL), puis le wiki OSDev (utile, parfois daté ou faux). Un registre
  trouvé dans un tuto se recoupe avant usage.
- Par pilote, un en-tête qui donne la carte des registres : offset,
  largeur, accès (RO, RW, W1C, RC, W1S), bits nommés, valeur au reset.
  La référence précise (spec, version, section) va dans
  `docs/justifications/<pilote>.md`, pas en commentaire.
- Specs utiles : Intel SDM vol. 3, AMD APM vol. 2, ACPI et UEFI
  (uefi.org/specifications), PCI Local Bus et PCIe Base, AHCI 1.3.1,
  NVMe Base, xHCI, datasheet 16550 (TI PC16550D), 8259A, 82093AA
  (IOAPIC), IA-PC HPET, ARM ARM (DDI 0487), GIC Architecture
  Specification, PL011 TRM, RISC-V Privileged, RISC-V SBI, RISC-V PLIC,
  Devicetree Specification (devicetree.org), virtio (OASIS).

## Découvrir au lieu de supposer

Aucune adresse, IRQ ou fonction CPU en dur hors des cas imposés par
l'architecture (COM1 0x3F8 sur PC, par exemple).

- CPU : `cpuid` avant toute fonction (PAE, NX leaf 0x80000001 EDX bit 20,
  APIC leaf 1 EDX bit 9, x2APIC, TSC invariant leaf 0x80000007 EDX bit 8,
  SSE, RDRAND). ARM : registres `ID_AA64*_EL1`. RISC-V en mode S :
  `riscv,isa-extensions` du DTB. Fonction absente : message clair et
  repli, jamais un `#UD` trois fonctions plus loin.
- Carte mémoire (Multiboot, Limine, UEFI) : trier, fusionner, jeter les
  zones de longueur nulle, arrondir les zones libres vers l'intérieur à
  4 Kio. Ne jamais réutiliser ACPI NVS ni le réservé ; ACPI reclaimable
  seulement après lecture des tables. Les BIOS réels donnent des zones en
  désordre ou qui se chevauchent.
- ACPI (x86) : RSDP donné par le chargeur (requête Limine, tag
  Multiboot 2, table de configuration EFI), sinon balayage BIOS (premier
  Kio de l'EBDA puis 0xE0000 à 0xFFFFF, pas de 16). Chaque table :
  signature, longueur bornée, somme des octets nulle. XSDT si révision
  >= 2 et adresse non nulle, sinon RSDT. MADT : LAPIC, IOAPIC,
  overrides (l'IRQ 0 du PIT arrive souvent sur la GSI 2). FADT : reset,
  PM timer, `IAPC_BOOT_ARCH` bit 1 (8042 présent), indice seulement car
  des firmwares le mettent faux. HPET et MCFG absents sur les vieux PC.
  L'AML (DSDT, SSDT, nécessaire pour `\_S5` et l'extinction) demande un
  interpréteur : plus tard, uACPI (MIT) ou ACPICA, en code tiers.
- PCI : vendor 0xFFFF = absent ; bit 7 du header type = multifonction ;
  pont PCI-PCI (classe 0x06, sous-classe 0x04) : scanner le bus
  secondaire. Accès legacy 0xCF8/0xCFC (256 octets) ou ECAM par la MCFG
  (4 Kio par fonction). BAR : type (I/O ou mémoire, 32 ou 64 bits sur deux
  BAR, prefetchable), taille par écriture de 0xFFFFFFFF avec le décodage
  coupé dans le registre de commande, puis restaurer. Associer le pilote
  par classe, sous-classe, prog-if (AHCI 01/06/01, NVMe 01/08/02, xHCI
  0C/03/30, EHCI 0C/03/20) plutôt que par liste d'IDs. Activer memory
  space et bus master (bit 2) seulement pour le périphérique piloté.
- Device tree (ARM, RISC-V) : DTB donné par le chargeur (requête Limine,
  U-Boot, firmware du Pi ; OpenSBI le passe en `a1`, hart id en `a0` ;
  `x0` dans le protocole de boot arm64 de Linux). Le FDT est
  **big-endian** : convertir chaque champ. Vérifier magic 0xd00dfeed,
  `totalsize`, offsets et version avant de lire. `compatible` choisit le
  pilote, `reg` se lit avec `#address-cells` et `#size-cells` du parent,
  `interrupts` avec `interrupt-parent`, `status = "okay"`, `/chosen`
  (`stdout-path`), `timebase-frequency` dans `/cpus` (RISC-V). libfdt
  (BSD-2 ou GPL au choix) en code tiers, ou parseur maison testé sur
  l'hôte avec de vrais DTB (`qemu-system-riscv64 -M
  virt,dumpdtb=build/virt.dtb`).

## MMIO

- Accès à la largeur de la spec : un registre 32 bits se lit et s'écrit
  en 32 bits (AHCI l'exige). Helpers `mmio_read32` / `mmio_write32`
  (`volatile`) ; sur ARM, asm `ldr`/`str` explicites, sinon gcc peut
  fusionner, découper ou choisir un mode d'adressage que l'hyperviseur
  ne sait pas émuler.
- Registres par masques et décalages. Une structure de registres est
  possible si chaque champ est `volatile uint32_t` et chaque offset vérifié
  par `_Static_assert(offsetof(...))`. Jamais de champs de bits C.
- W1C : écrire seulement le masque à effacer ; un lire-modifier-écrire
  effacerait les autres bits posés. RC : une lecture change l'état, y
  compris une lecture de debug. Lire-modifier-écrire d'un registre partagé
  avec un handler : interruptions coupées autour.
- Écritures postées (PCI) : l'écriture peut ne pas être arrivée. Relire un
  registre du même périphérique avant un délai ou un acquittement.
- Ordre, par architecture :
  - x86 : MMIO non cacheable (PCD|PWT dans la page, ou PAT). L'ordre est
    fort, une barrière compilateur suffit en général. Framebuffer en
    write-combining : `sfence` avant de prévenir le périphérique.
  - ARMv8 : MMIO mappé Device-nGnRE (MAIR), jamais Normal. `dmb` ordonne,
    `dsb` attend la fin (avant un DMA, avant `wfi`), `isb` après un
    registre système. MMU coupée : tout est Device et un accès non aligné
    faute, donc `-mstrict-align` pour ce code (`-mno-unaligned-access` en
    ARM 32 bits).
  - RISC-V : `fence w,o` avant l'écriture qui lance le périphérique,
    `fence i,r` après la lecture d'un statut, `fence.i` après avoir écrit
    du code, `sfence.vma` après un changement de tables de pages.
- Endianness : PCI, USB, AHCI, NVMe, virtio moderne en little-endian ;
  DTB et en-têtes réseau en big-endian. Helpers `le32_to_cpu` /
  `be32_to_cpu` même sur une arch little-endian : le code dit ce qu'il lit.

## Attendre le matériel

- Aucune boucle `while (!(reg & READY))` sans limite. Timeout en temps
  réel : TSC calibré sur le PIT ou le HPET, compteur ACPI PM (3,579545
  MHz), timer générique ARM (`CNTFRQ_EL0`, `CNTVCT_EL0`), CSR `time` et
  `timebase-frequency` sur RISC-V. Un nombre d'itérations n'est pas un
  temps : un CPU dix fois plus rapide divise l'attente par dix.
- Timeout : message (pilote, registre, valeur lue), périphérique
  désactivé, le système continue sans lui.
- Délais imposés par la spec (reset, mise sous tension d'un port) :
  respectés au minimum, relus dans la spec.

## Interruptions

- Handler : lire la cause dans le périphérique, l'acquitter dans le
  périphérique, puis EOI au contrôleur. Le travail long sort du handler.
- Niveau ou front : une ligne à niveau non acquittée redéclenche sans fin
  (tempête d'IRQ) ; un front manqué ne revient jamais, donc relire le
  statut après réarmement.
- x86 legacy : 8259 remappé ; IRQ 7 et 15 parasites : lire l'ISR (OCW3
  0x0B), pas d'EOI si le bit est absent (IRQ 15 parasite : EOI au maître
  seulement). APIC : activer par le registre spurious (0xF0), EOI en
  écrivant 0 à 0xB0, IOAPIC avec les overrides de la MADT, 8259 masqué
  (0xFF sur 0x21 et 0xA1). PCI : MSI ou MSI-X plutôt que les lignes INTx
  partagées.
- ARM : GIC (v2 par défaut sur QEMU `virt`, `gic-version=3` possible et
  courant sur les cartes récentes), IAR pour prendre, EOIR pour finir,
  adresses depuis le DTB. RISC-V : PLIC (claim puis complete) pour
  l'externe ; timer par SBI (extension TIME) ou `stimecmp` si Sstc.
- Données partagées entre handler et code normal : c-bas-niveau.

## DMA et caches

- Le périphérique voit des adresses physiques (ou d'IOMMU), jamais
  virtuelles. Tampons contigus, ou scatter-gather ; alignements de la spec
  (AHCI : liste de commandes 1 Kio, FIS reçus 256 octets, table de
  commande 128 octets).
- Contrôleur sans adressage 64 bits : tampons sous 4 Gio. DMA ISA : sous
  16 Mio.
- Cohérence : sur PC, le DMA est cohérent. Sur ARM et beaucoup de RISC-V,
  pas forcément : nettoyer (`dc cvac`) avant que le périphérique lise,
  invalider (`dc ivac`) avant que le CPU lise ce qu'il a écrit, puis
  `dsb`. Tampons alignés et dimensionnés sur la ligne de cache (lue dans
  `CTR_EL0`), ou mappés non cacheables.
- Ordre : écrire le descripteur, barrière d'écriture (`sfence`, `dsb st`,
  `fence w,o`), puis sonner la doorbell.
- Bus master activé quand le pilote est prêt, coupé à l'arrêt. Sans
  IOMMU, un périphérique qui fait du DMA lit toute la RAM
  (os-confidentialite).

## Entrées sur un vrai PC

- USB legacy : le firmware émule un clavier PS/2 par SMM tant que l'OS n'a
  pas pris le contrôleur. Prise de main par la capacité USBLEGSUP (xHCI)
  ou EECP (EHCI), avec timeout, avant de toucher au contrôleur.
- PS/2 : tester le 8042 (FADT puis réponse au port 0x64 avec timeout).
  Beaucoup de portables récents n'en ont plus : prévoir xHCI + HID.
- Port série : absent sur la plupart des portables (integration-systeme,
  « voir ce qui se passe »).

## USB

- Contrôleurs : xHCI sur les PC récents (et USB 2 et 1 à travers lui),
  EHCI avec UHCI ou OHCI compagnons sur les anciens. Prise de main
  BIOS/OS d'abord (section précédente).
- xHCI : contexte des périphériques (DCBAA), anneau de commandes, anneau
  d'événements, anneau de transfert par endpoint ; doorbells ; tout en DMA
  (section DMA et caches).
- Énumération : port réinitialisé, `Address Device`, descripteur de
  périphérique, de configuration, `Set Configuration`, puis le pilote de
  classe. Hubs : même travail derrière chaque port.
- Classes à écrire d'abord : HID en protocole boot (clavier, souris),
  stockage de masse Bulk-Only avec commandes SCSI (READ(10), WRITE(10),
  READ CAPACITY), qui deviennent un périphérique bloc (fichiers-unix).
- Descripteurs venant du périphérique : entrées non fiables (longueurs,
  nombres d'interfaces et d'endpoints bornés).
- QEMU : `-device qemu-xhci -device usb-kbd -device usb-mouse`,
  `-drive if=none,id=cle,file=build/cle.img,format=raw -device
  usb-storage,drive=cle`.
- Spécifications : xHCI 1.2, USB 2.0 et 3.2, HID 1.11, Mass Storage
  Bulk-Only Transport.

## Quirks

- Un contournement vise une machine ou une puce identifiée (DMI/SMBIOS,
  IDs PCI, révision), s'annonce au démarrage (`quirk <nom> appliqué`) et
  s'inscrit dans la fiche matériel. Jamais un délai global « parce que ça
  marche mieux ».
- Tables du firmware, descripteurs USB, DTB : entrées non fiables. Bornes,
  longueurs et sommes vérifiées, parseurs testés avec des entrées tronquées
  et corrompues (integration-systeme).

## Tester un pilote

1. Logique séparée des accès : le pilote passe par une petite interface
   (`read32`, `write32`, attente). Sur l'hôte, un faux périphérique
   (tableau de registres + petite machine à états) rejoue la séquence de
   la spec, cas d'erreur compris (timeout, bit d'erreur, W1C). Tests avec
   `-fsanitize=address,undefined`.
2. QEMU : virtio pour avancer vite, puis le modèle du vrai matériel
   (`-machine q35` pour l'AHCI, `-device qemu-xhci`, `-device nvme`,
   `-device e1000`). `-d guest_errors,unimp` montre les accès à des
   registres non implémentés ; `-trace help` liste les traces
   (`-trace 'ahci_*'`).
3. Vraie machine (integration-systeme), résultat dans la fiche matériel.

## Références

- OSDev wiki : PCI, ACPI, RSDP, MADT, Detecting Memory (x86), APIC, 8259
  PIC, USB, xHCI, AHCI, Serial Ports. Passer par web.archive.org si le
  site bloque.
- Linux `Documentation/driver-api/` et `Documentation/core-api/` (barrières,
  DMA) pour comprendre les pièges ; code GPL : lire, ne pas copier.
- Devicetree Specification : devicetree.org/specifications.
