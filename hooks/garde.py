"""PreToolUse : confirmer une perte de travail local (rm, git), un disque, le firmware, un force-push
ou un git sans ses hooks ; refuser un secret."""
import base64
import glob
import os
import re
import shlex
import stat
from pathlib import Path

from garde_depot import GitIndisponible, danger_git, danger_rm

HOME = Path.home()
RACINES = ({Path('/'), Path('/home'), HOME, HOME / 'Bureau', HOME / 'Documents', HOME / '.agents',
            HOME / '.claude', HOME / '.ssh', HOME / '.gnupg', HOME / '.local', HOME / '.config'}
           | {Path('/', d) for d in ('bin', 'boot', 'etc', 'lib', 'lib64', 'opt', 'root', 'sbin',
                                     'srv', 'usr', 'var')})
SECRET = re.compile(r"\.credentials\.json|\.ssh/id_[\w-]+(?!\.pub)\b|\.git-credentials|\.netrc|\.pgpass"
                    r"|gh/hosts\.yml|\.aws/credentials"
                    r"|(?:^|[\s/'\"=<])\.env(?:\.(?!example|sample|template|dist)[\w.-]+)?(?=$|[\s'\";|&)>])")
LECTEURS = {'cat', 'less', 'more', 'head', 'tail', 'bat', 'batcat', 'grep', 'egrep', 'rg', 'sed', 'awk',
            'strings', 'xxd', 'od', 'hexdump', 'base64', 'cp', 'scp', 'rsync', 'curl', 'wget', 'nc',
            'jq', 'sort', 'uniq', 'tee', 'diff', 'vim', 'vi', 'nano', 'python', 'python3', 'node', 'perl',
            'source', '.'}
INTERPRETEURS = {'python', 'python3', 'node', 'perl', 'ruby', 'bash', 'sh'}
DRAPEAUX_EVAL = {
    'python': {'-c'},
    'python3': {'-c'},
    'node': {'-e', '--eval'},
    'perl': {'-e', '-E'},
    'ruby': {'-e'},
    'bash': {'-c', '--command'},
    'sh': {'-c', '--command'},
}
DRAPEAUX_VALEUR = {
    'python': {'-W', '-X', '-Q', '--check-hash-based-pycs'},
    'python3': {'-W', '-X', '-Q', '--check-hash-based-pycs'},
    'node': {'-r', '--require', '--import', '--loader', '--experimental-loader'},
    'perl': {'-I', '-M'},
    'ruby': {'-I', '-r'},
    'bash': {'-o'},
    'sh': {'-o'},
}
SANS_SCRIPT = {'python': {'-m'}, 'python3': {'-m'}}
HEXA = re.compile(r'\\x([0-9a-fA-F]{2})')
ASSEMBLAGES = (
    re.compile(r'''(['"])(.*?)\1\s*\+\s*(['"])(.*?)\3'''),
    re.compile(r'''(['"])(.*?)\1\s*\.\s*(['"])(.*?)\3'''),
    re.compile(r'''(['"])(.*?)\1\s*(?=['"])(['"])(.*?)\3'''),
    re.compile(r'''(['"])(.*?)\1\.concat\(\s*(['"])(.*?)\3\s*\)'''),
)
JETON_B64 = re.compile(r'(?<![A-Za-z0-9+/])([A-Za-z0-9+/]{4,}={0,2})(?![A-Za-z0-9+/=])')
CHR_CHAINE = re.compile(
    r'chr\(\s*\d{1,3}\s*\)(?:\s*\*\s*\d+)?'
    r'(?:\s*\+\s*chr\(\s*\d{1,3}\s*\)(?:\s*\*\s*\d+)?)+'
)
CHR_TERME = re.compile(r'chr\(\s*(\d{1,3})\s*\)(?:\s*\*\s*(\d+))?')
PLAFOND_CHR = 32
NOM_READ = 'read' + 'File'
OUVERTURE = re.compile(
    r'(?:\bopen|\b' + NOM_READ + r'(?:Sync)?|\.read_text|\bIO\.read|\bPath)\s*\(\s*[^)\'"\s]'
)
LECTURE_OUVERTE = re.compile(
    r'(?:\bopen|\b' + NOM_READ + r'(?:Sync)?|\bIO\.read|\bload_dotenv|\bdotenv_values)'
    r'\s*\(\s*[^)\'"\s]'
)
CHEMIN_ENV = re.compile(r'\bPath\s*\(\s*os\.(?:environ|getenv)')
LECTURE_PATH = re.compile(r'\.read_text\b|\.read_bytes\b|\.open\s*\(')
SOURCE_VARIABLE = re.compile(r'''(?:\bsource|(?<![\w.])\.)\s+['"]?\$(?!\()''')
EXEC_FIND = {'-exec', '-execdir', '-ok', '-okdir'}
DUREE_OU_VARIABLE = re.compile(r'^\w+=|^\d[\d.]*[smhd]?$')
SOUS_COMMANDE = re.compile(r'\$\(([^()]*)\)|`([^`]*)`')
MAX_GLOB = 50
TAILLE_SCRIPT = 256 * 1024
PREFIXES = {'sudo', 'doas', 'pkexec', 'env', 'command', 'exec', 'nice', 'nohup', 'time', 'timeout', 'xargs'}
OUTILS_DISQUE = {'dd', 'wipefs', 'fdisk', 'sfdisk', 'cfdisk', 'parted', 'gdisk', 'sgdisk', 'shred', 'blkdiscard',
                 'cp', 'tee', 'ddrescue', 'bmaptool', 'grub-install', 'grub2-install', 'limine'}
