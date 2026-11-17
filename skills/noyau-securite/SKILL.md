---
name: noyau-securite
description: >-
  Durcissement d'un noyau hobby : canari, UBSan, W^X, NX, SMEP/SMAP/UMIP, pages de garde, copies user, Spectre. Use when hardening the kernel, writing syscall entry or reviewing for exploits.
---

# Sécurité du noyau

os-confidentialite dit ce que le noyau protège (isolation, permissions,
rien ne sort). Ce skill dit comment rendre ses bugs difficiles à exploiter
et faciles à voir. Chaque protection est prouvée par un test (charte du
projet) et son coût est mesuré (os-efficience). On ne retire pas une
protection pour un gain non mesuré.

Voisins : noyau-conception (kassert, verrous, `t_uptr`), c-bas-niveau,
pilotes-materiel (DMA, tables firmware), integration-systeme (fuzzing
hôte), code-review, unix-freebsd-linux (Capsicum, durcissements Linux).

## Modèle de menace d'abord

- Qui attaque : une appli malveillante ou buggée (appels système,
  formats chargés, IPC) ; un fichier ou une clé USB piégés (parseurs) ; un
  périphérique qui fait du DMA (IOMMU) ; l'accès physique, hors périmètre
  au début.
- `docs/charte.md` du projet dit ce qui est couvert et ce qui ne l'est pas
  encore, avec le test de chaque engagement.

## Drapeaux du compilateur

Vérifiés le 2026-09-29 en freestanding sur i686-elf-gcc 15.3 et clang 23
(i686, x86_64, aarch64, riscv64) ; les quatre premiers sont dans le
gabarit osdev-c, dont `make test` prouve le canari et le piège UBSan.

| Drapeau | Effet | À savoir |
|---------|-------|----------|
| `-fstack-protector-strong` | canari sur les fonctions à tableau local | fournir `__stack_chk_guard` (défini en asm) et `__stack_chk_fail` qui panique |
| `-fsanitize=undefined -fsanitize-trap=undefined` | UB changé en `ud2` (gcc) ou `ud1l` (clang), donc `#UD`, sans runtime | profil debug ; le handler `#UD` affiche EIP, puis `addr2line` |
| `-ftrivial-auto-var-init=zero` | locales mises à zéro : pas de fuite de pile non initialisée | peut appeler `memset`, à fournir |
| `-fzero-call-used-regs=used-gpr` | registres utilisés effacés au retour : moins de fuites et de gadgets ROP | petit coût, à mesurer |
| `-fno-delete-null-pointer-checks` | garde les tests de pointeur nul | |
| `-fno-strict-overflow` | débordement signé défini | release ; en debug, UBSan le détecte |
| `-Wframe-larger-than=1024 -Wvla` | pile noyau bornée | |
| `-fstack-clash-protection` | sondes sur les grosses frames | utile avec des piles à page de garde |
| `-fcf-protection=full` | `endbr` et shadow stack (CET) | seulement si le CPU a CET et que le noyau l'active |
| `-mindirect-branch=thunk-extern` (gcc), `-mretpoline-external-thunk` (clang) | retpoline contre Spectre v2 | fournir `__x86_indirect_thunk_*` |
| `-mbranch-protection=standard` (arm64) | PAC (`hint #25/#29`) et BTI | activer PAC (`SCTLR_EL1.EnIA`) et BTI (`SCTLR_EL1.BT1`, bit GP des pages) |

- Canari : valeur tirée au boot (RDSEED ou RDRAND si CPUID les annonce,
  sinon TSC mélangé), écrite avant qu'une fonction protégée ne retourne.
  Le gabarit part d'un canari fixe terminateur `0x000aff0d` (un octet nul
  arrête les copies de chaînes) en attendant l'aléa.
- Pas de `_FORTIFY_SOURCE` en freestanding : helpers de copie bornés et
  `__builtin_object_size` pour les tailles connues.
- KASAN demande une mémoire fantôme et un runtime : plus tard. En attendant,
  ASan sur l'hôte pour tout ce qui s'y teste.

## Mémoire du noyau

- W^X : text en RX, rodata en R, data et bss en RW sans exécution. Le
  gabarit sort trois segments séparés (`readelf -lW`). CR0.WP (bit 16)
  pour que le noyau respecte lui aussi la lecture seule.
- NX : CPUID 0x80000001 EDX bit 20, puis EFER.NXE (bit 11) ; demande PAE
  en 32 bits.
- SMEP (CR4 bit 20) et SMAP (CR4 bit 21) si CPUID leaf 7 EBX bits 7 et
  20 : le noyau ne peut ni exécuter ni lire la mémoire user par accident ;
  `stac` et `clac` autour des seules copies user. UMIP (CR4 bit 11, leaf 7
  ECX bit 2) : `sgdt`, `sidt`, `sldt`, `smsw`, `str` interdits en ring 3.
  ARM : PAN, PXN et UXN. RISC-V : bit SUM de `sstatus` à zéro hors copies.
- Page de garde sous chaque pile noyau ; double fault sur sa propre pile
  (tâche TSS en 32 bits, IST en 64 bits), NMI et `#MC` aussi en IST.
- Page 0 jamais mappée, pages noyau jamais accessibles en ring 3 (U/S à 0).
- Tas : poison à la libération, double libération détectée, en-têtes avec
  magic vérifié ; plus tard, pointeurs de liste libre masqués par un secret.
