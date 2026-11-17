# Feature : POSIX.1-2024 en dev shell et OS

Date : 2026-09-29

## Métier

- Besoin : L'auteur a demandé d'intégrer les meilleures pratiques de la
  norme POSIX, puis de la vérifier sur le dev shell et l'OS.
- Qui est concerné : les scripts `#!/bin/sh` du workflow et des projets,
  le shell maison, la libc et le noyau de type Unix (gabarit, sqscore).
- Impact si on ne le fait pas : scripts qui cassent hors de bash, libc aux
  signatures inventées, écritures partielles perdues, appels retirés de
  la norme réimplémentés, et des règles tirées de la mémoire au lieu du
  texte d'Issue 8.

## Ce qu'on fait

- Skill `posix` : lecture de la norme, conformité et macros, règles de C
  système, shell et utilitaires (nouveautés 2024 et ce qui reste hors
  POSIX), make, POSIX comme spec de son shell et de son OS.
- Outil `verifier-posix` (`scripts/verifier_posix.py`, lié dans
  `~/.local/bin`) : noms d'erreurs et prototypes d'une libc maison face à
  POSIX.1-2024 ; référence de 78 noms et 120 prototypes, dont 118
  confirmés par un test contre la glibc 2.43 ; 11 tests pytest, ruff,
  mypy strict.
- Gabarit Unix-like mis en conformité : types POSIX générés
  (`abi/types.liste`, `outils/genere-types`), `ssize_t write`,
  `pid_t getpid`, cible `make posix` dans `make test` (vert, 0 écart).
- Hook : `checkbashisms -p` sur tout `#!/bin/sh` écrit (`POSIX KO`),
  test ajouté à verify.py.
- Exemple `exemples/` : `ecrire_tout` (écritures partielles, `EINTR`,
  `SSIZE_MAX`), test scripté et test sur vrai tube interrompu par un
  timer POSIX ; `pipefail.sh` vérifié sous dash et `bash --posix`.
- `compare-shells` : deux cas de 2024 (`pipefail`, `$'...'`).
- Renvois dans scripts-shell, shell-maison, terminal-unix (termios sans
  `ioctl`), processus-unix, libc-maison, fichiers-unix,
  unix-freebsd-linux ; règles PERMANENTES dans AGENTS.md.
- Faits vérifiés le 2026-09-29 sur pubs.opengroup.org/onlinepubs/9799919799
  (pages lues en entier par curl quand l'outil web tronquait), le git de
  dash et `features.h` de la glibc.

## Choix techniques

| Choix | Pourquoi | Alternative rejetée | Impact métier |
|-------|----------|---------------------|---------------|
| Types POSIX générés dans `build/` | une seule liste (`abi/types.liste`) fixe les tailles pour la libc et le noyau ; les prototypes gardent les vrais noms | types écrits à la main dans chaque en-tête, ou `long` à la place de `ssize_t` | libc conforme aux signatures POSIX, sans types dupliqués |
| Référence de prototypes en TSV, validée contre la glibc | la glibc suit POSIX pour ces fonctions ; `__builtin_types_compatible_p` prouve chaque ligne | recopier les pages à la main sans contrôle | une ligne fausse fait échouer le test |
| Comparaison sur les types, pas le texte | noms de paramètres, `restrict` et attributs ne changent pas la compatibilité | comparaison textuelle | pas de faux écart sur un nom de paramètre |
| `checkbashisms -p` dans le hook | shellcheck laisse passer `kill -SIGTERM`, `type` ; le mode `-p` retire les tolérances Debian (`local`, `echo -n`) | shellcheck seul | contrôle POSIX automatique à chaque écriture |
| Idiome `pipefail` testé, directive SC3040 | `pipefail` est POSIX depuis 2024 mais shellcheck 0.11 l'ignore | bannir `pipefail` en sh | erreurs des tuyaux visibles en sh aussi |
| Test sur vrai tube avec timer POSIX | l'interruption d'un vrai `write` prouve la boucle, pas seulement un faux | faux `write` seul | on sait que le code tient face au noyau |

## Traçabilité

| Fichier | Bloc | Justifié par |
|---------|------|--------------|
| `scripts/verifier_posix.py` | `verifier_errno`, `verifier_entetes`, `normaliser_parametre`, `canoniser` | comparaison sur les types |
| `scripts/reference/*` | 78 noms, 120 prototypes | référence validée contre la glibc |
| `scripts/test_verifier_posix.py` | `test_reference_conforme_a_la_glibc` | référence validée contre la glibc |
| `exemples/ecrire_tout.c` | `ecrire_tout_avec` | test sur vrai tube |
| `exemples/test_tube.c`, `exemples/tube_lecteur.c` | minuterie, lecteur lent | test sur vrai tube |
| `exemples/pipefail.sh` | idiome | idiome `pipefail` |
| `~/.agents/hooks/gate-shell-post.sh` | `checkbashisms -p` | `checkbashisms -p` dans le hook |
| `systeme-maison/templates/unix-like-i686/outils/genere-types` | `sys/types.h` | types POSIX générés |
