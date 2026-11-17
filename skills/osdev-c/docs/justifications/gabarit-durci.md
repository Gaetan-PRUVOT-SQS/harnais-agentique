# Feature : gabarit noyau durci, deux profils, preuves au test

Date : 2026-09-29

## Métier

- Besoin : tout nouveau noyau (VelumOS ou labo) part de
  `templates/i686-multiboot`. S'il part sans durcissement, les débordements
  de pile et les UB passent inaperçus jusqu'au jour où ils deviennent une
  faille ou un crash introuvable.
- Qui est concerné : L'auteur au démarrage d'un projet noyau, l'agent qui
  relance `make test` à chaque fin de tour.
- Impact si on ne le fait pas : durcissement ajouté tard, jamais prouvé,
  cassé en silence par un changement de flags.

## Ce qu'on fait

- Comportement visible : `PROFIL=debug` (défaut) et `PROFIL=release`,
  sorties dans `build/<profil>-v<VERIF>/`. `make test` démarre les deux
  profils, prouve que le canari déclenche la panique et que le piège UBSan
  lève un `#UD`. Build-id dans l'ELF.
- Fichiers touchés : `Makefile`, `linker.ld`, `boot.S`, `kernel.c`,
  `serial.c`, `serial.h`, `panic.c`, `panic.h`, `verif.c`, `verif.h`.

## Choix techniques

| Choix | Pourquoi | Alternative rejetée | Impact métier |
|-------|----------|---------------------|---------------|
| Deux profils, tous deux testés | debug attrape les UB, release est ce qu'on livre | un seul profil | on ne livre jamais un binaire jamais testé |
| UBSan en mode piège (`-fsanitize-trap`) | aucun runtime à écrire, `ud2` ou `ud1l` suffit | runtime `__ubsan_handle_*` maison | UB visibles dès le premier jour |
| `-fno-strict-overflow` en release seulement | en debug il couperait la détection UBSan du débordement signé | partout | détection en debug, comportement défini en release |
| Canari : `__stack_chk_guard` dans `boot.S` | valeur fixe en `.data`, présente dès la première instruction, avant tout C | `-mstack-protector-guard-symbol` (réservé au mode TLS) | le canari existe avant `kmain`, sans initialisation C |
| Canari fixe terminateur `0x000aff0d` | pas encore d'aléa au boot, l'octet nul arrête les copies de chaînes | canari à 0 | protège déjà contre les débordements par chaîne |
| `panic.c` à part, `__stack_chk_fail` y appelle `panic` | une seule sortie de secours, message sur la série | arrêt muet | l'erreur se lit dans le journal |
| `serial.c` à part, attente bornée | une responsabilité par fichier ; pas de timer au boot, borne en nombre de lectures de port | boucle sans limite | pas de gel sur un UART bloqué |
| `verif.c` et `VERIF=1/2` | preuve que canari et piège marchent vraiment, dans le vrai noyau | faire confiance aux flags | un flag cassé fait échouer `make test` |
| Pointeur `volatile` dans `verif_canari` | sans lui gcc supprime les écritures et le tableau, donc le canari | tableau lu après coup | le test mesure bien le canari |
| Build-id dans sa propre section | dans `.rodata` la note héritait de l'alignement 4 Kio et readelf la jugeait corrompue | pas de build-id | un journal se rattache au binaire exact |
| `.note.GNU-stack` dans `boot.S` | sans elle, un lien sans `-z noexecstack` annonce une pile exécutable | compter sur le seul drapeau du Makefile | pile non exécutable quel que soit le lien (segment `GNU_STACK` vérifié) |
| `build/` par profil et `-MMD -MP` | profils sans mélange d'objets, rebuild juste quand un en-tête change | objets à côté des sources | builds fiables, `make clean` simple |

## Traçabilité

| Fichier | Fonction / bloc | Justifié par |
|---------|-----------------|--------------|
| `Makefile` | `PROFIL`, `DURCI` | deux profils, UBSan piège, `-fno-strict-overflow` |
| `Makefile` | `test`, `demarre`, `canari`, `piege` | deux profils testés, `VERIF` |
| `Makefile` | `B`, `-MMD -MP` | `build/` par profil |
| `boot.S` | `__stack_chk_guard` | canari en asm, valeur terminateur |
| `boot.S` | `.note.GNU-stack` | pile non exécutable |
| `panic.c` | `panic`, `__stack_chk_fail` | une seule sortie de secours |
| `serial.c` | `serial_putc`, `ATTENTE_MAX` | attente bornée |
| `verif.c` | `verif_canari`, `verif_ubsan` | preuves, pointeur `volatile` |
| `linker.ld` | `.note.gnu.build-id` | build-id dans sa section |

## Notes

Vérifié le 2026-09-29 avec i686-elf-gcc 15.3 et clang 23 : quatre tests
verts par toolchain, `grub2-file --is-x86-multiboot` OK, deux builds
release successifs au même sha256.
