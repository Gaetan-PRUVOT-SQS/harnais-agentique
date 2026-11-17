#!/usr/bin/env bash
# Adaptation locale : pas de parcours du home. Apache-2.0, LICENSE.
set -euo pipefail
shopt -s inherit_errexit

nom=${0##*/}

if [[ -n ${GHIDRA_HOME:-} ]]; then
	tete=$GHIDRA_HOME/support/analyzeHeadless
	if [[ -x $tete ]]; then
		printf '%s\n' "$tete"
		exit 0
	fi
	printf '%s: GHIDRA_HOME sans analyzeHeadless: %s\n' "$nom" "$GHIDRA_HOME" >&2
	exit 1
fi

bases=(
	/opt/homebrew/Caskroom/ghidra
	/usr/local/Caskroom/ghidra
	/opt/ghidra
	/usr/local/ghidra
	"$HOME/.local/opt/ghidra"
	"$HOME/ghidra"
	"$HOME/Applications/ghidra"
	/Applications/ghidra
	/usr/share/ghidra
	/usr/local/share/ghidra
)

for base in "${bases[@]}"; do
	[[ -d $base ]] || continue
	lien=$base/current/support/analyzeHeadless
	if [[ -x $lien ]]; then
		printf '%s\n' "$lien"
		exit 0
	fi
	tete=$(find "$base" -name analyzeHeadless -type f -print -quit)
	if [[ -n $tete && -x $tete ]]; then
		printf '%s\n' "$tete"
		exit 0
	fi
done

printf '%s: analyzeHeadless introuvable. Renseigner GHIDRA_HOME.\n' "$nom" >&2
exit 1
