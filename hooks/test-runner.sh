#!/usr/bin/env bash
# Lance les tests du projet courant, directement dans le projet.
# Usage : run-tests.sh [--dir CHEMIN]
set -euo pipefail

racine="$(pwd)"
while [ $# -gt 0 ]; do
  case "$1" in
    --all) shift ;;  # ancienne option, sans effet
    --dir) racine="$2" ; shift 2 ;;
    *) echo "option inconnue : $1" >&2 ; exit 2 ;;
  esac
done

cd "$racine"

if [ -f package.json ]; then
  # Le script de npm init ("no test specified") ne compte pas comme une suite.
  script="$(jq -r '.scripts.test // empty' package.json 2>/dev/null || true)"
  if [ -n "$script" ] && ! printf '%s' "$script" | grep -q 'no test specified'; then
    if [ ! -d node_modules ]; then
      echo "tests non lancés : node_modules absent (npm install)"
      exit 3
    fi
    if ! command -v npm >/dev/null 2>&1; then
      echo "tests non lancés : npm introuvable dans le PATH"
      exit 3
    fi
    npm test
    exit $?
  fi
fi

if [ -f manage.py ]; then
  python=python3
  for f in .venv/bin/python venv/bin/python; do
    if [ -x "$f" ]; then
      python="$f"
      break
    fi
  done
  set +e
  sortie="$("$python" manage.py test 2>&1)"
  code=$?
  set -e
  printf '%s\n' "$sortie"
  # Bases arrêtées par défaut sur ce poste : ce n'est pas une régression.
  if [ "$code" -ne 0 ] && printf '%s' "$sortie" \
    | grep -qiE 'connection refused|could not connect to server|Is the server running|No such file or directory.*PGSQL|Can.t connect to (local )?(MySQL )?server|ServerSelectionTimeout'; then
    echo "tests non lancés : base de données arrêtée"
    exit 3
  fi
  exit "$code"
fi

if [ -f composer.json ]; then
  if [ -n "$(jq -r '.scripts.test // empty' composer.json 2>/dev/null || true)" ]; then
    composer test
    exit $?
  fi
  if [ -x vendor/bin/phpunit ]; then
    vendor/bin/phpunit
    exit $?
  fi
fi

if [ -f pyproject.toml ] || [ -f pytest.ini ] || [ -f setup.cfg ]; then
  # Le pytest du venv du projet voit ses dépendances, pas le pytest global.
  lanceur=()
  for f in .venv/bin/python venv/bin/python; do
    if [ -x "$f" ]; then
      if ! "$f" -c 'import pytest' >/dev/null 2>&1; then
        echo "tests non lancés : pytest absent du venv ($f -m pip install pytest)"
        exit 3
      fi
      lanceur=("$f" -m pytest)
      break
    fi
  done
  if [ "${#lanceur[@]}" -eq 0 ] && command -v pytest >/dev/null 2>&1; then
    lanceur=(pytest)
  fi
  if [ "${#lanceur[@]}" -gt 0 ]; then
    set +e
    "${lanceur[@]}"
    code=$?
    set -e
    # Code 5 : aucun test collecté.
    if [ "$code" -eq 5 ]; then
      echo "tests non collectés : pytest n'a trouvé aucun test" >&2
      exit 1
    fi
    exit "$code"
  fi
fi

if [ -f Cargo.toml ]; then
  cargo test --offline
  exit $?
fi

if [ -f go.mod ]; then
  go test ./...
  exit $?
fi

if [ -f CMakeLists.txt ]; then
  for b in build cmake-build-debug out/build; do
    if [ -f "$b/CTestTestfile.cmake" ]; then
      ctest --test-dir "$b" --output-on-failure
      exit $?
    fi
  done
  echo "tests non lancés : build CMake absent (cmake -S . -B build)"
  exit 3
fi

# Projet C (noyau, bas niveau) : cible `test-rapide` si le projet
# en a une (suite complète trop longue pour la fin de tour), sinon `test`.
for f in GNUmakefile makefile Makefile; do
  if [ -f "$f" ] && grep -qE '^test-rapide[[:space:]]*:' "$f"; then
    make -f "$f" test-rapide
    exit $?
  fi
  if [ -f "$f" ] && grep -qE '^test[[:space:]]*:' "$f"; then
    make -f "$f" test
    exit $?
  fi
  if [ -f "$f" ] && grep -qE '^check[[:space:]]*:' "$f"; then
    make -f "$f" check
    exit $?
  fi
done

echo "aucun lanceur de tests reconnu dans $racine" >&2
exit 1
