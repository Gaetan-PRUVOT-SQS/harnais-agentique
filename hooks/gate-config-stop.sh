#!/usr/bin/env bash
set -euo pipefail

verifier="${AGENT_CONFIG_ROOT:?}/verifier"
if [ ! -x "$verifier" ] || [ -f "${AGENT_HOOKS_ROOT:?}/disable-config" ]; then
	exit 0
fi

payload="$(cat)"
changes=()
while IFS= read -r ligne; do
	[ -n "$ligne" ] && changes+=("$ligne")
done < <(printf '%s' "$payload" | jq -r '.config_changes[]? // empty' 2>/dev/null || true)

set +e
if [ "${#changes[@]}" -gt 0 ]; then
	out="$("$verifier" --rapide --pour "${changes[@]}" 2>&1)"
else
	out="$("$verifier" --rapide 2>&1)"
fi
status=$?
set -e

if [ "$status" -ne 0 ]; then
	short="$(printf '%s\n' "$out" | grep -v '^OK ' | tail -n 40)"
	jq -nc --arg reason "$short" \
		'{decision:"block",reason:("Config ~/.agents : verifier --rapide KO. Corriger avant de rendre la main :\n" + $reason)}'
fi
