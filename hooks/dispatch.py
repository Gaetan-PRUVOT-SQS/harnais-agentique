#!/usr/bin/env python3
"""Hooks personnels de Claude Code."""
import fcntl
import functools
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

from garde_depot import contient_projet

ROOT = Path(__file__).resolve().parent
# Les règles fixes sont dans ~/.agents/AGENTS.md, chargé par chaque agent.
# Ici, seulement ce qui change d'un tour à l'autre (anciens force-*.sh :
# ~/.agents/archives/hooks-force-20260927 et hooks-mode-20260929).
PROMPT = ['skill-trigger-sft-dataset']
STOP = ['gate-cyber-stop', 'gate-secrets-stop', 'gate-sast-stop', 'gate-regression-stop', 'gate-oracle-stop']
OUTILS_MODIFIANTS = ('Write', 'Edit', 'NotebookEdit', 'MultiEdit', 'ApplyPatch')
VERROU_DUREE = 6 * 3600
GARDE_INTERROMPUE = ('Le garde a été interrompu avant sa fin (délai dépassé ou arrêt brutal) : '
                     'au moins un appel d\'outil n\'a pas été contrôlé. Reprendre l\'action '
                     'concernée sous contrôle avant d\'annoncer quoi que ce soit.')
EVENEMENTS_ATTENDUS = ('SessionStart', 'UserPromptSubmit', 'PreToolUse', 'PostToolUse', 'Stop')
CONFIG = Path(os.environ.get('AGENT_CONFIG_ROOT', str(Path.home() / '.agents')))
CONFIG_GATE_TIMEOUT = 240
MARKERS = ('.git', '.mode-side-project')
SHELL_FILES = ('.sh', '.bash')
SHEBANG_SHELL = re.compile(r'^#!\s*(?:/usr)?/bin/(?:env\s+)?(?:ba|da|k)?sh\b')
# Le Stop a 400 s dans settings.json : finir avant d'être tué.
STOP_BUDGET = 360
# Le PostToolUse a 150 s : quatre gates à 60 s dépasseraient sans budget commun.
POST_BUDGET = 140
# États de sessions terminées gardés une semaine, puis supprimés au SessionStart.
ETAT_MAX_AGE = 7 * 86400
EXTRA_PATH = ('.local/bin', '.local/share/mise/shims', '.bun/bin')
JQ_MISSING = 'jq introuvable : contrôles des hooks non lancés, ne pas annoncer de validation (installer jq).'
OUTILS_GROK = {'run_terminal_command': 'Bash', 'read_file': 'Read', 'grep': 'Grep',
               'search_replace': 'Edit', 'hashline_edit': 'Edit', 'write': 'Write',
               'web_search': 'WebSearch', 'web_fetch': 'WebFetch', 'list_dir': 'Glob'}
CHILD = {}


@functools.cache
def ignores():
    # Même liste que les scripts shell (ignores.sh).
    text = (ROOT / 'ignores.sh').read_text()
    return set(re.search(r'IGNORES="([^"]*)"', text).group(1).split())


def normalized(raw):
    if not isinstance(raw, dict):
        raise TypeError('payload JSON non objet')
    data = dict(raw)
    data['hook_event_name'] = sys.argv[1] if len(sys.argv) > 1 else data.get('hook_event_name')
    cwd = data.get('cwd') or os.getcwd()
    # Chemin résolu : pas de slash final ni de lien pour les scripts.
    data['cwd'] = str(Path(str(cwd)).resolve())
    tool = data.get('tool_input')
    data['tool_input'] = dict(tool) if isinstance(tool, dict) else {}
    nom = data.get('tool_name')
    if isinstance(nom, str) and nom in OUTILS_GROK:
        data['tool_name'] = OUTILS_GROK[nom]
    if 'file_path' not in data['tool_input'] and isinstance(data['tool_input'].get('target_file'), str):
        data['tool_input']['file_path'] = data['tool_input']['target_file']
    if data.get('stopHookActive') or data.get('stop_hook_active'):
        data['stop_hook_active'] = True
    if data['hook_event_name'] in ('Stop', 'SubagentStop') and not data.get('reason'):
        data['reason'] = 'end_turn'
    return data