PERIPHERIQUE_DISQUE = r'/dev/(?:sd[a-z]|nvme\d|mmcblk\d|hd[a-z]|vd[a-z]|xvd[a-z]|mtd\d|disk/by-)'
DISQUE = re.compile(r'^(?:of=)?' + PERIPHERIQUE_DISQUE)
REDIRECTION_DISQUE = re.compile(r'>\s*' + PERIPHERIQUE_DISQUE)
LECTURE_EFI = {'-v', '--verbose', '-V', '--version', '-h', '--help'}
LECTURE_MOK = {'-h', '--help', '-l', '--list-enrolled', '-N', '--list-new', '--list-delete', '--sb-state',
               '--pk', '--kek', '--db', '--dbx', '--list-sbat-revocations', '--short', '--all', '-a',
               '--mok', '-m', '--mokx', '-X', '-t', '--test-key', '-x', '--export'}
ECRITURE_FLASHROM = ('--write', '--erase', '--wp-enable', '--wp-disable', '--wp-range', '--wp-region')
SOUS_COMMANDES_HOOKS = {'commit', 'push', 'merge', 'rebase', 'cherry-pick', 'am'}
OPTIONS_COMMIT_AVEC_VALEUR = {'-m', '--message', '-F', '--file', '-C', '--reuse-message', '-c', '--reedit-message',
                              '--author', '--date', '-t', '--template', '--fixup', '--squash', '--pathspec-from-file'}
LETTRES_COMMIT_AVEC_VALEUR = 'mFCctuS'
ACTIONS_FWUPD = {'install', 'local-install', 'update', 'upgrade', 'downgrade', 'reinstall', 'switch-branch',
                 'unlock', 'activate', 'set-bios-setting', 'security-fix', 'security-undo', 'sync', 'sync-bkc',
                 'verify-update', 'report-devices', 'report-history'}


def decision(kind, raison):
    return {'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': kind,
                                   'permissionDecisionReason': raison}}


def sous_commandes(commande):
    yield commande
    for dollar, backtick in SOUS_COMMANDE.findall(commande):
        yield dollar or backtick


def segments(commande):
    textes = (t for c in sous_commandes(commande) for t in re.split(r'\|\||&&|[;|&\n]', c))
    for texte in textes:
        try:
            mots = shlex.split(texte)
        except ValueError:
            mots = texte.split()
        while mots and (mots[0] in PREFIXES or mots[0].startswith('-')
                        or DUREE_OU_VARIABLE.match(mots[0])):
            mots.pop(0)
        if mots:
            yield os.path.basename(mots[0]), mots[1:], texte


