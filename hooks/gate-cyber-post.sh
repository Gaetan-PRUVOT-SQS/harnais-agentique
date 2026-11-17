#!/usr/bin/env bash
# PostToolUse : après une écriture, signaler les motifs baseline sécu.
# Fail-soft : ne bloque pas l outil.
set -euo pipefail

payload="$(cat)"

if [ -f "${AGENT_HOOKS_ROOT}/disable-norme-cybersecurite" ]; then
	exit 0
fi

file="$(printf '%s' "$payload" | jq -r '
	.toolInput.file_path
	// .toolInput.filePath
	// .toolInput.path
	// .toolInput.target_file
	// .tool_input.file_path
	// .tool_input.filePath
	// .tool_input.path
	// .tool_input.target_file
	// empty
' 2>/dev/null || true)"

if [ -z "$file" ] || [ ! -f "$file" ]; then
	exit 0
fi

case "$file" in
"${AGENT_HOOKS_ROOT}"/*|"${AGENT_SKILLS_ROOT}"/*)
	exit 0
	;;
esac

SCAN="${AGENT_HOOKS_ROOT}/cyber-scan.sh"
if [ ! -x "$SCAN" ]; then
	exit 0
fi

set +e
cwd="$(printf '%s' "$payload" | jq -r '.cwd // empty' 2>/dev/null || true)"
root="$(dirname "$file")"
if [ -n "$cwd" ] && [ -d "$cwd" ]; then
	root="$cwd"
fi
hits="$("$SCAN" --root "$root" "$file" 2>/dev/null)"
set -e

if [ -n "$hits" ]; then
	jq -nc --arg ctx "$hits" \
		'{hookSpecificOutput:{hookEventName:"PostToolUse",additionalContext:("CYBER AUTO KO. Corriger dans ce tour (skill norme-cybersecurite) :\n" + $ctx)}}'
	exit 0
fi

exit 0
