#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
	cd "$BATS_TEST_DIRNAME/.." || exit 1
	cas=$PWD/build/cas-$BATS_TEST_NUMBER
	rm -rf "$cas"
	mkdir -p "$cas/ghidra/support" "$cas/sortie"
	JOURNAL=$cas/journal
	export JOURNAL
	cat >"$cas/ghidra/support/analyzeHeadless" <<'EOF'
#!/usr/bin/env bash
printf '%s\0' "$@" >"${JOURNAL:?}"
exit 0
EOF
	chmod +x "$cas/ghidra/support/analyzeHeadless"
	export GHIDRA_HOME=$cas/ghidra
}

teardown() {
	rm -rf "$cas"
	unset JOURNAL GHIDRA_HOME
}

@test "sans argument : usage et code 2" {
	run ./scripts/ghidra-analyze.sh
	[ "$status" -eq 2 ]
	[[ "$output" == *"binaire manquant"* ]]
}

@test "aide : code 0 et projet sous la sortie" {
	run ./scripts/ghidra-analyze.sh --help
	[ "$status" -eq 0 ]
	[[ "$output" == *"ghidra-project"* ]]
	[[ "$output" != *"/tmp"* ]]
}

@test "fichier absent : code 1" {
	run ./scripts/ghidra-analyze.sh -o "$cas/sortie" -- "$cas/nom avec espaces.bin"
	[ "$status" -eq 1 ]
	[[ "$output" == *"nom avec espaces.bin"* ]]
	[ ! -e "$JOURNAL" ]
}

@test "timeout invalide : code 2" {
	printf 'x' >"$cas/echantillon.bin"
	run ./scripts/ghidra-analyze.sh --timeout abc -o "$cas/sortie" "$cas/echantillon.bin"
	[ "$status" -eq 2 ]
	[[ "$output" == *"timeout invalide"* ]]
	[ ! -e "$JOURNAL" ]
}

@test "sortie sous /tmp refusee, rien n'est cree" {
	printf 'x' >"$cas/echantillon.bin"
	refuse=/tmp/ghidra-skill-refus-test
	rm -rf "$refuse"
	run ./scripts/ghidra-analyze.sh -o "$refuse" "$cas/echantillon.bin"
	[ "$status" -eq 2 ]
	[[ "$output" == *"chemin refuse"* ]]
	[ ! -e "$refuse" ]
}

@test "projet par defaut, etoile litterale, nom a espaces" {
	printf 'x' >"$cas/nom avec espaces.bin"
	run ./scripts/ghidra-analyze.sh -o "$cas/sortie" -s ExportStrings.java -a '*' -- "$cas/nom avec espaces.bin"
	[ "$status" -eq 0 ]
	mapfile -d '' args <"$JOURNAL"
	[ "${args[0]}" = "$cas/sortie/ghidra-project" ]
	import_at=-1
	star=0
	supprime=0
	for i in "${!args[@]}"; do
		if [[ ${args[$i]} == -import ]]; then
			import_at=$i
		fi
		if [[ ${args[$i]} == '*' ]]; then
			star=1
		fi
		if [[ ${args[$i]} == -deleteProject ]]; then
			supprime=1
		fi
		[[ ${args[$i]} != /tmp && ${args[$i]} != /tmp/* && ${args[$i]} != /var/tmp && ${args[$i]} != /var/tmp/* ]]
	done
	[ "$import_at" -ge 0 ]
	[ "${args[$((import_at + 1))]}" = "$cas/nom avec espaces.bin" ]
	[ "$star" -eq 1 ]
	[ "$supprime" -eq 1 ]
}

@test "arguments de script vides ou avec separateur" {
	printf 'x' >"$cas/echantillon.bin"
	run ./scripts/ghidra-analyze.sh -o "$cas/sortie" -s ExportStrings.java -a '' -a $'a\x1fb' "$cas/echantillon.bin"
	[ "$status" -eq 0 ]
	mapfile -d '' args <"$JOURNAL"
	post=-1
	for i in "${!args[@]}"; do
		if [[ ${args[$i]} == -postScript ]]; then
			post=$i
		fi
	done
	[ "$post" -ge 0 ]
	[ "${args[$((post + 1))]}" = "ExportStrings.java" ]
	[ "${args[$((post + 2))]}" = "" ]
	[ "${args[$((post + 3))]}" = $'a\x1fb' ]
}

@test "keep-project retire -deleteProject" {
	printf 'x' >"$cas/echantillon.bin"
	run ./scripts/ghidra-analyze.sh --keep-project -o "$cas/sortie" "$cas/echantillon.bin"
	[ "$status" -eq 0 ]
	mapfile -d '' args <"$JOURNAL"
	for a in "${args[@]}"; do
		[ "$a" != "-deleteProject" ]
	done
}

@test "find-ghidra rend le binaire de GHIDRA_HOME" {
	run ./scripts/find-ghidra.sh
	[ "$status" -eq 0 ]
	[ "$output" = "$cas/ghidra/support/analyzeHeadless" ]
}

@test "sans GHIDRA_HOME, .local/opt/ghidra avant le home" {
	unset GHIDRA_HOME
	mkdir -p "$cas/home/.local/opt/ghidra/courant/support" "$cas/home/ghidra/support"
	cp "$cas/ghidra/support/analyzeHeadless" "$cas/home/.local/opt/ghidra/courant/support/analyzeHeadless"
	cp "$cas/ghidra/support/analyzeHeadless" "$cas/home/ghidra/support/analyzeHeadless"
	chmod +x "$cas/home/.local/opt/ghidra/courant/support/analyzeHeadless" \
		"$cas/home/ghidra/support/analyzeHeadless"
	HOME=$cas/home run ./scripts/find-ghidra.sh
	[ "$status" -eq 0 ]
	[ "$output" = "$cas/home/.local/opt/ghidra/courant/support/analyzeHeadless" ]
}

@test "le lien current prime sur une autre version du même dossier" {
	unset GHIDRA_HOME
	vieux=$cas/home/.local/opt/ghidra/ghidra_12.1.4_PUBLIC/support
	neuf=$cas/home/.local/opt/ghidra/ghidra_12.2_PUBLIC/support
	mkdir -p "$vieux" "$neuf"
	cp "$cas/ghidra/support/analyzeHeadless" "$vieux/analyzeHeadless"
	cp "$cas/ghidra/support/analyzeHeadless" "$neuf/analyzeHeadless"
	chmod +x "$vieux/analyzeHeadless" "$neuf/analyzeHeadless"
	ln -s ghidra_12.2_PUBLIC "$cas/home/.local/opt/ghidra/current"
	HOME=$cas/home run ./scripts/find-ghidra.sh
	[ "$status" -eq 0 ]
	[ "$output" = "$cas/home/.local/opt/ghidra/current/support/analyzeHeadless" ]
}

@test "GHIDRA_HOME sans binaire : code 1, pas de repli" {
	export GHIDRA_HOME=$cas/vide
	mkdir -p "$GHIDRA_HOME" "$cas/home/ghidra/support"
	cp "$cas/ghidra/support/analyzeHeadless" "$cas/home/ghidra/support/analyzeHeadless"
	HOME=$cas/home run ./scripts/find-ghidra.sh
	[ "$status" -eq 1 ]
	[[ "$output" == *"sans analyzeHeadless"* ]]
	[[ "$output" != *"home/ghidra/support/analyzeHeadless"* ]]
}

@test "option inconnue : code 2" {
	run ./scripts/ghidra-analyze.sh --injecte
	[ "$status" -eq 2 ]
	[[ "$output" == *"option inconnue"* ]]
}