def cible(mot, cwd):
    mot = re.sub(r'^(?:~|\$HOME|\$\{HOME\})(?=/|$)', str(HOME), mot)
    while len(mot) > 1 and mot.endswith(('/*', '/.', '/')):
        mot = (mot[:-2] if mot[-1] in '*.' else mot[:-1]) or '/'
    if mot == '*':
        mot = '.'
    return Path(os.path.normpath(os.path.join(cwd, mot)))


def recursif(args):
    return any(a == '--recursive' or (a.startswith('-') and not a.startswith('--') and 'r' in a.lower())
               for a in args)


def touche_firmware(prog, args):
    options = [a for a in args if a.startswith('-')]
    if prog == 'flashrom':
        return any(a in ('-w', '-E') or a.startswith(ECRITURE_FLASHROM) for a in args)
    if prog == 'fwupdmgr':
        return bool(ACTIONS_FWUPD.intersection(args))
    if prog == 'efibootmgr':
        return any(a not in LECTURE_EFI for a in options)
    if prog == 'mokutil':
        return any(a not in LECTURE_MOK for a in options)
    return False


def ecrit_disque(prog, args, texte):
    if REDIRECTION_DISQUE.search(texte):
        return True
    if prog.startswith('python') and args:
        prog, args = os.path.basename(args[0]), args[1:]
    if prog in ('ecrire-image', 'ecrire_image.py'):
        return '--ecrire' in args
    return (prog in OUTILS_DISQUE or prog.startswith('mkfs')) and any(DISQUE.match(a) for a in args)


def concatene(texte):
    precedent = None
    courant = texte
    for _ in range(8):
        if courant == precedent:
            break
        precedent = courant
        for motif in ASSEMBLAGES:
            courant = motif.sub(
                lambda mot: mot.group(1) + mot.group(2) + mot.group(4) + mot.group(1), courant)
    return courant


def decodages(texte):
    clairs = []
    for trouve in JETON_B64.finditer(texte):
        jeton = trouve.group(1)
        if len(jeton) % 4:
            continue
        try:
            clair = base64.b64decode(jeton, validate=True).decode('utf-8')
        except (ValueError, UnicodeDecodeError):
            continue
        clairs.append(clair)
    return clairs


def deplie_chr(texte):
    def chaine(mot):
        chars = []
        for code, fois in CHR_TERME.findall(mot.group(0)):
            nombre = min(int(fois) if fois else 1, PLAFOND_CHR)
            if nombre == 0:
                continue
            chars.append(chr(int(code)) * nombre)
        clair = ''.join(chars)
        if not clair or "'" in clair or '\\' in clair:
            return clair or "''"
        return "'" + clair + "'"

    return CHR_CHAINE.sub(chaine, texte)


def morceaux_clairs(texte):
    substitue = HEXA.sub(lambda mot: chr(int(mot.group(1), 16)), deplie_chr(texte))
    return substitue, concatene(substitue)


def indices_caches(texte):
    substitue, joint = morceaux_clairs(texte)
    return '\n'.join((substitue, joint, *decodages(substitue), *decodages(joint)))


def lit_secret(prog, args, texte):
    lecteur = (prog in LECTEURS or prog in INTERPRETEURS
               or (prog == 'find' and bool(EXEC_FIND.intersection(args))))
    return lecteur and bool(SECRET.search(texte))


def secret_cache(prog, texte):
    if prog not in LECTEURS and prog not in INTERPRETEURS:
        return False
    cache = indices_caches(texte)
    return cache != texte and bool(SECRET.search(cache)) and not SECRET.search(texte)


def lecture_dynamique(prog, args, texte):
    if prog not in INTERPRETEURS or not DRAPEAUX_EVAL.get(prog, ()).intersection(args):
        return False
    if SECRET.search(texte) or SECRET.search(indices_caches(texte)):
        return False
    return bool(OUVERTURE.search(texte) or SOURCE_VARIABLE.search(texte))


def cibles_rm(args, cwd):
    for mot in args:
        if mot.startswith('-'):
            continue
        chemin = cible(mot, cwd)
        if re.search(r'[*?[]', str(chemin)):
            yield from (Path(c) for c in sorted(glob.glob(str(chemin)))[:MAX_GLOB])
        else:
            yield chemin


