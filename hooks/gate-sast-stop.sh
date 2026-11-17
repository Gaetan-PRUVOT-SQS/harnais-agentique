#!/usr/bin/env bash
# Stop gate : SAST du projet (semgrep, règles p/python et p/owasp-top-ten,
# alertes ERROR seulement). Fail-open dit : semgrep absent = annoncé.
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

if ! command -v semgrep >/dev/null 2>&1; then
	jq -nc --arg ctx "semgrep absent : SAST du projet non lancé, ne pas annoncer de validation." \
		'{hookSpecificOutput:{hookEventName:"Stop",additionalContext:$ctx}}'
	exit 0
fi

# Règles web/python : un projet sans fichier de ce type n'a rien à scanner.
if ! find "$cwd" -type f \( -name '*.py' -o -name '*.js' -o -name '*.jsx' \
	-o -name '*.ts' -o -name '*.tsx' -o -name '*.php' -o -name '*.java' \
	-o -name '*.go' -o -name '*.rb' \) -print -quit 2>/dev/null | grep -q .; then
	exit 0
fi

if out="$(semgrep scan --metrics=off --disable-version-check --quiet --error \
	--severity ERROR --max-target-bytes 1000000 \
	--config p/python --config p/owasp-top-ten "$cwd" 2>&1)"; then
	exit 0
fi

jq -nc --arg reason "SAST KO (semgrep) : corriger avant de clore le tour.
$(printf '%s' "$out" | tail -n 15)" '{decision:"block",reason:$reason}'
