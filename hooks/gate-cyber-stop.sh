#!/usr/bin/env bash
# Stop gate : avant de terminer le tour / livrer, le workspace
# ne doit pas contenir de motif baseline sécu.
# Fail-open s'il n'y a rien à scanner.
set -euo pipefail

payload="$(cat)"
reason="$(printf '%s' "$payload" | jq -r '.reason // empty' 2>/dev/null || true)"
cwd="$(printf '%s' "$payload" | jq -r '.cwd // empty' 2>/dev/null || true)"

if [ "$reason" != "end_turn" ]; then
	exit 0
fi

if [ -f "${AGENT_HOOKS_ROOT}/disable-norme-cybersecurite" ]; then
	exit 0
fi

if [ -z "$cwd" ] || [ ! -d "$cwd" ]; then
	exit 0
fi

case "$cwd" in
"$HOME/.claude"|"$HOME/.claude"/*)
	exit 0
	;;
esac

SCAN="${AGENT_HOOKS_ROOT}/cyber-scan.sh"
if [ ! -x "$SCAN" ]; then
	exit 0
fi

set +e
# Seulement les fichiers modifiés pendant le tour : un ancien motif du
# projet ne bloque pas chaque tour. Sans repère, tout le projet.
hits="$("$SCAN" --root "$cwd" --newer "${AGENT_HOOK_STATE}/turn-start" "$cwd" 2>/dev/null)"
status=$?
set -e

if [ "$status" -ne 0 ] && [ -n "$hits" ]; then
	jq -nc --arg reason "$hits" \
		'{decision:"block",reason:("Check sécu livraison KO. Corriger avant de livrer (skill norme-cybersecurite) :\n" + $reason)}'
	exit 0
fi

exit 0
