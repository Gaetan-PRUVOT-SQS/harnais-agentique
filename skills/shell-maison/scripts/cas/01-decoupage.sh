#!/bin/sh
x='a  b'
# shellcheck disable=SC2086
printf '[%s]' $x "$x"
echo
