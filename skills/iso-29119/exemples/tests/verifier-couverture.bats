#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
	outil="$BATS_TEST_DIRNAME/../verifier-couverture"
	fixtures="$BATS_TEST_DIRNAME/fixtures"
}

@test "couverture complete : succes" {
	run -0 "$outil" "$fixtures/complet.txt"
	[[ "$output" == *"Condition outcomes covered 100.00%"* ]]
}

@test "MC/DC sous le seuil : echec" {
	run -1 "$outil" "$fixtures/mcdc-partiel.txt"
	[[ "$output" == *"Condition outcomes covered 87.50% < 100%"* ]]
}

@test "MC/DC sous un seuil plus bas : succes" {
	run -0 "$outil" "$fixtures/mcdc-partiel.txt" 80
}

@test "mesure MC/DC absente : echec" {
	run -1 "$outil" "$fixtures/sans-mcdc.txt"
	[[ "$output" == *"mesure absente : Condition outcomes covered"* ]]
}

@test "resume illisible : echec" {
	run -1 "$outil" "$fixtures/absent.txt"
	[[ "$output" == *"illisible"* ]]
}

@test "mauvais usage : code 2" {
	run -2 "$outil"
	run -2 "$outil" "$fixtures/complet.txt" dix
	run -2 "$outil" a b c
}
