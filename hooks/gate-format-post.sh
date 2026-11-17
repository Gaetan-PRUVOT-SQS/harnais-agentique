#!/usr/bin/env bash
# PostToolUse : après l'écriture d'un fichier, le formateur du projet le
# remet en forme. Le C n'est pas touché.
set -euo pipefail

payload="$(cat)"

if [ -f "${AGENT_HOOKS_ROOT}/disable-format" ]; then
	exit 0
fi

file="$(printf '%s' "$payload" | jq -r '.tool_input.file_path // empty' 2>/dev/null || true)"
racine="$(printf '%s' "$payload" | jq -r '.cwd // empty' 2>/dev/null || true)"
if [ -z "$file" ] || [ ! -f "$file" ] || [ -z "$racine" ] || [ ! -d "$racine" ]; then
	exit 0
fi

script_shell()
{
	head -n 1 -- "$1" 2>/dev/null |
		grep -Eq '^#![[:space:]]*(/usr)?/bin/(env[[:space:]]+)?(ba|da|k)?sh([[:space:]]|$)'
}

config_ruff()
{
	[ -f "$racine/ruff.toml" ] || [ -f "$racine/.ruff.toml" ] ||
		{
			[ -f "$racine/pyproject.toml" ] && grep -q '^\[tool\.ruff' "$racine/pyproject.toml"
		}
}

config_prettier()
{
	local f
	for f in "$racine"/.prettierrc "$racine"/.prettierrc.* "$racine"/prettier.config.*; do
		[ -e "$f" ] && return 0
	done
	[ -f "$racine/package.json" ] && jq -e '.prettier' "$racine/package.json" >/dev/null 2>&1
}

formateur=""
case "$(basename -- "$file")" in
*.c | *.h | Makefile | makefile | GNUmakefile) exit 0 ;;
*.sh | *.bash) formateur=shfmt ;;
*.py | *.pyi) config_ruff && formateur=ruff ;;
*.js | *.jsx | *.mjs | *.cjs | *.ts | *.tsx | *.mts | *.cts | *.json | *.css | *.scss | *.html | *.vue | *.md | *.yaml | *.yml)
	config_prettier && formateur=prettier
	;;
*.*) exit 0 ;;
*) script_shell "$file" && formateur=shfmt ;;
esac
if [ -z "$formateur" ]; then
	exit 0
fi

empreinte()
{
	sha256sum -- "$file" | cut -d ' ' -f 1
}

avant="$(empreinte)"
set +e
case "$formateur" in
shfmt)
	if ! command -v shfmt >/dev/null 2>&1; then
		exit 0
	fi
	# Sans drapeau, shfmt suit le .editorconfig du projet.
	if [ -f "$racine/.editorconfig" ]; then
		out="$(shfmt -w -- "$file" 2>&1)"
	else
		out="$(shfmt -fn -w -- "$file" 2>&1)"
	fi
	;;
ruff)
	if ! command -v ruff >/dev/null 2>&1; then
		exit 0
	fi
	out="$(cd "$racine" && ruff format --quiet -- "$file" 2>&1)"
	;;
prettier)
	binaire="$racine/node_modules/.bin/prettier"
	if [ ! -x "$binaire" ]; then
		binaire="$(command -v prettier 2>/dev/null || true)"
	fi
	if [ -z "$binaire" ]; then
		exit 0
	fi
	out="$(cd "$racine" && "$binaire" --write --ignore-unknown --log-level warn -- "$file" 2>&1)"
	;;
esac
status=$?
set -e

if [ "$status" -ne 0 ]; then
	jq -nc --arg ctx "$(printf 'FORMATAGE KO (%s) : corriger le fichier.\n%s' "$formateur" "$(printf '%s\n' "$out" | tail -n 15)")" \
		'{hookSpecificOutput:{hookEventName:"PostToolUse",additionalContext:$ctx}}'
	exit 0
fi

if [ "$(empreinte)" != "$avant" ]; then
	jq -nc --arg ctx "Fichier reformaté par $formateur : $file. Il a changé sur le disque, le relire avant une nouvelle édition." \
		'{hookSpecificOutput:{hookEventName:"PostToolUse",additionalContext:$ctx}}'
fi
exit 0
