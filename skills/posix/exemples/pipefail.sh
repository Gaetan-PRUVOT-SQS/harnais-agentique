#!/bin/sh
set -eu
# shellcheck disable=SC3040
if (set -o pipefail) 2>/dev/null; then set -o pipefail; fi
false | true
printf "%s\n" non-atteint