def raison_rm(args, cwd):
    for chemin in cibles_rm(args, cwd):
        if chemin in RACINES or chemin.resolve() in RACINES:
            return 'rm récursif sur ' + str(chemin)
        danger = danger_rm(chemin.resolve())
        if danger:
            return 'rm récursif sur ' + str(chemin) + ' (' + danger + ')'
    return None


def sans_verify(mot):
    return mot.startswith('--no-v') and '--no-verify'.startswith(mot)


def commit_sans_hooks(args):
    saute = False
    for mot in args:
        if saute or mot in OPTIONS_COMMIT_AVEC_VALEUR:
            saute = not saute
        elif mot == '--':
            return False
        elif sans_verify(mot):
            return True
        elif mot.startswith('-') and not mot.startswith('--'):
            lettres = mot[1:]
            if 'n' in lettres.split(next((c for c in lettres if c in LETTRES_COMMIT_AVEC_VALEUR), '\0'))[0]:
                return True
    return False


def git_sans_hooks(args):
    if any(a.lower().startswith('core.hookspath=') for a in args):
        return True
    sous_commande = next((a for a in args if a in SOUS_COMMANDES_HOOKS), None)
    if sous_commande is None:
        return False
    reste = args[args.index(sous_commande) + 1:]
    return commit_sans_hooks(reste) if sous_commande == 'commit' else any(sans_verify(a) for a in reste)


def raison_git(args, cwd):
    if git_sans_hooks(args):
        return 'git sans ses hooks (--no-verify, core.hooksPath) : les contrôles du dépôt seraient contournés'
    if 'push' in args and any(a in ('-f', '--force') or a.startswith(('--force', '+')) for a in args):
        return 'Force-push : réécrit l\'historique distant'
    danger = danger_git(args, cwd)
    return 'git : ' + danger if danger else None


def raison_confirmation(prog, args, texte, cwd):
    if prog == 'rm' and recursif(args):
        return raison_rm(args, cwd)
    if ecrit_disque(prog, args, texte):
        return 'Écriture directe sur un disque : vérifier la cible'
    if touche_firmware(prog, args):
        return 'Firmware (flash, variables EFI, clés, rapport envoyé) : irréversible hors du projet'
    if prog == 'git':
        return raison_git(args, cwd)
    return None


def apres_cd(args, cwd):
    if not args:
        return str(HOME)
    return cwd if args[0] == '-' else str(cible(args[0], cwd))


def fichiers_module(nom):
    if not nom or '/' in nom or '\\' in nom or '..' in nom or nom.startswith('-'):
        return []
    if not re.fullmatch(r'[A-Za-z_][\w.]*', nom):
        return []
    relatif = nom.replace('.', '/')
    return [relatif + '.py', relatif + '/__main__.py']


def candidats_script(prog, args):
    valeur = DRAPEAUX_VALEUR.get(prog, ())
    sans = SANS_SCRIPT.get(prog, ())
    evaluation = DRAPEAUX_EVAL.get(prog, ())
    fin_options = False
    index = 0
    candidats = []
    while index < len(args):
        mot = args[index]
        if mot == '--' and not fin_options:
            fin_options = True
            index += 1
            continue
        if not fin_options and mot in evaluation:
            index += 2
            continue
        if not fin_options and mot in sans:
            index += 1
            if index < len(args):
                candidats.extend(fichiers_module(args[index]))
                index += 1
            continue
        if not fin_options and mot in valeur:
            index += 1
            if index < len(args):
                candidats.append(args[index])
                index += 1
            continue
        if not fin_options and mot.startswith('-'):
            index += 1
            continue
        candidats.append(mot)
        index += 1
    return candidats


LECTURE_MOT = re.compile(
    r'\b(?:open|' + NOM_READ + r'(?:Sync)?|read_text|load_dotenv|dotenv_values|source)\b'
)
SOURCE_POINT = re.compile(r'(?<![\w.])\.\s+[\'"]?[^\n;|&]*$')


def index_point(match):
    relatif = match.group().find('.')
    return match.start() + max(relatif, 0)


