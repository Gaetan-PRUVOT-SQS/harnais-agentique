# Feature : pratiques Unix, FreeBSD et Linux

Date : 2026-09-29

## Métier

- Besoin : L'auteur a demandé d'intégrer les meilleures pratiques d'Unix, de
  FreeBSD et de Linux au workflow, pour ses systèmes maison (sqscore,
  VelumOS) et pour l'hôte Fedora.
- Qui est concerné : L'auteur quand il conçoit un appel système, un format,
  un outil de base ou un sous-système du noyau ; l'agent qui explique,
  relit et écrit l'échafaudage.
- Impact si on ne le fait pas : on refait des erreurs déjà payées ailleurs
  (pid réutilisé, `time_t` 32 bits, drapeaux non vérifiés qu'on ne peut plus
  étendre, erreurs d'écriture perdues), et chaque correction casse l'ABI.

## Ce qu'on fait

- Nouveau skill `unix-freebsd-linux` : méthode (lire les deux manuels et ce
  que chacun a dû corriger), tradition Unix, conventions des outils, pages
  de manuel, conception des appels système et de l'ABI, descripteurs plutôt
  que noms globaux, moindre privilège, outils de débogage du noyau
  (tableau FreeBSD, Linux, chez nous), conception du noyau, système de
  base, durabilité des fichiers, façon de travailler, ce qu'on ne reprend
  pas.
- Exemple vérifié `exemples/` : lecture d'une structure extensible et
  refus des drapeaux inconnus (règles d'`adding-syscalls.rst`), testé
  sous ASan et UBSan avec gcc et clang ; page de manuel mdoc
  `ouvrir.2` vérifiée par `mandoc -T lint -W style`.
- Renvois courts dans les skills qui appliquent ces pratiques :
  processus-unix, fichiers-unix, noyau-conception, gestion-memoire,
  noyau-securite, os-confidentialite, libc-maison, integration-systeme,
  systeme-maison, pile-reseau, linux-serveur (bac à sable systemd,
  SELinux, firewalld, repères FreeBSD).
- Règle PERMANENTE dans AGENTS.md ; paquet `mandoc` installé sur le poste.
- Faits vérifiés le 2026-09-29 sur man.freebsd.org, docs.freebsd.org,
  docs.kernel.org, man7.org, les pages installées et POSIX.1-2024
  (pubs.opengroup.org/onlinepubs/9799919799). Nuances retenues : erreurs
  Capsicum (`ECAPMODE` pour un nom global, `ENOTCAPABLE` pour une sortie
  d'arbre), code 1 pour tout échec chez FreeBSD et `sysexits` déconseillé,
  i386 retiré de FreeBSD 15.0, `time_t` 64 bits exigé par POSIX.1-2024,
  exemple `perf_event_open` dans `adding-syscalls.rst`, rapport `errseq_t`
  par fichier ouvert.

## Choix techniques

| Choix | Pourquoi | Alternative rejetée | Impact métier |
|-------|----------|---------------------|---------------|
| Un skill carrefour plus des renvois courts | la question « comment FreeBSD et Linux font » traverse tous les sous-systèmes ; le détail d'un sous-système reste dans son skill | tout éparpiller dans les skills existants | une seule entrée à charger, pas de doublon long |
| Idées tirées des manuels, docs et livres, jamais du code | clean room (systeme-maison), licences BSD et GPL | lire le code de FreeBSD ou Linux | aucune dette de licence |
| Conventions du projet à la place de style(9) et du coding-style | formateur, linter et conventions du projet (règle de AGENTS.md) | adopter le style d'un des deux | un seul style dans tout le C |
| Structure extensible avec sa taille | les appels du gabarit n'ont que 4 paramètres, le gabarit Unix-like prévoyait déjà une structure pour les appels plus riches | multiplier les appels | l'ABI grandit sans casser les applis |
| Types 64 bits dès le départ | FreeBSD (ino64) et Linux (time64) ont dû migrer en cassant ou en doublant l'ABI | tailles natives i686 | pas de migration d'ABI plus tard |
| Capsicum comme modèle de privilège | un droit égale un descripteur, colle au « Private by default » de VelumOS | uid et setuid classiques | bac à sable simple à prouver par test |
| `mandoc` installé | vérifier les pages mdoc sur l'hôte | ne pas vérifier | pages de manuel propres dès le départ |

## Traçabilité

| Fichier | Bloc | Justifié par |
|---------|------|--------------|
| `SKILL.md` | tout | skill carrefour |
| `exemples/abi_extensible.c` | `drapeaux_valides`, `copier_struct_user`, `lire_ouvrir` | structure extensible |
| `exemples/test_abi_extensible.c`, `exemples/Makefile` | cas de taille, de drapeaux, hors espace user | structure extensible |
| `exemples/ouvrir.2` | page mdoc | `mandoc` installé |
