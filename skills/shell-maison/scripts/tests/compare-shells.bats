#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup()
{
	cd "$BATS_TEST_DIRNAME/.." || exit 1
}

teardown()
{
	rm -rf build
}

@test "dash contre lui-même : tous les cas OK" {
	run ./compare-shells dash cas
	[ "$status" -eq 0 ]
	[[ "$output" == *"10 cas, 0 KO"* ]]
}

@test "bash donne les mêmes résultats que dash sur ces cas" {
	run ./compare-shells bash cas
	[ "$status" -eq 0 ]
}

@test "un shell faux est rejeté avec le détail" {
	run ./compare-shells tests/faux-shell cas
	[ "$status" -eq 1 ]
	[[ "$output" == *"KO 01-decoupage.sh (out)"* ]]
	[[ "$output" == *"10 cas, 10 KO"* ]]
}

@test "sans argument : usage et code 2" {
	run ./compare-shells
	[ "$status" -eq 2 ]
	[[ "$output" == *"usage"* ]]
}

@test "référence absente : code 127" {
	run -127 ./compare-shells dash cas shell-qui-n-existe-pas
}

@test "dossier sans cas : échec" {
	run ./compare-shells dash tests
	[ "$status" -eq 1 ]
	[[ "$output" == *"0 cas, 0 KO"* ]]
}
