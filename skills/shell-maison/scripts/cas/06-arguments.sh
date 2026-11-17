#!/bin/sh
set -- "a b" c
for a in "$@"; do printf '[%s]' "$a"; done
echo
IFS=:
v='x:y:z'
# shellcheck disable=SC2086
set -- $v
echo "$#"
