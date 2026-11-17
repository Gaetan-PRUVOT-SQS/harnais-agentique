# Feature : licences-tierces, prouver qu'on ne dépend d'aucune licence tierce

Date : 2026-09-29

## Métier

- Besoin : L'auteur veut un système à lui, sans dépendre de licences tierces.
  Pour le prouver, il faut savoir à tout moment quel code du projet n'est
  pas de lui, sous quelle licence, et repérer une copie qui serait entrée
  sans être déclarée.
- Qui est concerné : L'auteur avant chaque livraison, l'agent quand il ajoute
  ou porte du code.
- Impact si on ne le fait pas : un fichier copié (Linux, KolibriOS, un
  tuto) impose sa licence en silence ; notice manquante à la publication ;
  promesse « tout maison » fausse sans que personne le sache.

## Ce qu'on fait

- Comportement visible : `licences-tierces --licence-projet LICENCE
  [--autorisees A,B] [--dir D]` lance `reuse lint`, affiche le code maison
  et le code tiers groupé par licence, puis cherche des textes de licence
  dans les sources déclarées maison. Code 1 si le projet n'est pas conforme
  REUSE, si une licence tierce n'est pas autorisée, ou si une copie non
  déclarée est soupçonnée. Sans `--autorisees`, tout code tiers fait
  échouer : c'est l'objectif « aucune dépendance ».
- Fichiers touchés : `scripts/licences_tierces.py`,
  `scripts/test_licences_tierces.py`, `scripts/pyproject.toml`,
  `scripts/fixtures/copie-non-declaree/`, `exemples/projet-reuse/`, lien
  `~/.local/bin/licences-tierces`.

## Choix techniques

| Choix | Pourquoi | Alternative rejetée | Impact métier |
|-------|----------|---------------------|---------------|
| REUSE et `REUSE.toml` | standard ouvert, outil existant, licences déclarées sans commentaire dans chaque fichier | en-têtes SPDX dans chaque fichier | compatible avec la règle « pas de commentaires » |
| S'appuyer sur `reuse lint --json` | pas de réécriture de l'analyse SPDX | parser REUSE.toml soi-même | moins de code, même résultat que l'outil de référence |
| Recherche de textes de licence dans le code maison | `reuse` considère comme maison un fichier copié sans balise SPDX (vérifié sur la fixture) | faire confiance à `reuse` seul | une copie non déclarée est trouvée avant publication |
| Recherche limitée aux sources (C, asm, scripts, linker, Makefile) | un README qui parle de la GPL n'est pas une copie | tous les fichiers | pas de faux positif sur la doc et les textes de `LICENSES/` |
| Aucune licence tierce autorisée par défaut | l'objectif est l'indépendance ; une exception se déclare avec `--autorisees` | tout autoriser | chaque dépendance est un choix écrit |
| Logique pure (`classer`, `marqueurs_trouves`) testée avec pytest, `reuse` appelé seulement à la frontière | tests rapides, sans réseau | tester seulement le script entier | régressions visibles en 0,1 s |

## Traçabilité

| Fichier | Fonction / bloc | Justifié par |
|---------|-----------------|--------------|
| `scripts/licences_tierces.py` | `lire_reuse` | s'appuyer sur `reuse lint --json` |
| `scripts/licences_tierces.py` | `classer` | aucune licence tierce autorisée par défaut |
| `scripts/licences_tierces.py` | `marqueurs_trouves`, `SOURCES`, `MARQUEURS` | recherche de textes de licence, limitée aux sources |
| `scripts/licences_tierces.py` | `main` | codes de sortie |
| `scripts/test_licences_tierces.py` | tous | logique pure testée, fixtures |
| `exemples/projet-reuse/REUSE.toml` | annotations | REUSE et REUSE.toml |
