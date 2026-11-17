#!/usr/bin/env python3
"""Lancer les tests directement dans le projet, sans copie."""
import argparse
import os
import re
import subprocess
from pathlib import Path

VARIABLE_MASQUEE = re.compile(r'(?:KEY|TOKEN|SECRET|PASSWORD|PASSPHRASE|CREDENTIAL|CREDENTIALS|API|AUTH|COOKIE|PRIVATE)$', re.IGNORECASE)
AGENTS_AUTH = ('SSH_AUTH_SOCK', 'SSH_AGENT_PID', 'GPG_AGENT_INFO', 'GPG_TTY', 'GNOME_KEYRING_CONTROL')


def environnement_epure(env):
    """Le code des suites de test n'est pas fidèle : il ne voit ni secrets
    d'environnement ni sockets des agents d'authentification."""
    retour = {nom: valeur for nom, valeur in env.items() if not VARIABLE_MASQUEE.search(nom)}
    for nom in AGENTS_AUTH:
        retour.pop(nom, None)
    return retour


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', default=os.getcwd())
    parser.add_argument('--all', action='store_true')
    args = parser.parse_args()
    root = Path(args.dir).resolve()
    if root == Path.home() or root == Path('/') or root in Path.home().parents:
        raise ValueError('Une racine de projet précise est requise, pas le home.')
    if not root.is_dir():
        raise ValueError('Projet introuvable.')
    env = environnement_epure(os.environ.copy())
    extra = [Path.home() / d for d in ('.local/bin', '.local/share/mise/shims', '.bun/bin')]
    env['PATH'] = ':'.join([str(d) for d in extra if d.is_dir()] + [env.get('PATH', '')])
    # Pas de mode watch ni de couleurs : un runner interactif bloquerait le tour.
    env['CI'] = '1'
    env.setdefault('FORCE_COLOR', '0')
    hooks = Path(__file__).resolve().parent
    command = ['bash', str(hooks / 'test-runner.sh'), '--dir', str(root)]
    if args.all:
        command.append('--all')
    return subprocess.call(
        command,  # nosemgrep: dangerous-subprocess-use-tainted-env-args
        cwd=root,
        env=env,
    )


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as error:
        print('Tests non validés : ' + str(error), flush=True)
        raise SystemExit(1)
