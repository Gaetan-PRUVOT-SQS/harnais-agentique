#!/usr/bin/env bash
# PostToolUse : après l'écriture d'un script shell, lancer shellcheck.
set -euo pipefail

payload="$(cat)"

if [ -f "${AGENT_HOOKS_ROOT}/disable-shellcheck" ]; then
	exit 0
fi

file="$(printf '%s' "$payload" | jq -r '.tool_input.file_path // empty' 2>/dev/null || true)"
if [ -z "$file" ] || [ ! -f "$file" ]; then
	exit 0
fi

if ! command -v shellcheck >/dev/null 2>&1; then
	jq -nc '{hookSpecificOutput:{hookEventName:"PostToolUse",additionalContext:"shellcheck absent : script shell non vérifié (installer le paquet shellcheck)."}}'
	exit 0
fi

set +e
out="$(cd "$(dirname "$file")" && shellcheck -S info -x -e SC1091 -f gcc -- "$(basename "$file")" 2>&1)"
status=$?
set -e

posix=""
case "$(head -n 1 -- "$file" 2>/dev/null || true)" in
'#!/bin/sh' | '#!/bin/sh '* | '#!/usr/bin/env sh' | '#!/usr/bin/env sh '* | '#!/bin/dash' | '#!/bin/dash '*)
	if command -v checkbashisms >/dev/null 2>&1; then
		posix="$(checkbashisms -p -- "$file" 2>&1 || true)"
	fi
	;;
esac

ctx=""
if [ "$status" -ne 0 ]; then
	ctx="$(printf 'SHELLCHECK KO. Corriger :\n%s' "$out")"
fi
if [ -n "$posix" ]; then
	ctx="${ctx:+$ctx$'\n\n'}$(printf 'POSIX KO (script #!/bin/sh). Corriger, ou passer en bash si le script en a besoin :\n%s' "$posix")"
fi
if [ -n "$ctx" ]; then
	jq -nc --arg ctx "$ctx" \
		'{hookSpecificOutput:{hookEventName:"PostToolUse",additionalContext:$ctx}}'
fi
exit 0
