#!/usr/bin/env bash
# Stop gate : secrets du projet (gitleaks dir sur l'arbre de travail, sans git).
# Fail-open dit : gitleaks absent = annoncé, jamais une validation muette.
set -euo pipefail

payload="$(cat)"
reason="$(printf '%s' "$payload" | jq -r '.reason // empty' 2>/dev/null || true)"
cwd="$(printf '%s' "$payload" | jq -r '.cwd // empty' 2>/dev/null || true)"

if [ "$reason" != "end_turn" ]; then
	exit 0
fi
if [ -z "$cwd" ] || [ ! -d "$cwd" ]; then
	exit 0
fi

if ! command -v gitleaks >/dev/null 2>&1; then
	jq -nc --arg ctx "gitleaks absent : scan de secrets du projet non lancé, ne pas annoncer de validation." \
		'{hookSpecificOutput:{hookEventName:"Stop",additionalContext:$ctx}}'
	exit 0
fi

if out="$(gitleaks dir --no-banner --redact --exit-code 2 "$cwd" 2>&1)"; then
	exit 0
fi

jq -nc --arg reason "SECRETS KO (gitleaks) : corriger avant de clore le tour.
$(printf '%s' "$out" | tail -n 12)" '{decision:"block",reason:$reason}'
