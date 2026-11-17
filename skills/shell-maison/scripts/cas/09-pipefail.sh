#!/bin/sh
# shellcheck disable=SC3040
set -o pipefail
false | true
echo "$?"
set +o pipefail
false | true
echo "$?"
