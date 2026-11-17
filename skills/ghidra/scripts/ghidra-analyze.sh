#!/usr/bin/env bash
# Adaptation locale : arguments en tableau, projet hors de /tmp. Apache-2.0, LICENSE.
set -euo pipefail
shopt -s inherit_errexit

nom=${0##*/}

usage()
{
	cat <<'EOF'
Usage: ghidra-analyze.sh [options] [--] <binaire>

  -o, --output <dir>       dossier de sortie (defaut: .)
  -s, --script <nom>       script apres analyse, repetable
  -a, --script-args <arg>  un argument du dernier script, repetable
  --script-path <chemin>   chemin de scripts supplementaire
  -p, --processor <id>     architecture
  -c, --cspec <id>         compilateur
  --no-analysis            pas d'auto-analyse
  --timeout <secondes>     delai par fichier
  --keep-project           garder le projet
  --project-dir <dir>      projet (defaut: <sortie>/ghidra-project)
  --project-name <nom>     nom du projet
  -v, --verbose            commande sur stderr
  -h, --help               cette aide
EOF
}

die()
{
	printf '%s: %s\n' "$nom" "$1" >&2
	exit "${2:-1}"
}

refuse_tmp()
{
	local canon
	canon=$(realpath -m -- "$1")
	case $canon in
	/tmp | /tmp/* | /var/tmp | /var/tmp/*)
		die "chemin refuse: $1" 2
		;;
	esac
}

main()
{
	local output_dir=.
	local script_path="" processor="" cspec="" timeout="" project_dir="" project_name=""
	local no_analysis=0 keep_project=0 verbose=0 binary=""
	local -a scripts=() arg_counts=() all_args=() cmd=()
	local script_dir analyze builtin full_path log_file base_name i exit_code last count offset

	script_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)

	while [[ $# -gt 0 ]]; do
		case $1 in
		-h | --help)
			usage
			exit 0
			;;
		-o | --output)
			[[ $# -ge 2 ]] || die "option $1 sans valeur" 2
			output_dir=$2
			shift 2
			;;
		-s | --script)
			[[ $# -ge 2 ]] || die "option $1 sans valeur" 2
			scripts+=("$2")
			arg_counts+=(0)
			shift 2
			;;
		-a | --script-args)
			[[ $# -ge 2 ]] || die "option $1 sans valeur" 2
			[[ ${#scripts[@]} -gt 0 ]] || die "script-args sans script" 2
			last=$((${#scripts[@]} - 1))
			all_args+=("$2")
			arg_counts[$last]=$((arg_counts[$last] + 1))
			shift 2
			;;
		--script-path)
			[[ $# -ge 2 ]] || die "option $1 sans valeur" 2
			script_path=$2
			shift 2
			;;
		-p | --processor)
			[[ $# -ge 2 ]] || die "option $1 sans valeur" 2
			processor=$2
			shift 2
			;;
		-c | --cspec)
			[[ $# -ge 2 ]] || die "option $1 sans valeur" 2
			cspec=$2
			shift 2
			;;
		--no-analysis)
			no_analysis=1
			shift
			;;
		--timeout)
			[[ $# -ge 2 ]] || die "option $1 sans valeur" 2
			timeout=$2
			shift 2
			;;
		--keep-project)
			keep_project=1
			shift
			;;
		--project-dir)
			[[ $# -ge 2 ]] || die "option $1 sans valeur" 2
			project_dir=$2
			shift 2
			;;
		--project-name)
			[[ $# -ge 2 ]] || die "option $1 sans valeur" 2
			project_name=$2
			shift 2
			;;
		-v | --verbose)
			verbose=1
			shift
			;;
		--)
			shift
			[[ $# -eq 1 ]] || die "un seul binaire" 2
			binary=$1
			shift
			;;
		-*)
			die "option inconnue: $1" 2
			;;
		*)
			[[ -z $binary ]] || die "un seul binaire" 2
			binary=$1
			shift
			;;
		esac
	done

	if [[ -z $binary ]]; then
		usage >&2
		die "binaire manquant" 2
	fi
	[[ -f $binary ]] || die "fichier introuvable: $binary" 1
	if [[ -n $timeout && ! $timeout =~ ^[0-9]+$ ]]; then
		die "timeout invalide" 2
	fi
	refuse_tmp "$output_dir"
	if [[ -z $project_dir ]]; then
		project_dir=$output_dir/ghidra-project
	fi
	refuse_tmp "$project_dir"
	mkdir -p -- "$output_dir" "$project_dir"

	if [[ -z $project_name ]]; then
		base_name=$(basename -- "$binary")
		project_name=ghidra_${base_name//[^A-Za-z0-9_-]/_}_$$
	fi

	analyze=$("$script_dir/find-ghidra.sh")
	builtin=$script_dir/ghidra_scripts
	if [[ -n $script_path ]]; then
		full_path="${builtin}:${script_path}"
	else
		full_path=$builtin
	fi

	cmd=("$analyze" "$project_dir" "$project_name" -import "$binary" -scriptPath "$full_path")
	offset=0
	for i in "${!scripts[@]}"; do
		cmd+=(-postScript "${scripts[$i]}")
		count=${arg_counts[$i]}
		if [[ $count -gt 0 ]]; then
			cmd+=("${all_args[@]:offset:count}")
		fi
		offset=$((offset + count))
	done

	export GHIDRA_OUTPUT_DIR=$output_dir
	if [[ -n $processor ]]; then
		cmd+=(-processor "$processor")
	fi
	if [[ -n $cspec ]]; then
		cmd+=(-cspec "$cspec")
	fi
	if [[ $no_analysis -eq 1 ]]; then
		cmd+=(-noanalysis)
	fi
	if [[ -n $timeout ]]; then
		cmd+=(-analysisTimeoutPerFile "$timeout")
	fi
	if [[ $keep_project -eq 0 ]]; then
		cmd+=(-deleteProject)
	fi
	log_file=$output_dir/ghidra_analysis.log
	cmd+=(-log "$log_file")

	if [[ $verbose -eq 1 ]]; then
		printf 'Lancement:' >&2
		printf ' %q' "${cmd[@]}" >&2
		printf '\n' >&2
	fi

	set +e
	"${cmd[@]}" 2>&1 | tee -- "$output_dir/ghidra_output.log"
	exit_code=${PIPESTATUS[0]}
	set -e
	if [[ $exit_code -ne 0 ]]; then
		printf '%s: analyse en echec, code %s, journal %s\n' "$nom" "$exit_code" "$log_file" >&2
	else
		printf 'Analyse terminee. Sortie: %s\n' "$output_dir"
	fi
	exit "$exit_code"
}

main "$@"