- Compteurs de références saturants : un débordement ne doit jamais
  ramener à zéro (use-after-free classique).
- Repris des options de Linux : décalage aléatoire de la pile noyau à
  chaque appel système (`RANDOMIZE_KSTACK_OFFSET`), mémoire mise à zéro à
  l'allocation ou à la libération (`INIT_ON_ALLOC_DEFAULT_ON`,
  `INIT_ON_FREE_DEFAULT_ON`), copie user bornée par la taille réelle de
  l'objet noyau visé (`HARDENED_USERCOPY`). Chacune avec son test et son
  coût mesuré.
- Page effacée avant d'être donnée à une appli, secrets effacés après usage
  (os-confidentialite).

## Frontière user

- Entrée d'appel système : sauver les registres, effacer ceux qui ne
  servent pas au retour (pas de valeur noyau qui fuit), vérifier le numéro.
- Numéro et indices venus d'une appli : borne vérifiée, puis indice masqué
  sans branche contre la spéculation (Spectre v1, idée de
  `array_index_nospec`), ou `lfence` après la vérification sur x86.
- Copie user : une fonction par sens (`t_uptr`, noyau-conception) qui
  vérifie `adresse + taille` sans débordement et dans l'espace user, ouvre
  SMAP (`stac`) seulement pendant la copie, et rattrape une faute de page
  pendant la copie par une table d'exceptions (instruction fautive vers
  adresse de reprise qui rend `E_FAULT`). Jamais « la page était présente
  à la vérification » : en SMP, une autre tâche peut la retirer.
- Structure user : copiée une fois, puis validée sur la copie (double
  lecture, os-confidentialite).
- Drapeau inconnu refusé (`EINVAL`), octets d'une structure plus récente
  refusés s'ils ne sont pas nuls (`E2BIG`), taille plafonnée : l'ABI
  extensible est aussi une protection (`unix-freebsd-linux/exemples`).
- Aucune adresse noyau ne sort : ni retour, ni message, ni registre.
- Retour en ring 3 : IF à 1, IOPL à 0, NT à 0 ; en x86-64, `sysret` avec
  un RIP non canonique faute en ring 0 sur Intel (CVE-2012-0217) :
  vérifier ou repasser par `iret`.
- Pas d'I/O directe pour les applis : IOPL à 0 et bitmap d'I/O du TSS
  fermée, sauf pilote user autorisé explicitement.

## Spéculation

- Lire au boot : CPUID leaf 7 EDX (bit 10 MD_CLEAR, 26 IBRS/IBPB, 27
  STIBP, 29 ARCH_CAPABILITIES, 31 SSBD) et le MSR IA32_ARCH_CAPABILITIES
  (0x10A : bit 0 RDCL_NO, bit 5 MDS_NO).
- Meltdown (Intel sans RDCL_NO) : tables séparées en ring 3 (KPTI),
  coûteux sans PCID, donc seulement sur CPU touché, chiffre avant et après
  dans la justification.
- Spectre v1 : masquage des indices, toujours actif, presque gratuit.
- Spectre v2 : retpoline ou IBRS selon le CPU ; un petit noyau a peu
  d'appels indirects, les compter d'abord.
- MDS : `verw` au retour en ring 3 si MD_CLEAR et CPU touché.
- FPU : sauvegarde à chaque bascule (XSAVE), jamais paresseuse (LazyFP,
  CVE-2018-3665).
- Choix fait par CPU détecté et annoncé au boot (`meltdown: KPTI actif`),
  jamais global et silencieux.
- Secrets comparés en temps constant.

## Chargement et intégrité

- Appli : en-tête vérifié, tailles bornées, segments W^X, pas de
  relocation dans le code. Plus tard, signature vérifiée par le noyau.
- Aléa pour canari, piles et plus tard KASLR : RDSEED ou RDRAND (CF
  vérifié, réessais, jamais seuls) mélangés dans un pool. KASLR n'a de
  sens que si aucune adresse noyau ne fuit.

## Tester

- `make test` du gabarit : canari et piège UBSan prouvés à chaque tour.
- Tests négatifs pour chaque appel système : pointeur nul, noyau, non
  canonique, `adresse + taille` qui déborde, page absente, taille énorme,
  numéro hors table. Attendu : erreur propre, noyau vivant.
- Fuzzer d'appels système dans l'OS : une appli de test enchaîne des
  appels au hasard (graine affichée, rejouable) pendant N minutes en
  profil debug. Toute panique est un bug, reproduit par sa graine. Idée de
  syzkaller et trinity, en petit.
- Parseurs (ELF, VELUMAPP, FAT, ACPI, DTB) nourris d'entrées tronquées et
  corrompues sur l'hôte avec ASan (integration-systeme).
- Relecture (code-review) : entier qui déborde dans un calcul de taille,
  vérification puis usage sur mémoire user, verrou oublié, chemin d'erreur
  qui fuit une ressource.

## Références

- Kernel Self Protection Project : kspp.github.io.
- Intel SDM vol. 3 (SMEP, SMAP, UMIP, CET) ; documents Intel et ARM sur
  les canaux auxiliaires de l'exécution spéculative.
- Linux `Documentation/admin-guide/hw-vuln/` : lire pour comprendre.
