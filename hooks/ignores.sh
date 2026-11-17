#!/usr/bin/env bash
# A sourcer. Dossiers jamais parcourus par les hooks (dépendances, builds,
# caches, config des agents). dispatch.py lit aussi cette liste.
IGNORES="node_modules .git .venv venv dist build out target coverage vendor
third_party Pods DerivedData .gradle .idea .next .nuxt .turbo .cache
__pycache__ .mypy_cache .pytest_cache .subjects debian-root sysroot
site-packages .tox .nox bower_components .svelte-kit .angular .parcel-cache
.dart_tool .expo .terraform .agents .claude"

# Remplit le tableau PRUNE pour find : \( -name a -o -name b ... \) -prune
prune_args()
{
	local n
	local first=1
	PRUNE=( \( )
	for n in $IGNORES; do
		if [ "$first" -eq 0 ]; then
			PRUNE+=( -o )
		fi
		PRUNE+=( -name "$n" )
		first=0
	done
	PRUNE+=( \) -prune )
}