def lecture_pres(morceau, debut_nom, fin_nom):
    avant = morceau[max(0, debut_nom - 80):debut_nom]
    if SOURCE_POINT.search(avant):
        return True
    bas = max(0, debut_nom - 80)
    haut = min(len(morceau), fin_nom + 80)
    return bool(LECTURE_MOT.search(morceau[bas:haut]))


def secret_lu(texte):
    substitue, joint = morceaux_clairs(texte)
    for morceau in (substitue, joint):
        for match in SECRET.finditer(morceau):
            if lecture_pres(morceau, index_point(match), match.end()):
                return True
        for trouve in JETON_B64.finditer(morceau):
            jeton = trouve.group(1)
            if len(jeton) % 4:
                continue
            try:
                clair = base64.b64decode(jeton, validate=True).decode('utf-8')
            except (ValueError, UnicodeDecodeError):
                continue
            if SECRET.search(clair) and lecture_pres(morceau, trouve.start(), trouve.end()):
                return True
            if secret_clair(clair):
                return True
    return False


def secret_clair(clair):
    for match in SECRET.finditer(clair):
        if lecture_pres(clair, index_point(match), match.end()):
            return True
    return False


LECTURE_ATTRIBUT = re.compile(
    r'(?:Path\s*\(\s*(?P<interieur>[^)]*?)\s*\)|(?P<nom>[A-Za-z_]\w*))'
    r'\s*\.\s*(?:read_text|read_bytes)\s*\('
)


def lecture_attribut(texte):
    for match in LECTURE_ATTRIBUT.finditer(texte):
        interieur = match.group('interieur')
        if interieur is None:
            return True
        corps = interieur.strip()
        if corps == '__file__':
            continue
        if len(corps) >= 2 and corps[0] == corps[-1] and corps[0] in '"\'':
            continue
        return True
    return False


def lecture_ouverte(texte):
    if LECTURE_OUVERTE.search(texte) or lecture_attribut(texte):
        return True
    for match in CHEMIN_ENV.finditer(texte):
        if LECTURE_PATH.search(texte[match.end():match.end() + 120]):
            return True
    return False


def scripts_exempts():
    dossier = Path(__file__).resolve().parent
    noms = ('verify.py', 'dispatch.py', 'garde.py', 'garde_depot.py', 'oracle_vide.py')
    return {dossier / nom for nom in noms} | {dossier.parent / 'verifier'}


def exempte_scan(resolu):
    return resolu in scripts_exempts()


def lit_brut(chemin, taille):
    try:
        with chemin.open('rb') as fichier:
            return fichier.read(taille)
    except OSError:
        return None


def avis_contenu(brut, trop_gros):
    if brut is None:
        return 'ask'
    texte = brut.decode('utf-8', errors='replace')
    if secret_lu(texte):
        return 'deny'
    if trop_gros or b'\0' in brut[:512]:
        return 'ask'
    if lecture_ouverte(texte) or SOURCE_VARIABLE.search(texte):
        return 'ask'
    return None


def avis_un_script(mot, cwd):
    chemin = cible(mot, cwd)
    try:
        info = chemin.stat()
        resolu = chemin.resolve()
    except OSError:
        return None
    if SECRET.search(str(chemin)) or SECRET.search(str(resolu)):
        return 'deny'
    if exempte_scan(resolu) or not stat_fichier(info) or info.st_size == 0:
        return None
    trop_gros = info.st_size > TAILLE_SCRIPT
    return avis_contenu(lit_brut(chemin, TAILLE_SCRIPT), trop_gros)


def avis_script(prog, args, cwd):
    if prog not in INTERPRETEURS:
        return None
    resultat = None
    for mot in candidats_script(prog, args):
        avis = avis_un_script(mot, cwd)
        if avis == 'deny':
            return 'deny'
        if avis == 'ask':
            resultat = 'ask'
    return resultat


def stat_fichier(info):
    return stat.S_ISREG(info.st_mode)


