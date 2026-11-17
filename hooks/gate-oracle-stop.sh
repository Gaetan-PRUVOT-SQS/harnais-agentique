#!/usr/bin/env bash
set -euo pipefail
shopt -s inherit_errexit

payload="$(cat)"
reason="$(printf '%s' "$payload" | jq -r '.reason // empty' 2>/dev/null || true)"
cwd="$(printf '%s' "$payload" | jq -r '.cwd // empty' 2>/dev/null || true)"

if [ "$reason" != "end_turn" ]; then
	exit 0
fi

if [ -f "${AGENT_HOOKS_ROOT}/disable-tests-regression-auto" ] ||
	[ -f "${AGENT_HOOKS_ROOT}/disable-tests-locaux" ]; then
	exit 0
fi

stamp="${AGENT_HOOK_STATE}/turn-start"
if [ ! -f "$stamp" ] || [ -z "$cwd" ] || [ ! -d "$cwd" ]; then
	exit 0
fi

texte="$(python3 -E -s "$AGENT_HOOKS_ROOT/oracle_vide.py" --dir "$cwd" --depuis "$stamp")"
if [ -z "$texte" ]; then
	exit 0
fi

message="Oracle vide ou trop faible. Affirmer la valeur attendue."
jq -nc --arg message "$message" --arg texte "$texte" \
	'{decision:"block",reason:($message + "\n" + $texte)}'