def marked_root(start):
    """Premier parent avec .git ou un marqueur de projet, sans passer le home."""
    home = Path.home().resolve()
    for folder in (start, *start.parents):
        if folder in (home, Path.home(), Path('/')):
            break
        if any((folder / name).exists() for name in MARKERS):
            return folder
    return None


def project_root(cwd):
    return marked_root(cwd) or cwd


def conteneur_de_projets(root):
    """Dossier sans marqueur qui contient des projets (Bureau) : pas un projet lui-même."""
    return marked_root(root) is None and contient_projet(root)


def paths(data):
    tool = data['tool_input']
    found = [tool[k] for k in ('file_path', 'notebook_path', 'path')
             if isinstance(tool.get(k), str)]
    base = Path(data['cwd']).resolve()
    result = []
    for value in found:
        raw = Path(os.path.abspath(base / value))
        # Un lien vers un fichier peut mener hors du projet : on ne suit pas.
        if raw.is_symlink() or not raw.is_file() or raw in [r for r, _ in result]:
            continue
        result.append((raw, raw.resolve()))
    return result


def script_shell(path):
    if path.suffix in SHELL_FILES:
        return True
    if path.suffix:
        return False
    try:
        with path.open('rb') as f:
            premiere = f.readline(200).decode(errors='replace')
    except OSError:
        return False
    return bool(SHEBANG_SHELL.match(premiere))


def changed_since(root, stamp):
    """Vrai si un fichier du projet est plus récent que le début du tour."""
    if not stamp.is_file():
        # Pas de repère (premier tour) : on contrôle.
        return True
    limit = stamp.stat().st_mtime
    for top, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in ignores()]
        for name in files:
            try:
                info = os.lstat(os.path.join(top, name))
                # ctime : un fichier déplacé par mv garde son ancien mtime.
                if max(info.st_mtime, info.st_ctime) > limit:
                    return True
            except OSError:
                continue
    return False