def verdict_bash(commande, cwd):
    for prog, args, texte in segments(commande):
        if prog == 'cd':
            cwd = apres_cd(args, cwd)
            continue
        avis = avis_script(prog, args, cwd)
        if lit_secret(prog, args, texte) or secret_cache(prog, texte) or avis == 'deny':
            return decision('deny', 'Commande qui lit ou copie un fichier de secrets, refusée (AGENTS.md). '
                                    'Si c\'est voulu, l\'auteur la lance lui-même.')
        if avis == 'ask' or lecture_dynamique(prog, args, texte):
            return decision('ask', 'Interpréteur qui ouvre un fichier sans chemin littéral, '
                                   'ou script trop gros ou illisible : confirmation de l\'auteur.')
        try:
            raison = raison_confirmation(prog, args, texte, cwd)
        except GitIndisponible:
            raison = 'git ne répond pas, impossible de vérifier ce qui serait perdu'
        if raison:
            return decision('ask', raison + ' : confirmation de l\'auteur.')
    return {}


def chemin_secret(entree, cles):
    for cle in cles:
        valeur = entree.get(cle)
        if isinstance(valeur, str) and SECRET.search(valeur):
            return True
    return False


CLES_CHEMIN = {
    'path', 'file', 'file_path', 'target_file', 'notebook_path', 'snapshot_path',
    'output_directory', 'device_path', 'filename', 'uri',
}
PROFONDEUR_CHEMIN = 32


def cle_de_chemin(cle):
    brut = str(cle)
    snake = re.sub(r'(?<!^)(?=[A-Z])', '_', brut).lower()
    for nom in (brut.lower(), snake):
        if nom in CLES_CHEMIN or nom.endswith(('_path', '_file', '_directory', '_dir')):
            return True
    return False


def chemin_avec_espaces(valeur):
    texte = valeur.strip()
    if len(texte) >= 2 and texte[0] == texte[-1] and texte[0] in '"\'':
        texte = texte[1:-1].strip()
    for trouve in SECRET.finditer(texte):
        if texte[trouve.end():].strip():
            continue
        avant = texte[:trouve.start()].rstrip()
        debut = texte[trouve.start():trouve.start() + 1]
        if not avant or debut in '/\\' or avant.endswith(('/', '\\')):
            return True
    return False


def valeur_secrete(cle, valeur):
    if not isinstance(valeur, str) or not SECRET.search(valeur):
        return False
    if cle_de_chemin(cle):
        return True
    corps = valeur.strip()
    if corps.startswith(('/', '~/', './', '../')):
        return True
    if any(caractere.isspace() for caractere in valeur):
        return chemin_avec_espaces(valeur)
    return valeur.startswith(('/', '~', '.')) or '/' in valeur


def contient_chemin_secret(entree, cle='', profondeur=0):
    if profondeur > PROFONDEUR_CHEMIN:
        return True
    if isinstance(entree, str):
        return valeur_secrete(cle, entree)
    if isinstance(entree, dict):
        return any(contient_chemin_secret(valeur, nom, profondeur + 1) for nom, valeur in entree.items())
    if isinstance(entree, (list, tuple)):
        return any(contient_chemin_secret(valeur, cle, profondeur + 1) for valeur in entree)
    return False


OUTILS_FICHIERS = {'Read', 'Grep', 'Write', 'Edit', 'NotebookEdit'}
OUTILS_ECRITURE = {'Write', 'Edit', 'NotebookEdit'}


def refus_secret(ecriture):
    if ecriture:
        motif = 'Écriture d\'un fichier de secrets refusée (AGENTS.md). '
    else:
        motif = 'Lecture d\'un fichier de secrets refusée (AGENTS.md). '
    return decision('deny', motif + 'Si c\'est voulu, l\'auteur le lance lui-même.')


def verdict(tool, entree, cwd):
    if tool in OUTILS_FICHIERS:
        cles = ('file_path', 'path', 'target_file', 'notebook_path')
        if tool in ('Read', 'Grep'):
            cles = cles + ('glob',)
        if chemin_secret(entree, cles):
            return refus_secret(tool in OUTILS_ECRITURE)
    commande = entree.get('command')
    if tool == 'Bash' and isinstance(commande, str):
        return verdict_bash(commande, cwd)
    if contient_chemin_secret(entree):
        return refus_secret(tool in OUTILS_ECRITURE)
    return {}
