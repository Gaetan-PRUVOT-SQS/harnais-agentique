#!/usr/bin/env bash
# Scan un fichier ou un dossier pour la baseline sécu.
# Usage : cyber-scan.sh [--root RACINE] [--newer REPERE] CIBLE
#   --root  : racine du projet, où lire .cyber-ignore (défaut : CIBLE si
#             c'est un dossier, sinon son dossier)
#   --newer : dans un dossier, seulement les fichiers plus récents que REPERE
# .cyber-ignore : une exception par ligne, `chemin`, `chemin:ligne` ou
# `dossier/`, relatifs à la racine ; `#` pour les commentaires.
# stdout = hits, exit 1 s'il y en a, 0 sinon.
set -euo pipefail

. "$(dirname "$(readlink -f "$0")")/ignores.sh"
prune_args

root=""
newer=""
while [ $# -gt 1 ]; do
	case "$1" in
	--root) root="$2" ; shift 2 ;;
	--newer) newer="$2" ; shift 2 ;;
	*) break ;;
	esac
done
target="${1:-}"
if [ -z "$target" ]; then
	exit 0
fi
if [ -z "$root" ]; then
	if [ -d "$target" ]; then
		root="$target"
	else
		root="$(dirname "$target")"
	fi
fi
root="$(cd "$root" && pwd -P)"
target="$(realpath -e "$target" 2>/dev/null || printf '%s' "$target")"

# Vider un élément (innerHTML = '') n'injecte rien : pas signalé.
SAFE='innerHTML[[:space:]]*=[[:space:]]*(""|'"'"''"'"'|``)[[:space:]]*;?[[:space:]]*$|yaml\.(safe_)?load\(.*SafeLoader|\.php.[0-9]+:.*[^v]sprintf[[:space:]]*\('

# Limite à gauche : fgets, retrieval, ft_printf ou $obj->exec ne sont pas visés.
B='(^|[^.a-zA-Z0-9_$>])'
# shellcheck disable=SC2016
PATTERN="${B}"'(strcpy|strcat|gets|sprintf|system|popen|eval)[[:space:]]*\(|'"${B}"'scanf[[:space:]]*\([[:space:]]*"%s"|new Function[[:space:]]*\(|innerHTML|dangerouslySetInnerHTML|document\.write[[:space:]]*\(|\.html[[:space:]]*\(|v-html|pickle\.loads[[:space:]]*\(|os\.(system|popen)[[:space:]]*\(|child_process\.exec(Sync)?[[:space:]]*\(|shell[[:space:]]*=[[:space:]]*True|yaml\.load[[:space:]]*\(|execute[[:space:]]*\([[:space:]]*f["'"'"']|Access-Control-Allow-Origin.*\*|localStorage\.setItem\([^)]*(token|password|jwt|secret|auth)|sessionStorage\.setItem\([^)]*(token|password|jwt|secret|auth)|'"${B}"'printf[[:space:]]*\([[:space:]]*[a-zA-Z_][a-zA-Z0-9_]*[[:space:]]*\)|shell_exec[[:space:]]*\(|passthru[[:space:]]*\(|proc_open[[:space:]]*\(|unserialize[[:space:]]*\(|(^|[^.a-zA-Z_])exec[[:space:]]*\(|execSync[[:space:]]*\([^)]*\+|echo[[:space:]]+\$_(GET|POST|REQUEST|COOKIE)|(query|prepare|exec)[[:space:]]*\([^)]*\$_(GET|POST|REQUEST|COOKIE)|mark_safe[[:space:]]*\(|\|[[:space:]]*safe[[:space:]]*}}|objects\.raw[[:space:]]*\(|\.extra[[:space:]]*\(|BEGIN PRIVATE KEY|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,}|sk-ant-|sk_live_'

scan_file() {
	local f="$1"
	local base
	base=$(basename "$f")
	case "$base" in
	*.c|*.h|*.js|*.jsx|*.mjs|*.ts|*.tsx|*.py|*.php|*.rb|*.go|*.java|*.sh|*.sql|*.html|*.htm|*.vue|*.env|*.json)
		;;
	Makefile|makefile)
		;;
	*)
		return 0
		;;
	esac
	grep_hits "$f"
}

# Octets bruts (LC_ALL=C, -a) : un fichier en latin-1 n'est pas pris pour du
# binaire. -Z sépare le nom du fichier, qui peut contenir « : ».
grep_hits() {
	LC_ALL=C xargs -0 -r grep -a -nHZ -E "$PATTERN" 2>/dev/null < <(printf '%s\0' "$@") \
		| tr '\0' '\1' \
		| LC_ALL=C grep -a -vE "$SAFE" \
		| LC_ALL=C sed -E 's/\x01([0-9]+):.*$/:\1/' || true
}

if [ -f "$target" ]; then
	hits="$(scan_file "$target")"
elif [ -d "$target" ]; then
	recent=()
	if [ -n "$newer" ] && [ -e "$newer" ]; then
		# -cnewer : un fichier déplacé par mv garde son mtime, pas son ctime.
		recent=(-cnewer "$newer")
	fi
	hits="$(
		find "$target" -mindepth 1 "${PRUNE[@]}" \
			-o -type f \( \
				-name '*.c' -o -name '*.h' -o -name '*.js' -o -name '*.jsx' \
				-o -name '*.mjs' -o -name '*.ts' -o -name '*.tsx' \
				-o -name '*.py' -o -name '*.php' -o -name '*.rb' \
				-o -name '*.go' -o -name '*.java' -o -name '*.sh' \
				-o -name '*.sql' -o -name '*.html' -o -name '*.htm' \
				-o -name '*.vue' -o -name '*.env' -o -name '*.json' \
				-o -name Makefile -o -name makefile \
			\) "${recent[@]}" -print0 2>/dev/null \
		| LC_ALL=C xargs -0 -r grep -a -nHZ -E "$PATTERN" 2>/dev/null \
		| tr '\0' '\1' \
		| LC_ALL=C grep -a -vE "$SAFE" \
		| LC_ALL=C sed -E 's/\x01([0-9]+):.*$/:\1/' || true
	)"
else
	exit 0
fi

# Exceptions justifiées du projet. Les chemins sont comparés en relatif.
if [ -n "$hits" ] && [ -f "$root/.cyber-ignore" ]; then
	hits="$(printf '%s\n' "$hits" | CYBER_ROOT="$root/" LC_ALL=C awk '
		BEGIN { root = ENVIRON["CYBER_ROOT"] }
		NR == FNR {
			sub(/\r$/, "")
			if (FNR == 1)
				sub(/^\357\273\277/, "")
			sub(/[ \t]*#.*/, "")
			gsub(/^[ \t]+|[ \t]+$/, "")
			sub(/^\.\//, "")
			if ($0 != "")
				skip[++n] = $0
			next
		}
		{
			line = $0
			rel = line
			if (index(rel, root) == 1)
				rel = substr(rel, length(root) + 1)
			sub(/^\.\//, "", rel)
			file = rel
			sub(/:[0-9]+$/, "", file)
			for (i = 1; i <= n; i++) {
				s = skip[i]
				if (s == rel || s == file)
					next
				if (s ~ /\/$/ && index(file, s) == 1)
					next
			}
			print line
		}' "$root/.cyber-ignore" -)"
fi

if [ -n "$hits" ]; then
	# Tronquer après les exceptions, jamais avant.
	total="$(printf '%s\n' "$hits" | wc -l)"
	printf '%s\n' "$hits" | head -n 40
	if [ "$total" -gt 40 ]; then
		echo "... et $((total - 40)) autres lignes"
	fi
	exit 1
fi
exit 0