def config_changes(stamp):
    """Fichiers modifiés de la config git plus récents que le début du tour.

    None : dépôt git présent mais état invérifiable (status en échec).
    Une absence de preuve n'est pas une absence de modification."""
    if not stamp.is_file():
        return []
    if not (CONFIG / '.git').is_dir():
        return []
    try:
        status = subprocess.run(['git', '-C', str(CONFIG), 'status', '--porcelain', '-z'],
                                capture_output=True, text=True, timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if status.returncode != 0:
        return None
    limit = stamp.stat().st_mtime
    changes = []
    for entry in status.stdout.split('\0'):
        try:
            info = os.lstat(CONFIG / entry[3:])
        except OSError:
            continue
        if len(entry) > 3 and max(info.st_mtime, info.st_ctime) > limit:
            changes.append(entry[3:])
    return changes


def verrou_fichier(state, root):
    return state.parent / 'locks' / (hashlib.sha256(str(root).encode()).hexdigest()[:24] + '.json')


def autre_ecrivain(state, root, identity):
    """Session vivante qui écrit déjà sur ce dépôt ; None si le dépôt est libre."""
    try:
        garde = json.loads(verrou_fichier(state, root).read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return None
    if garde.get('session') == identity:
        return None
    try:
        age = time.time() - float(garde.get('ts') or 0)
    except (TypeError, ValueError):
        return None
    return str(garde.get('session')) if age < VERROU_DUREE else None


def ecrit_vivant(state, root, identity):
    dossier = state.parent / 'locks'
    dossier.mkdir(parents=True, exist_ok=True, mode=0o700)
    verrou_fichier(state, root).write_text(
        json.dumps({'session': identity, 'ts': time.time()}), encoding='utf-8')


def libere_verrous(state, identity):
    try:
        fichiers = list((state.parent / 'locks').glob('*.json'))
    except OSError:
        return
    for fichier in fichiers:
        try:
            if json.loads(fichier.read_text(encoding='utf-8')).get('session') == identity:
                fichier.unlink()
        except (OSError, json.JSONDecodeError):
            continue


def rafraichit_verrous(state, identity):
    """Battement de cœur : une session active garde ses dépôts, l'expiration
    ne mesure que l'inactivité, pas l'ancienneté du dernier écrit."""
    try:
        fichiers = list((state.parent / 'locks').glob('*.json'))
    except OSError:
        return
    for fichier in fichiers:
        try:
            donnees = json.loads(fichier.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError):
            continue
        if donnees.get('session') == identity:
            donnees['ts'] = time.time()
            fichier.write_text(json.dumps(donnees), encoding='utf-8')


def note_qualite(state, chemin, problemes):
    """État des fichiers dont une gate de qualité a échoué : tient le Stop
    jusqu'à ce qu'une écriture du fichier repasse propre."""
    fichier = state / 'qualite-ko.json'
    try:
        etat = json.loads(fichier.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        etat = {}
    if problemes:
        etat[str(chemin)] = ' '.join(problemes[-1].split())[:300]
    else:
        etat.pop(str(chemin), None)
    fichier.write_text(json.dumps(etat, ensure_ascii=False, indent=0, sort_keys=True), encoding='utf-8')


def run(name, data, env, timeout=60, deadline=None):
    if deadline is not None:
        timeout = min(timeout, deadline - time.monotonic())
        if timeout < 5:
            return {'decision': 'block', 'reason': name + ' : pas lancé, temps du hook épuisé. Contrôle non validé.'}
    process = subprocess.Popen(['bash', str(ROOT / (name + '.sh'))],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, env=env,
                               cwd=data['cwd'], start_new_session=True)
    CHILD['pid'] = process.pid
    try:
        output, _ = process.communicate(json.dumps(data), timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.communicate()
        return {'decision': 'block', 'reason': name + ' : délai dépassé, contrôle non validé.'}
    finally:
        CHILD.pop('pid', None)
    if process.returncode:
        return {'decision': 'block', 'reason': name + ' : échec technique, contrôle non validé.'}
    if not output.strip():
        return {}
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {'decision': 'block', 'reason': name + ' : réponse invalide, contrôle non validé.'}


AGENT_MARKERS = ('<task-notification>', '<agent-message', 'Another Claude session sent a message',
                 '[SYSTEM NOTIFICATION', '[Subagent hand-back]')


def from_agent(prompt):
    """Vrai si le « prompt » est une notification ou un rapport d'agent."""
    head = str(prompt or '').lstrip()
    return head.startswith(AGENT_MARKERS)


def in_config(path):
    home = Path.home().resolve()
    return path == home or any(path.is_relative_to(home / d)
                               for d in ('.claude', '.agents'))


def problems_registration(chemin):
    """Événements attendus absents de l'enregistrement moteur, None si ce
    fichier n'enregistre pas ce harnais (absent, illisible, sans dispatch.py)."""
    try:
        donnees = json.loads(Path(chemin).read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(donnees, dict):
        return None
    hooks = donnees.get('hooks')
    if not isinstance(hooks, dict) or 'dispatch.py' not in json.dumps(hooks):
        return None
    if 'events' in hooks:
        if hooks.get('enabled') is not True:
            return ['hooks désactivés chez le moteur (enabled: true attendu)']
        evenements = hooks['events']
    else:
        evenements = hooks
    if not isinstance(evenements, dict):
        return None
    return [evenement + " : événement retiré de l'enregistrement du moteur"
            for evenement in EVENEMENTS_ATTENDUS if evenement not in evenements]


def registration_problems():
    """Premier enregistrement moteur qui référence ce harnais, None sinon.

    Un moteur retiré du harnais n'alerte plus : sans aucun hook actif, rien
    ne peut s'exécuter pour le constater."""
    candidats = ([os.environ['AGENT_MOTEUR_HOOKS']] if os.environ.get('AGENT_MOTEUR_HOOKS')
                 else [str(Path.home() / '.zcode' / 'cli' / 'config.json'),
                       str(Path.home() / '.claude' / 'settings.json'),
                       str(Path.home() / '.grok' / 'hooks' / 'agents.json')])
    for chemin in candidats:
        problemes = problems_registration(chemin)
        if problemes is not None:
            return problemes
    return None


def harnais_degrade(state, problemes):
    """Pose ou lève le drapeau de dégradation selon l'enregistrement moteur."""
    if problemes:
        (state / 'harnais-degrade').write_text('\n'.join(problemes), encoding='utf-8')
        return 'Harnais dégradé : ' + '\n'.join(problemes) \
               + '. Contrôles moteur absents, ne pas annoncer de validation.'
    (state / 'harnais-degrade').unlink(missing_ok=True)
    return None


def protected(root):
    home = Path.home().resolve()
    return (root == home or root == Path('/') or root in home.parents
            or any(root.is_relative_to(home / d)
                   for d in ('.claude', '.agents')))


def read_lines(path):
    try:
        return [line for line in path.read_text().splitlines() if line]
    except OSError:
        return []


def remember(path, root):
    if str(root) not in read_lines(path):
        with path.open('a') as handle:
            handle.write(str(root) + '\n')


def purge_etats(state_root, courant):
    """Supprime les états des sessions terminées depuis plus d'une semaine."""
    limite = time.time() - ETAT_MAX_AGE
    try:
        dossiers = [d for d in state_root.iterdir() if d.is_dir() and d != courant]
    except OSError:
        return
    for dossier in dossiers:
        fin = dossier / 'ended'
        try:
            if fin.is_file() and fin.stat().st_mtime < limite:
                shutil.rmtree(dossier, ignore_errors=True)
        except OSError:
            continue


def stop_children(signum, frame):
    # Claude Code tue le hook au délai : ne pas laisser les tests orphelins.
    if CHILD.get('pid'):
        try:
            os.killpg(CHILD['pid'], signal.SIGKILL)
        except OSError:
            pass
    raise SystemExit(128 + signum)


def sous_grok():
    # Grok pose cette variable sur chaque hook. Il jette le contexte d'un
    # UserPromptSubmit qui laisse passer : le rappel passe par PreToolUse.
    return bool(os.environ.get('GROK_HOOK_EVENT'))


def prendre_ko(path):
    if not path.is_file():
        return None
    texte = path.read_text()[:1500]
    path.unlink()
    return ('Contrôles restés KO au tour précédent, à signaler sans annoncer de validation :\n'
            + texte)


def etat_session(identity):
    if not identity:
        return None
    key = hashlib.sha256(('native' + str(identity)).encode()).hexdigest()[:24]
    root = Path(os.environ.get('AGENT_HOOK_STATE_ROOT',
                               str(Path.home() / '.local/state/agent-hooks')))
    return root / key


def hook_env(state):
    env = os.environ.copy()
    home = Path.home()
    extra = [str(home / d) for d in EXTRA_PATH if (home / d).is_dir()]
    env['PATH'] = ':'.join(extra + [env.get('PATH', '')])
    env.update(AGENT_HOOK_STATE=str(state), AGENT_HOOKS_ROOT=str(ROOT),
               AGENT_SKILLS_ROOT=str(CONFIG / 'skills'), AGENT_CONFIG_ROOT=str(CONFIG))
    return env


def main():
    data = normalized(json.load(sys.stdin))
    event = data['hook_event_name']
    fin = event in ('Stop', 'SubagentStop')
    identity = data.get('session_id')
    state = etat_session(identity)
    if event == 'PreToolUse':
        # Fail-closed : une marque posée avant le garde et levée après. Un hook
        # tué en plein verdict laisse la marque, et le Stop du tour bloque.
        if state is not None:
            state.mkdir(parents=True, exist_ok=True, mode=0o700)
            (state / 'garde-encours').touch()
        from garde import verdict
        sortie = verdict(data.get('tool_name'), data['tool_input'], data['cwd'])
        if state is not None:
            (state / 'garde-encours').unlink(missing_ok=True)
        decision = sortie.get('hookSpecificOutput', {}).get('permissionDecision')
        if state is not None and data.get('tool_name') in OUTILS_MODIFIANTS and decision is None:
            vise = next((data['tool_input'][cle] for cle in ('file_path', 'path', 'target_file')
                         if isinstance(data['tool_input'].get(cle), str)), None)
            chemin = Path(os.path.abspath(os.path.join(data['cwd'], vise))) if vise else None
            marque = marked_root(chemin.parent) if chemin is not None else None
            if marque is None and chemin is not None:
                base = Path(data['cwd'])
                if chemin.is_relative_to(base) and not protected(base) and not conteneur_de_projets(base):
                    marque = base
            if marque is not None:
                autre = autre_ecrivain(state, marque.resolve(), identity)
                if autre:
                    sortie = {'hookSpecificOutput': {
                        'hookEventName': 'PreToolUse', 'permissionDecision': 'deny',
                        'permissionDecisionReason': 'Dépôt déjà en écriture par la session ' + autre
                        + ' : un seul écrivain (AGENTS.md). Faire écrire la session propriétaire.'}}
                    decision = 'deny'
        # deny et ask jettent le contexte (refus du hook, ou refus au prompt).
        if sous_grok() and state is not None and decision not in ('deny', 'ask', 'defer'):
            state.mkdir(parents=True, exist_ok=True, mode=0o700)
            with (state / 'lock').open('a') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                rappel = prendre_ko(state / 'ko')
            if rappel:
                bloc = sortie.setdefault('hookSpecificOutput', {'hookEventName': 'PreToolUse'})
                bloc['additionalContext'] = rappel
        print(json.dumps(sortie, ensure_ascii=False))
        return
    if state is None:
        # Sans identifiant, aucun état global partagé entre conversations.
        print(json.dumps({'systemMessage': 'Hook commun : session_id absent, état non modifié.'}))
        return
    # Clé par session, pas par dossier : le cwd suit les cd de l'agent.
    state_root = state.parent
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    env = hook_env(state)
    jq = shutil.which('jq', path=env['PATH'])
    contexts, reasons, messages = [], [], []
    def collect(result):
        if result.get('decision') == 'block':
            reasons.append(result.get('reason', 'Contrôle non validé.'))
        ctx = result.get('hookSpecificOutput', {}).get('additionalContext')
        if ctx:
            contexts.append(ctx)
    with (state / 'lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        cwd = project_root(Path(data['cwd']))
        roots_file = state / 'roots'
        ko_file = state / 'ko'
        if event == 'SessionStart':
            purge_etats(state_root, state)
            if not jq:
                contexts.append(JQ_MISSING)
            alerte = harnais_degrade(state, registration_problems())
            if alerte:
                contexts.append(alerte)
        elif event == 'UserPromptSubmit':
            (state / 'turn-start').touch()
            roots_file.unlink(missing_ok=True)
            marqueur = state / 'garde-encours'
            if marqueur.is_file():
                marqueur.unlink()
                contexts.append(GARDE_INTERROMPUE)
            rafraichit_verrous(state, identity)
            alerte = harnais_degrade(state, registration_problems())
            if alerte:
                contexts.append(alerte)
            if ko_file.is_file() and not sous_grok():
                contexts.append('Contrôles restés KO au tour précédent, à signaler sans annoncer de validation :\n'
                                + ko_file.read_text()[:1500])
                ko_file.unlink()
            if not jq:
                contexts.append(JQ_MISSING)
            # Notification ou rapport d'agent : pas un message de l'auteur.
            elif not from_agent(data.get('prompt')):
                for name in PROMPT:
                    collect(run(name, data, env, 5))
        elif event == 'PostToolUse':
            deadline = time.monotonic() + POST_BUDGET
            for raw, path in paths(data):
                # Racine du fichier écrit, pas du cwd : une session lancée dans
                # le home peut écrire dans un projet par chemin absolu.
                marked = marked_root(raw.parent)
                if marked:
                    root = marked.resolve()
                elif path.is_relative_to(cwd) and not protected(cwd) and not conteneur_de_projets(cwd):
                    root = cwd
                else:
                    # Fichier isolé (/tmp, Téléchargements) : scan du fichier
                    # seul, jamais de gate Stop sur tout son dossier.
                    root = None
                if root is not None and (protected(root) or not path.is_relative_to(root)):
                    continue
                if root is None and in_config(path):
                    continue
                if root is not None:
                    remember(roots_file, root)
                if not jq:
                    contexts.append(JQ_MISSING)
                    continue
                where = root or path.parent
                item = dict(data, cwd=str(where), tool_input={'file_path': str(path)})
                avant_reasons, avant_contexts = len(reasons), len(contexts)
                # Le formateur du projet passe avant les contrôles.
                collect(run('gate-format-post', item, env, deadline=deadline))
                if script_shell(path):
                    collect(run('gate-shell-post', item, env, deadline=deadline))
                echecs = reasons[avant_reasons:] + [c for c in contexts[avant_contexts:] if 'KO' in c]
                collect(run('gate-cyber-post', item, env, deadline=deadline))
                note_qualite(state, path, echecs)
                if root is not None:
                    autre = autre_ecrivain(state, root.resolve(), identity)
                    if autre:
                        contexts.append('Écriture croisée sur ' + str(root.resolve())
                                        + ' : la session ' + autre + ' tient le dépôt (un seul '
                                          'écrivain, AGENTS.md). Faire écrire la session propriétaire.')
                    else:
                        ecrit_vivant(state, root.resolve(), identity)
        elif fin and data.get('reason') == 'end_turn':
            degrade = state / 'harnais-degrade'
            if degrade.is_file():
                reasons.append('Harnais dégradé : ' + degrade.read_text(encoding='utf-8')[:1500]
                               + '. Rétablir les hooks du moteur avant de clore le tour.')
            marqueur = state / 'garde-encours'
            if marqueur.is_file():
                marqueur.unlink()
                reasons.append(GARDE_INTERROMPUE)
            try:
                qualite = json.loads((state / 'qualite-ko.json').read_text(encoding='utf-8'))
            except (OSError, json.JSONDecodeError):
                qualite = {}
            if qualite:
                reasons.append('Contrôles de qualité restés KO — corriger puis rééditer chaque fichier '
                               'pour relancer son contrôle :\n'
                               + '\n'.join(f'{chemin} : {message}'
                                           for chemin, message in list(qualite.items())[:8]))
            # Un dossier de projets (Bureau) n'est pas un projet : seuls les projets écrits comptent.
            targets = ([] if conteneur_de_projets(cwd) else [cwd]) + [Path(line) for line in read_lines(roots_file)]
            deadline = time.monotonic() + STOP_BUDGET
            done = []
            verified = False
            for root in targets:
                if root in done or protected(root) or not root.is_dir():
                    continue
                done.append(root)
                # Tour sans modification (question, lecture) : rien à revérifier.
                if changed_since(root, state / 'turn-start'):
                    verified = True
                    if not jq:
                        reasons.append(JQ_MISSING)
                        break
                    item = dict(data, cwd=str(root))
                    for name in STOP:
                        collect(run(name, item, env, 120, deadline))
            changes = config_changes(state / 'turn-start')
            if changes is None:
                reasons.append('git status de la config a échoué : état invérifiable, la validation '
                               'de config ne peut pas être annoncée.')
            elif changes:
                # Le verifier ne lance que les contrôles que ces fichiers peuvent casser.
                item = dict(data, cwd=str(CONFIG), config_changes=changes)
                collect(run('gate-config-stop', item, env, CONFIG_GATE_TIMEOUT, deadline))
            if reasons:
                # Le repère ne bouge pas : la continuation revoit les mêmes fichiers.
                # Grok coupe au bout de 8 blocs. Le KO reste pour le tour d'après.
                ko_file.write_text('\n'.join(reasons))
            else:
                (state / 'turn-start').touch()
                roots_file.unlink(missing_ok=True)
                if verified:
                    ko_file.unlink(missing_ok=True)
        elif event == 'SessionEnd':
            (state / 'ended').touch()
            libere_verrous(state, identity)
    result = {}
    if contexts:
        result['hookSpecificOutput'] = {'hookEventName': event, 'additionalContext': '\n'.join(contexts)}
    if reasons:
        reason = '\n'.join(reasons)
        if fin:
            result.update(decision='block', reason=reason)
        elif event == 'PostToolUse':
            # Ajouter aux autres retours (cyber) au lieu de les écraser.
            text = '\n'.join(contexts + reasons)
            result['hookSpecificOutput'] = {'hookEventName': event, 'additionalContext': text}
        else:
            result['systemMessage'] = reason
    if messages:
        result['systemMessage'] = '\n'.join(messages)
    print(json.dumps(result, ensure_ascii=False))

def reponse_echec(error):
    raison = ('Hook commun en erreur (' + type(error).__name__
              + ') : contrôles non faits, ne pas annoncer de validation.')
    evenement = sys.argv[1] if len(sys.argv) > 1 else ''
    if evenement in ('Stop', 'SubagentStop'):
        return {'decision': 'block', 'reason': raison, 'systemMessage': raison}
    if evenement == 'PreToolUse':
        return {
            'decision': 'deny',
            'reason': raison,
            'systemMessage': raison,
            'hookSpecificOutput': {
                'hookEventName': 'PreToolUse',
                'permissionDecision': 'deny',
                'permissionDecisionReason': raison,
            },
        }
    return {'systemMessage': raison}


if __name__ == '__main__':
    for number in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
        signal.signal(number, stop_children)
    try:
        main()
    except Exception as error:
        # Code 0 : le client n'affiche le JSON que dans ce cas.
        print(json.dumps(reponse_echec(error), ensure_ascii=False))
