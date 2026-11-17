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

if [ -z "$cwd" ] || [ ! -d "$cwd" ]; then
	exit 0
fi

case "$cwd" in
"$HOME/.claude" | "$HOME/.claude"/*)
	exit 0
	;;
esac

SCRIPT="$AGENT_HOOKS_ROOT/run-tests.sh"
if [ ! -x "$SCRIPT" ]; then
	exit 0
fi

set +e
out="$("$SCRIPT" --dir "$cwd" 2>&1)"
status=$?
set -e

if printf '%s' "$out" | grep -q 'aucun lanceur de tests reconnu dans '; then
	stamp="${AGENT_HOOK_STATE}/turn-start"
	if [ -f "$stamp" ]; then
		recent="$(python3 -E -s "$AGENT_HOOKS_ROOT/oracle_vide.py" --code-recent --dir "$cwd" --depuis "$stamp")"
		if [ -n "$recent" ]; then
			message="Pas de lanceur de tests alors que du code a changé. Ne pas annoncer de tests OK."
			jq -nc --arg message "$message" --arg texte "$recent" \
				'{decision:"block",reason:($message + "\n" + $texte)}'
		fi
	fi
	exit 0
fi

# 127 : outil ou dépendance absente, pas une régression.
if [ "$status" -eq 127 ]; then
	manque="$(printf '%s\n' "$out" | grep -iE 'not found|introuvable' | tail -n 1)"
	out="$out
tests non lancés : commande introuvable (${manque:-code 127})"
	status=3
fi

# Tests impossibles à lancer (dépendances, base arrêtée) : le signaler une
# fois par session, sans le compter comme une régression.
if [ "$status" -eq 3 ] && printf '%s' "$out" | grep -q 'tests non lancés'; then
	flag="${AGENT_HOOK_STATE}/tests-non-lances"
	if [ -f "$flag" ]; then
		exit 0
	fi
	touch "$flag"
	msg="$(printf '%s\n' "$out" | grep 'tests non lancés' | tail -n 1)"
	jq -nc --arg reason "$msg" \
		'{decision:"block",reason:("Régression non vérifiée, " + $reason + ". Le signaler, ne pas annoncer de tests OK.")}'
	exit 0
fi

if [ "$status" -ne 0 ]; then
	# Truncate pour le hook.
	short="$(printf '%s\n' "$out" | tail -n 40)"
	jq -nc --arg reason "$short" \
		'{decision:"block",reason:("Régression auto KO. Corriger le code puis relancer (skill tests-regression-auto) :\n" + $reason)}'
	exit 0
fi

# Le scan sécu de fin de tour est fait par gate-cyber-stop.
exit 0
