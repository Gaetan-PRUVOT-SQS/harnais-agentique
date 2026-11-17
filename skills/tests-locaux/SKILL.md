---
name: tests-locaux
description: >-
  Use for l'auteur whenever running, verifying or claiming tests or trying code (npm test, pytest, make test...). Everything happens in the project: no sandbox, /tmp, scratchpad or temp file.
---

# Tests locaux, directement dans le projet

## Décisions de l'auteur

- 27/09/2026 : plus de copie du projet dans `/tmp` pour les tests (trop lent,
  quota disque rempli).
- 29/09/2026 : plus de dev en sandbox ni en fichier temporaire. Écrire,
  essayer et tester se fait dans le projet.

## Commande

```bash
~/.agents/hooks/run-tests.sh          # lance la suite du projet courant
# option  : --dir P (autre racine de projet)
```

## Où va quoi

- Un essai (comportement d'un outil, d'une option, d'une règle de la spec)
  devient un fichier du projet : test, exemple, cas de la suite. Sinon il
  n'existe pas.
- Sorties de build, de test, logs QEMU ou rapports d'analyse : dans le
  dossier de build du projet (`build/`, `obj/`...), ignoré par git.
- Fixtures d'un test : fichiers du projet (`tests/fixtures/`), pas de
  `mkdtemp` ni de `tempfile` vers `/tmp`.
- Environnement et données de test reproductibles (ISO 29119-2) : versions
  épinglées, graine affichée pour tout aléa, horloge et fuseau fixés
  quand le résultat en dépend.
- Le `check` C compile vers `/dev/null` et pose son binaire de test à côté
  du fichier, supprimé aussitôt.

## Règles gardées

1. Lire la sortie fraîche de la commande avant d'annoncer un résultat, et citer ce qu'elle dit (nombre de tests, échecs).
2. Tests de perf ou qui parcourent `$HOME` : seulement si l'auteur le demande. Le lanceur ne les filtre pas : les exclure par la config du projet (marqueur pytest, `--exclude` de Vitest...).
3. UI : aucun clic Nettoyer / Corbeille / supprimer.
4. Pas de CI pour « vérifier » : les tests se lancent ici.

## Interdit

- Copier le projet, créer un `TMPDIR`, un `mktemp` ou un dossier du scratchpad pour écrire, essayer ou tester du code
- Écrire un fichier d'essai jetable hors du projet
- Affirmer PASS sans sortie de cette session
