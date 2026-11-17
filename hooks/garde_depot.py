"""Travail local qu'aucun commit ne garde, et commandes git qui le détruisent."""
import os
import subprocess
import time
from pathlib import Path

MARQUEURS = ('.git', '.mode-side-project')
PROFONDEUR = 2
MAX_DOSSIERS = 2000
DELAI_GIT = 3
# Le hook PreToolUse a 10 s : tous les appels git d'un même verdict se partagent ce budget.
DELAI_TOTAL = 7
MAX_CHEMINS = 200
ECHEANCE = {}


class GitIndisponible(Exception):
    pass


def git(dossier, *args, entree=None):
    fin = ECHEANCE.setdefault('fin', time.monotonic() + DELAI_TOTAL)
    restant = min(DELAI_GIT, fin - time.monotonic())
    if restant <= 0:
        raise GitIndisponible('budget git du garde épuisé')
    try:
        return subprocess.run(['git', '-C', str(dossier), *args], capture_output=True, text=True,
                              input=entree, timeout=restant, check=False)
    except (OSError, subprocess.TimeoutExpired) as erreur:
        raise GitIndisponible(str(erreur)) from erreur


def est_racine_projet(chemin):
    return chemin.is_dir() and any((chemin / nom).exists() for nom in MARQUEURS)


def contient_projet(chemin):
    niveau, vus = [chemin], 0
    for _ in range(PROFONDEUR):
        suivant = []
        for dossier in niveau:
            try:
                enfants = [Path(e.path) for e in os.scandir(dossier) if e.is_dir(follow_symlinks=False)]
            except OSError:
                continue
            vus += len(enfants)
            if vus > MAX_DOSSIERS or any(est_racine_projet(e) for e in enfants):
                return True
            suivant.extend(enfants)
        niveau = suivant
    return False


def racine_depot(chemin):
    dossier = chemin if chemin.is_dir() else chemin.parent
    if not dossier.is_dir():
        return None
    resultat = git(dossier, 'rev-parse', '--show-toplevel')
    return Path(resultat.stdout.strip()) if resultat.returncode == 0 else None


def statut(depot, relatif):
    resultat = git(depot, 'status', '--porcelain=v1', '-z', '--ignored=matching', '--', relatif)
    if resultat.returncode:
        raise GitIndisponible(resultat.stderr.strip())
    entrees, morceaux = [], iter(resultat.stdout.split('\0'))
    for morceau in morceaux:
        if len(morceau) > 3:
            entrees.append((morceau[:2], morceau[3:]))
            if morceau[0] in 'RC':
                next(morceaux, None)
    return entrees


def exclu_localement(depot, chemins):
    resultat = git(depot, 'check-ignore', '-v', '-z', '--stdin', entree='\0'.join(chemins[:MAX_CHEMINS]) + '\0')
    if resultat.returncode > 1:
        raise GitIndisponible(resultat.stderr.strip())
    champs = resultat.stdout.split('\0')
    return any(source.endswith('info/exclude') for source in champs[0::4])


def perte_locale(depot, chemin):
    entrees = statut(depot, os.path.relpath(chemin, depot))
    if any(code != '!!' for code, _ in entrees):
        return 'travail non commité'
    ignores = [chemin_e for code, chemin_e in entrees if code == '!!']
    if ignores and exclu_localement(depot, ignores):
        return 'fichiers locaux exclus par .git/info/exclude'
    return None


def danger_rm(chemin):
    if not chemin.exists():
        return None
    if chemin.name == '.git':
        return 'historique git'
    if est_racine_projet(chemin):
        return 'racine de projet'
    depot = racine_depot(chemin)
    if depot is not None:
        return perte_locale(depot, chemin)
    return 'dossier qui contient un projet' if chemin.is_dir() and contient_projet(chemin) else None


def options_courtes(args, lettre):
    return any(a.startswith('-') and not a.startswith('--') and lettre in a[1:] for a in args)


def force(args):
    return '--force' in args or options_courtes(args, 'f')


def sous_commande(args, cwd):
    i = 0
    while i < len(args) and args[i].startswith('-'):
        if args[i] == '-C' and i + 1 < len(args):
            cwd = os.path.join(cwd, os.path.expanduser(args[i + 1]))
        i += 2 if args[i] in ('-C', '-c', '--git-dir', '--work-tree', '--namespace') else 1
    if i >= len(args):
        return None, [], cwd
    return args[i], args[i + 1:], cwd


def chemins_vises(args):
    if '--' in args:
        return args[args.index('--') + 1:]
    return [a for a in args if not a.startswith('-') and a != 'HEAD']


def jette_modifications(commande, args):
    if commande == 'reset':
        return ['.'] if '--hard' in args else None
    if commande == 'checkout' and ('--' in args or '.' in args):
        return chemins_vises(args) or ['.']
    if commande in ('checkout', 'switch') and (force(args) or '--discard-changes' in args):
        return ['.']
    if commande == 'restore':
        indexe_seul = ('--staged' in args or options_courtes(args, 'S')) and not (
            '--worktree' in args or options_courtes(args, 'W'))
        return None if indexe_seul else chemins_vises(args) or ['.']
    return None


def modifications_suivies(dossier, chemins):
    resultat = git(dossier, 'status', '--porcelain', '--untracked-files=no', '--', *chemins)
    return resultat.returncode == 0 and bool(resultat.stdout.strip())


def danger_git(args, cwd):
    commande, reste, dossier = sous_commande(args, cwd)
    if commande == 'clean':
        simulation = '--dry-run' in reste or options_courtes(reste, 'n')
        return None if simulation else 'git clean supprime les fichiers non suivis'
    if commande == 'worktree' and reste[:1] == ['remove'] and force(reste):
        return 'worktree supprimé de force avec son travail'
    chemins = jette_modifications(commande, reste)
    if chemins and modifications_suivies(dossier, chemins):
        return 'modifications non commitées jetées'
    return None
