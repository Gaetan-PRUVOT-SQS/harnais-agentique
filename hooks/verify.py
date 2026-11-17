import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HOOKS = ROOT if (ROOT / 'dispatch.py').exists() else ROOT / 'hooks'
# Faux projets hors ~/.agents. Un dossier par processus : deux verifiers
# en parallèle ne partagent pas les fixtures, et la fin n'efface que le sien.
RACINE_FIXTURES = Path.home() / '.cache' / 'agent-hooks-tests'
FIXTURES = RACINE_FIXTURES / str(os.getpid())


class Hooks(unittest.TestCase):
    def setUp(self):
        self.path = FIXTURES / self._testMethodName
        shutil.rmtree(self.path, ignore_errors=True)
        self.path.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, self.path, True)
        self.project = self.path / 'project'
        self.project.mkdir()
        self.env = os.environ.copy()
        self.env['AGENT_HOOK_STATE_ROOT'] = str(self.path / 'state')
        self.env['TMPDIR'] = str(self.path)
        self.env['PYTHONDONTWRITEBYTECODE'] = '1'
        self.config = self.path / 'config'
        self.env['AGENT_CONFIG_ROOT'] = str(self.config)
        self.env.pop('GROK_HOOK_EVENT', None)
        # Enregistrement moteur sain et isolé : les tests ne dépendent pas
        # des moteurs réellement posés sur le poste.
        self.moteur = self.path / 'moteur.json'
        self.env['AGENT_MOTEUR_HOOKS'] = str(self.moteur)
        self.saine = {'hooks': {'enabled': True, 'events': {
            evenement: [{'hooks': [{'type': 'command',
                                    'command': 'python3 -E -s ' + str(HOOKS / 'dispatch.py')
                                              + ' ' + evenement}]}]
            for evenement in ('SessionStart', 'UserPromptSubmit', 'PreToolUse',
                              'PostToolUse', 'Stop')}}}
        self.moteur.write_text(json.dumps(self.saine), encoding='utf-8')
        self.etat = self.path / 'state' / hashlib.sha256(b'nativetest-session').hexdigest()[:24]

    def call(self, event, **values):
        payload = {'session_id': 'test-session', 'cwd': str(self.project)}
        payload.update(values)
        process = subprocess.run(['python3', str(HOOKS / 'dispatch.py'), event],
                                 input=json.dumps(payload), text=True, capture_output=True,
                                 env=self.env, cwd=self.project, timeout=30, check=False)
        self.assertEqual(process.returncode, 0, process.stderr)
        return json.loads(process.stdout)

    def test_prompt_sans_mode_injecte(self):
        (self.project / '.mode-etudiant').touch()
        for prompt, mode in (('projet perso', 'default'), ('projet de devoir', 'auto'),
                             ('Bonjour', 'bypassPermissions')):
            self.assertEqual(self.call('UserPromptSubmit', prompt=prompt, permission_mode=mode), {}, prompt)
        self.call('SessionStart', source='compact')
        self.assertEqual(self.call('UserPromptSubmit', prompt='continue'), {})

    def test_scan_ne_divulgue_pas_la_ligne(self):
        (self.project / 'bad.js').write_text('eval("contenu-confidentiel");\n')
        result = self.call('PostToolUse', tool_input={'path': 'bad.js'})
        self.assertNotIn('contenu-confidentiel', json.dumps(result))

    def test_stop_claude_sans_reason(self):
        (self.project / 'bad.js').write_text('eval("x");\n')
        result = self.call('Stop')
        self.assertEqual(result['decision'], 'block')
        self.assertIn('sécu', result['reason'])

    def test_continuation_rouge_rebloque(self):
        (self.project / 'bad.js').write_text('eval("x");\n')
        result = self.call('Stop', stop_hook_active=True)
        self.assertEqual(result.get('decision'), 'block')
        self.assertIn('sécu', result['reason'])

    def test_stop_projet_sain_sans_suite(self):
        (self.project / 'main.js').write_text('const x = 1;\n')
        self.assertEqual(self.call('Stop'), {})

    def test_lien_hors_projet_ignore(self):
        external = self.path / 'outside.js'
        external.write_text('eval("x");\n')
        (self.project / 'link.js').symlink_to(external)
        self.assertEqual(self.call('PostToolUse', tool_input={'path': 'link.js'}), {})

    def test_test_runner_dans_le_projet(self):
        (self.project / 'node_modules').mkdir()
        (self.project / 'package.json').write_text(json.dumps({'scripts': {
            'test': "node -e \"require('fs').writeFileSync('test-created.txt', 'ok')\""}}))
        result = subprocess.run(['python3', str(HOOKS / 'lanceur.py'), '--dir', str(self.project)],
                                capture_output=True, text=True, env=self.env, timeout=60, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.project / 'test-created.txt').read_text(), 'ok')

    def test_makefile_garde_la_regression(self):
        (self.project / 'Makefile').write_text('up:\n\tdocker compose up\n')
        (self.project / 'node_modules').mkdir()
        (self.project / 'package.json').write_text(json.dumps({'scripts': {'test': 'exit 1'}}))
        result = self.call('Stop')
        self.assertEqual(result.get('decision'), 'block')
        self.assertIn('Régression', result['reason'])

    def test_make_test_side_project(self):
        (self.project / '.mode-side-project').touch()
        (self.project / 'kernel.c').write_text('void\tkmain(void)\n{\n}\n')
        (self.project / 'Makefile').write_text('test:\n\t@echo boot KO; exit 1\n')
        result = self.call('Stop')
        self.assertEqual(result.get('decision'), 'block')
        self.assertIn('boot KO', result['reason'])
        (self.project / 'Makefile').write_text('test:\n\t@echo boot OK\n')
        self.assertEqual(self.call('Stop'), {})

    def test_make_test_rapide_prefere(self):
        (self.project / '.mode-side-project').touch()
        (self.project / 'kernel.c').write_text('void\tkmain(void)\n{\n}\n')
        (self.project / 'Makefile').write_text('test:\n\t@echo complet KO; exit 1\n'
                                               'test-rapide:\n\t@echo rapide OK\n')
        self.assertEqual(self.call('Stop'), {})
        (self.project / 'Makefile').write_text('test:\n\t@echo complet OK\n'
                                               'test-rapide:\n\t@echo rapide KO; exit 1\n')
        result = self.call('Stop')
        self.assertEqual(result.get('decision'), 'block')
        self.assertIn('rapide KO', result['reason'])

    def test_script_npm_init_ignore(self):
        (self.project / 'package.json').write_text(json.dumps({'scripts': {
            'test': 'echo "Error: no test specified" && exit 1'}}))
        self.assertEqual(self.call('Stop'), {})

    def test_scan_php_django(self):
        (self.project / 'a.php').write_text('<?php echo shell_exec($cmd);\n')
        (self.project / 'b.py').write_text('html = mark_safe(texte)\n')
        (self.project / 'c.html').write_text('<p>{{ texte|safe }}</p>\n')
        result = subprocess.run(['bash', str(HOOKS / 'cyber-scan.sh'), str(self.project)],
                                capture_output=True, text=True, timeout=30, check=False)
        self.assertEqual(result.returncode, 1)
        for name in ('a.php:1', 'b.py:1', 'c.html:1'):
            self.assertIn(name, result.stdout)

    def test_innerhtml_vide_ignore(self):
        (self.project / 'a.js').write_text("liste.innerHTML = '';\nregex.exec(texte);\n")
        result = subprocess.run(['bash', str(HOOKS / 'cyber-scan.sh'), str(self.project)],
                                capture_output=True, text=True, timeout=30, check=False)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_session_start_sans_regle_injectee(self):
        self.assertEqual(self.call('SessionStart', source='startup'), {})

    def test_prompt_silencieux_dans_le_home(self):
        env = dict(self.env, HOME=str(self.path))
        payload = {'session_id': 'home', 'cwd': str(self.path), 'prompt': 'evalue mon workflow'}
        process = subprocess.run(['python3', str(HOOKS / 'dispatch.py'), 'UserPromptSubmit'],
                                 input=json.dumps(payload), text=True, capture_output=True,
                                 env=env, cwd=self.path, timeout=30, check=False)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout), {})

    def test_cyber_ignore(self):
        (self.project / 'a.js').write_text('eval("x");\nnew Function("y");\n')
        (self.project / 'lib').mkdir()
        (self.project / 'lib' / 'b.py').write_text('os.system(cmd)\n')
        (self.project / '.cyber-ignore').write_text('# justifié\na.js:1\nlib/\n')
        result = subprocess.run(['bash', str(HOOKS / 'cyber-scan.sh'), str(self.project)],
                                capture_output=True, text=True, timeout=30, check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn('a.js:2', result.stdout)
        self.assertNotIn('a.js:1', result.stdout)
        self.assertNotIn('b.py', result.stdout)

    def test_cyber_ignore_fichier_post(self):
        (self.project / 'a.js').write_text('eval("x");\n')
        (self.project / '.cyber-ignore').write_text('a.js\n')
        self.assertEqual(self.call('PostToolUse', tool_input={'file_path': 'a.js'}), {})

    def test_stop_ignore_ancien_motif(self):
        old = self.project / 'ancien.js'
        old.write_text('eval("x");\n')
        os.utime(old, (1, 1))
        (self.project / 'Makefile').write_text('test:\n\ttrue\n')
        self.call('UserPromptSubmit', prompt='projet perso')
        (self.project / 'nouveau.js').write_text('const x = 1;\n')
        self.assertEqual(self.call('Stop'), {})

    def test_stop_bloque_motif_du_tour(self):
        self.call('UserPromptSubmit', prompt='projet perso')
        (self.project / 'nouveau.js').write_text('eval("x");\n')
        result = self.call('Stop')
        self.assertEqual(result.get('decision'), 'block')
        self.assertIn('nouveau.js:1', result['reason'])

    def test_regex_sans_faux_positifs(self):
        (self.project / 'a.c').write_text('fgets(buf, 10, f);\nft_printf(str);\nx = retrieval(a);\n')
        (self.project / 'b.py').write_text('y = yaml.load(f, Loader=yaml.SafeLoader)\nString.raw(x)\n')
        (self.project / 'c.php').write_text('<?php $s = sprintf("%d", 1);\n')
        result = subprocess.run(['bash', str(HOOKS / 'cyber-scan.sh'), str(self.project)],
                                capture_output=True, text=True, timeout=30, check=False)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_regex_vrais_positifs(self):
        (self.project / 'a.c').write_text('gets(buf);\nsystem(cmd);\nprintf(str);\n')
        result = subprocess.run(['bash', str(HOOKS / 'cyber-scan.sh'), str(self.project)],
                                capture_output=True, text=True, timeout=30, check=False)
        for name in ('a.c:1', 'a.c:2', 'a.c:3'):
            self.assertIn(name, result.stdout)

    def test_dossier_racine_nomme_build(self):
        root = self.path / 'build'
        root.mkdir()
        (root / 'a.js').write_text('eval("x");\n')
        result = subprocess.run(['bash', str(HOOKS / 'cyber-scan.sh'), str(root)],
                                capture_output=True, text=True, timeout=30, check=False)
        self.assertIn('a.js:1', result.stdout)

    def test_dependances_absentes_signalees_une_fois(self):
        (self.project / 'package.json').write_text(json.dumps({'scripts': {'test': 'exit 1'}}))
        first = self.call('Stop')
        self.assertEqual(first.get('decision'), 'block')
        self.assertIn('node_modules', first['reason'])
        self.assertEqual(self.call('Stop'), {})

    def test_marqueur_side_project_fixe_la_racine(self):
        (self.project / '.mode-side-project').touch()
        (self.project / 'bad.js').write_text('eval("x");\n')
        sub = self.project / 'src'
        sub.mkdir()
        result = self.call('Stop', cwd=str(sub))
        self.assertEqual(result.get('decision'), 'block')
        self.assertIn('bad.js:1', result['reason'])

    def test_stop_a_la_racine_du_projet(self):
        (self.project / '.git').mkdir()
        (self.project / 'bad.js').write_text('eval("x");\n')
        sub = self.project / 'src'
        sub.mkdir()
        result = self.call('Stop', cwd=str(sub))
        self.assertEqual(result.get('decision'), 'block')
        self.assertIn('bad.js:1', result['reason'])

    def test_prompt_silencieux_dans_la_config(self):
        env = dict(self.env, HOME=str(self.path))
        conf = self.path / '.agents'
        conf.mkdir()
        payload = {'session_id': 'conf', 'cwd': str(conf), 'prompt': 'projet perso'}
        process = subprocess.run(['python3', str(HOOKS / 'dispatch.py'), 'UserPromptSubmit'],
                                 input=json.dumps(payload), text=True, capture_output=True,
                                 env=env, cwd=conf, timeout=30, check=False)
        self.assertEqual(json.loads(process.stdout), {})

    def scan(self, target=None):
        return subprocess.run(['bash', str(HOOKS / 'cyber-scan.sh'), str(target or self.project)],
                              capture_output=True, text=True, timeout=60, errors='replace', check=False)

    def test_troncature_apres_exceptions(self):
        (self.project / 'aaa').mkdir()
        for i in range(60):
            (self.project / 'aaa' / f'{i}.js').write_text('eval("x");\n')
        (self.project / 'c.js').write_text('eval("x");\n')
        (self.project / '.cyber-ignore').write_text('aaa/\n')
        result = self.scan()
        self.assertEqual(result.returncode, 1)
        self.assertIn('c.js:1', result.stdout)

    def test_session_dans_le_home_fichier_absolu(self):
        env = dict(self.env, HOME=str(self.path))
        (self.project / '.git').mkdir()
        bad = self.project / 'a.js'
        bad.write_text('eval("x");\n')
        payload = {'session_id': 'home', 'cwd': str(self.path),
                   'tool_input': {'file_path': str(bad)}}
        out = subprocess.run(['python3', str(HOOKS / 'dispatch.py'), 'PostToolUse'],
                             input=json.dumps(payload), text=True, capture_output=True,
                             env=env, cwd=self.path, timeout=30, check=False)
        self.assertIn('a.js:1', out.stdout)
        payload.pop('tool_input')
        out = subprocess.run(['python3', str(HOOKS / 'dispatch.py'), 'Stop'],
                             input=json.dumps(payload), text=True, capture_output=True,
                             env=env, cwd=self.path, timeout=30, check=False)
        self.assertEqual(json.loads(out.stdout).get('decision'), 'block')

    def test_latin1_detecte(self):
        (self.project / 'a.php').write_bytes(b'<?php eval($x); // caf\xe9\n')
        self.assertIn('a.php:1', self.scan().stdout)

    def test_ignore_crlf_et_bom(self):
        (self.project / 'a.js').write_text('eval("x");\n')
        (self.project / 'b.js').write_text('eval("x");\n')
        (self.project / '.cyber-ignore').write_bytes(b'\xef\xbb\xbfa.js\r\nb.js\r\n')
        self.assertEqual(self.scan().returncode, 0)

    def test_venv_nomme_env_ignore(self):
        lib = self.project / 'env' / 'lib' / 'python3' / 'site-packages'
        lib.mkdir(parents=True)
        (lib / 'x.py').write_text('exec(code)\n')
        self.assertEqual(self.scan().returncode, 0)

    def test_motifs_objet(self):
        (self.project / 'a.py').write_text('os.popen(cmd)\n')
        (self.project / 'b.js').write_text('child_process.exec(cmd)\n')
        out = self.scan().stdout
        self.assertIn('a.py:1', out)
        self.assertIn('b.js:1', out)

    def test_nom_de_fichier_avec_deux_points(self):
        (self.project / 'a:b.js').write_text('const x = 1;\neval("x");\n')
        self.assertIn('a:b.js:2', self.scan().stdout)

    def test_fichier_deplace_pendant_le_tour(self):
        src = self.path / 'ailleurs.js'
        src.write_text('eval("x");\n')
        os.utime(src, (1, 1))
        self.call('UserPromptSubmit', prompt='go')
        os.rename(src, self.project / 'deplace.js')
        result = self.call('Stop')
        self.assertEqual(result.get('decision'), 'block')

    def test_rapport_agent_sans_declencheur(self):
        prompt = 'Another Claude session sent a message: dataset sft tool call dataset'
        result = self.call('UserPromptSubmit', prompt=prompt)
        self.assertEqual(result, {})

    def test_payload_non_objet(self):
        for raw in ('null', '[]', '123'):
            out = subprocess.run(['python3', str(HOOKS / 'dispatch.py'), 'Stop'],
                                 input=raw, text=True, capture_output=True,
                                 env=self.env, cwd=self.project, timeout=30, check=False)
            self.assertIn('systemMessage', json.loads(out.stdout))

    def test_fichier_isole_ne_devient_pas_racine(self):
        env = dict(self.env, HOME=str(self.path))
        loose = self.path / 'vrac'
        (loose / 'sous').mkdir(parents=True)
        note = loose / 'note.py'
        note.write_text('x = 1\n')
        base = {'session_id': 'vrac', 'cwd': str(self.path)}
        for event, extra in (('UserPromptSubmit', {'prompt': 'go'}),
                             ('PostToolUse', {'tool_input': {'file_path': str(note)}}),
                             ('Stop', {})):
            if event == 'Stop':
                # Un autre programme écrit dans le même dossier pendant le tour.
                (loose / 'sous' / 'autre.js').write_text('eval("x");\n')
            out = subprocess.run(['python3', str(HOOKS / 'dispatch.py'), event],
                                 input=json.dumps(dict(base, **extra)), text=True,
                                 capture_output=True, env=env, cwd=self.path, timeout=30, check=False)
        self.assertEqual(json.loads(out.stdout), {})

    def test_dossier_lien_au_dessus_du_projet(self):
        env = dict(self.env, HOME=str(self.path))
        (self.project / '.git').mkdir()
        (self.project / 'a.js').write_text('eval("x");\n')
        link = self.path / 'raccourci'
        link.symlink_to(self.project)
        payload = {'session_id': 'lien', 'cwd': str(self.path),
                   'tool_input': {'file_path': str(link / 'a.js')}}
        out = subprocess.run(['python3', str(HOOKS / 'dispatch.py'), 'PostToolUse'],
                             input=json.dumps(payload), text=True, capture_output=True,
                             env=env, cwd=self.path, timeout=30, check=False)
        self.assertIn('a.js:1', out.stdout)

    def test_pytest_sans_collecte_bloque(self):
        if not shutil.which('pytest'):
            self.skipTest('pytest absent')
        (self.project / 'pyproject.toml').write_text('[project]\nname = "x"\n')
        result = self.call('Stop')
        self.assertEqual(result.get('decision'), 'block', result)
        self.assertIn('tests non collectés', result['reason'])
        self.assertNotIn('aucun lanceur', result['reason'])

    def test_pytest_un_echec_bloque(self):
        if not shutil.which('pytest'):
            self.skipTest('pytest absent')
        (self.project / 'pyproject.toml').write_text('[project]\nname = "x"\n')
        (self.project / 'test_ko.py').write_text('def test_ko():\n    raise AssertionError("suite KO")\n')
        result = self.call('Stop')
        self.assertEqual(result.get('decision'), 'block', result)
        self.assertIn('Régression auto KO', result['reason'])
        self.assertIn('suite KO', result['reason'])

    def test_pytest_vert_laisse_passer(self):
        if not shutil.which('pytest'):
            self.skipTest('pytest absent')
        (self.project / 'pyproject.toml').write_text('[project]\nname = "x"\n')
        (self.project / 'test_ok.py').write_text('def test_ok():\n    assert 1 == 1\n')
        self.assertEqual(self.call('Stop'), {})

    def test_npm_passe_avant_pytest_vide(self):
        (self.project / 'node_modules').mkdir()
        (self.project / 'package.json').write_text(
            json.dumps({'scripts': {'test': 'node -e "process.exit(0)"'}}))
        (self.project / 'pyproject.toml').write_text('[project]\nname = "x"\n')
        self.assertEqual(self.call('Stop'), {})

    def test_venv_sans_pytest(self):
        (self.project / 'pyproject.toml').write_text('[project]\nname = "x"\n')
        venv = self.project / '.venv' / 'bin'
        venv.mkdir(parents=True)
        (venv / 'python').symlink_to('/usr/bin/false')
        result = subprocess.run(['python3', str(HOOKS / 'lanceur.py'), '--dir', str(self.project)],
                                capture_output=True, text=True, env=self.env, timeout=60, check=False)
        self.assertEqual(result.returncode, 3, result.stdout)
        self.assertIn('pytest absent du venv', result.stdout)

    def fake_path(self):
        # Ni jq ni outils du home : seulement python3.
        bin_dir = self.path / 'bin'
        bin_dir.mkdir()
        (bin_dir / 'python3').symlink_to(sys.executable)
        return dict(self.env, HOME=str(self.path), PATH=str(bin_dir))

    def raw_call(self, event, env, **values):
        payload = {'session_id': 'brut', 'cwd': str(self.project)}
        payload.update(values)
        process = subprocess.run([sys.executable, str(HOOKS / 'dispatch.py'), event],
                                 input=json.dumps(payload), text=True, capture_output=True,
                                 env=env, cwd=self.project, timeout=30, check=False)
        self.assertEqual(process.returncode, 0, process.stderr)
        return json.loads(process.stdout)

    def test_jq_absent_ne_valide_rien(self):
        env = self.fake_path()
        (self.project / 'a.js').write_text('const x = 1;\n')
        result = self.raw_call('Stop', env)
        self.assertEqual(result.get('decision'), 'block')
        self.assertIn('jq introuvable', result['reason'])
        prompt = self.raw_call('UserPromptSubmit', env, prompt='go')
        self.assertIn('jq introuvable', prompt['hookSpecificOutput']['additionalContext'])

    def test_commande_introuvable_pas_une_regression(self):
        (self.project / 'node_modules').mkdir()
        (self.project / 'package.json').write_text(json.dumps({'scripts': {'test': 'outil-inexistant-xyz'}}))
        result = self.call('Stop')
        self.assertEqual(result.get('decision'), 'block')
        self.assertIn('non vérifiée', result['reason'])
        self.assertNotIn('Régression auto KO', result['reason'])

    def test_npm_absent_signale(self):
        (self.project / 'node_modules').mkdir()
        (self.project / 'package.json').write_text(json.dumps({'scripts': {'test': 'exit 0'}}))
        env = dict(self.env, HOME=str(self.path), PATH='/usr/bin:/bin')
        result = subprocess.run([sys.executable, str(HOOKS / 'lanceur.py'), '--dir', str(self.project)],
                                capture_output=True, text=True, env=env, timeout=60, check=False)
        self.assertEqual(result.returncode, 3, result.stdout)
        self.assertIn('npm introuvable', result.stdout)

    def test_ko_garde_jusqu_a_la_relance(self):
        self.call('UserPromptSubmit', prompt='go')
        (self.project / 'nouveau.js').write_text('eval("x");\n')
        self.assertEqual(self.call('Stop').get('decision'), 'block')
        still = self.call('Stop', stop_hook_active=True)
        self.assertEqual(still.get('decision'), 'block')
        reminder = self.call('UserPromptSubmit', prompt='suite')
        self.assertIn('restés KO', reminder['hookSpecificOutput']['additionalContext'])

    def test_ko_corrige_pendant_la_relance(self):
        (self.project / 'Makefile').write_text('test:\n\ttrue\n')
        self.call('UserPromptSubmit', prompt='go')
        bad = self.project / 'nouveau.js'
        bad.write_text('eval("x");\n')
        self.assertEqual(self.call('Stop').get('decision'), 'block')
        bad.write_text('const x = 1;\n')
        self.assertEqual(self.call('Stop', stop_hook_active=True), {})
        self.assertNotIn('restés KO', json.dumps(self.call('UserPromptSubmit', prompt='suite')))

    def test_stop_sous_agent(self):
        (self.project / 'bad.js').write_text('eval("x");\n')
        result = self.call('SubagentStop')
        self.assertEqual(result['decision'], 'block')
        self.assertIn('sécu', result['reason'])

    def test_ko_grok_au_premier_outil(self):
        self.env['GROK_HOOK_EVENT'] = 'pre_tool_use'
        self.call('UserPromptSubmit', prompt='go')
        (self.project / 'nouveau.js').write_text('eval("x");\n')
        self.assertEqual(self.call('Stop').get('decision'), 'block')
        self.call('Stop', stop_hook_active=True)
        self.assertNotIn('restés KO', json.dumps(self.call('UserPromptSubmit', prompt='suite')))
        self.assertEqual(self.call('Stop'), {})
        refuse = self.call('PreToolUse', tool_name='Bash', tool_input={'command': 'cat .env'})
        self.assertEqual(refuse['hookSpecificOutput']['permissionDecision'], 'deny')
        self.assertNotIn('restés KO', json.dumps(refuse))
        demande = self.call('PreToolUse', tool_name='Bash', tool_input={'command': 'rm -rf ~'})
        self.assertEqual(demande['hookSpecificOutput']['permissionDecision'], 'ask')
        self.assertNotIn('restés KO', json.dumps(demande))
        premier = self.call('PreToolUse', tool_name='Bash', tool_input={'command': 'git status'})
        self.assertIn('restés KO', premier['hookSpecificOutput']['additionalContext'])
        suite = self.call('PreToolUse', tool_name='Bash', tool_input={'command': 'git status'})
        self.assertNotIn('restés KO', json.dumps(suite))

    def test_erreur_visible_code_zero(self):
        out = subprocess.run(['python3', str(HOOKS / 'dispatch.py'), 'Stop'], input='pas du json',
                             text=True, capture_output=True, env=self.env, cwd=self.project, timeout=30, check=False)
        self.assertEqual(out.returncode, 0)
        corps = json.loads(out.stdout)
        self.assertEqual(corps.get('decision'), 'block')
        self.assertIn('ne pas annoncer de validation', corps['systemMessage'])

    def test_erreur_pretool_refuse(self):
        out = subprocess.run(['python3', str(HOOKS / 'dispatch.py'), 'PreToolUse'], input='pas du json',
                             text=True, capture_output=True, env=self.env, cwd=self.project, timeout=30, check=False)
        self.assertEqual(out.returncode, 0, out.stderr)
        corps = json.loads(out.stdout)
        self.assertEqual(corps['hookSpecificOutput']['permissionDecision'], 'deny')

    def test_stop_hook_actif_grok(self):
        self.call('UserPromptSubmit', prompt='go')
        (self.project / 'nouveau.js').write_text('eval("x");\n')
        self.assertEqual(self.call('Stop').get('decision'), 'block')
        suite = self.call('Stop', stopHookActive=True)
        self.assertEqual(suite.get('decision'), 'block')

    def garde(self, tool, cwd=None, **entree):
        payload = {'session_id': 'garde', 'cwd': str(cwd or self.project), 'tool_name': tool, 'tool_input': entree}
        out = subprocess.run(['python3', str(HOOKS / 'dispatch.py'), 'PreToolUse'],
                             input=json.dumps(payload), text=True, capture_output=True,
                             env=self.env, cwd=self.project, timeout=30, check=False)
        self.assertEqual(out.returncode, 0, out.stderr)
        return json.loads(out.stdout).get('hookSpecificOutput', {}).get('permissionDecision')

    def test_garde_rm_racines(self):
        for command in ('rm -rf ~', 'rm -rf "$HOME"/', 'sudo rm -rf /', 'cd x && rm -fr ~/Bureau',
                        'rm -r ~/.agents/*', 'rm -Rf /usr'):
            self.assertEqual(self.garde('Bash', command=command), 'ask', command)
        for command in ('rm -rf build', 'rm -rf ~/Bureau/projet/node_modules', 'rm -f ~/a.txt',
                        'rm -rf *', 'git status'):
            self.assertIsNone(self.garde('Bash', command=command), command)

    def test_garde_secrets(self):
        for command in ('cat .env', 'grep KEY ~/proj/.env.local', 'cp ~/.claude/.credentials.json x',
                        'head ~/.ssh/id_ed25519'):
            self.assertEqual(self.garde('Bash', command=command), 'deny', command)
        self.assertEqual(self.garde('Read', file_path='/p/.env'), 'deny')
        self.assertEqual(self.garde('run_terminal_command', command='cat .env'), 'deny')
        self.assertEqual(self.garde('read_file', target_file='/p/.env'), 'deny')
        self.assertEqual(self.garde('grep', path='src/.env'), 'deny')
        self.assertEqual(self.garde('run_terminal_command', command='rm -rf /'), 'ask')
        self.assertIsNone(self.garde('run_terminal_command', command='git status'))
        for command in ('cat .env.example', 'echo .env >> .gitignore', 'cat ~/.ssh/id_ed25519.pub',
                        'ls -la .env', 'cat src/environment.ts'):
            self.assertIsNone(self.garde('Bash', command=command), command)
        self.assertIsNone(self.garde('Read', file_path='/p/.envrc'))

    def test_garde_outils_hors_shell(self):
        self.assertEqual(self.garde('rea__open_binary', path='/srv/app/.env'), 'deny')
        self.assertEqual(
            self.garde('use_tool', tool_name='rea__open_binary', tool_input={'path': '/srv/app/.env'}),
            'deny')
        self.assertEqual(self.garde('rea__inspect_plist', path='/home/a/.netrc'), 'deny')
        self.assertIsNone(self.garde('rea__open_binary', path='/srv/app/programme'))
        self.assertIsNone(self.garde('web_search', query='lire un fichier .env au demarrage'))
        self.assertEqual(self.garde('hashline_edit', file_path='src/.env'), 'deny')
        self.assertIsNone(self.garde('hashline_edit', file_path='src/main.c'))
        boite = {'path': '/srv/app/.env'}
        for _ in range(6):
            boite = {'dedans': boite}
        self.assertEqual(self.garde('rea__open_binary', paquet=boite), 'deny')
        profond = 'x'
        for _ in range(40):
            profond = {'a': profond}
        self.assertEqual(self.garde('boite', paquet=profond), 'deny')
        self.assertEqual(self.garde('rea__open_binary', path='/home/a/Mon dossier/.env'), 'deny')
        self.assertEqual(
            self.garde('use_tool', tool_input={'target': '/home/a/Mon dossier/.env'}),
            'deny')
        self.assertEqual(
            self.garde('use_tool', tool_input={'filePath': 'Mon dossier/.env'}),
            'deny')
        self.assertIsNone(self.garde('web_search', query='voir /tmp/.env plus tard'))
        self.assertEqual(self.garde('use_tool', tool_input={'note': 'Mon dossier/.env'}), 'deny')
        self.assertEqual(self.garde('use_tool', tool_input={'note': 'Mon dossier/.env.local'}), 'deny')
        self.assertEqual(
            self.garde('use_tool', tool_input={'note': 'Mon dossier/.credentials.json'}),
            'deny')
        self.assertIsNone(self.garde('use_tool', tool_input={'note': 'le fichier .env'}))
        self.assertIsNone(self.garde('use_tool', tool_input={'note': 'Mon dossier/.env.example'}))

    def test_garde_disque_et_force_push(self):
        for command in ('sudo dd if=x.img of=/dev/sdb bs=4M', 'mkfs.ext4 /dev/nvme0n1p3',
                        'git push --force origin main', 'git push origin +main'):
            self.assertEqual(self.garde('Bash', command=command), 'ask', command)
        for command in ('dd if=/dev/zero of=disk.img bs=1M count=1', 'git push origin main',
                        'mkfs.fat -C floppy.img 1440'):
            self.assertIsNone(self.garde('Bash', command=command), command)

    def test_garde_git_sans_hooks(self):
        for command in ('git commit --no-verify -m x', 'git commit -n -m x', 'git commit -anm x',
                        'git commit --no-ver -m x', 'git push --no-verify origin main',
                        'git -c core.hooksPath=/dev/null commit -m x', 'git merge --no-verify feature',
                        'git commit -am x -n', 'cd . && git commit -n -m x'):
            self.assertEqual(self.garde('Bash', command=command), 'ask', command)
        for command in ('git commit -m -n', 'git commit -m x', 'git push -n origin main',
                        'git commit -am "no-verify later"', 'git commit -m --no-verify', 'git commit -S -m x',
                        'git commit -- -n', 'git commit -t -n', 'git commit -Sn -m x', 'git status -n'):
            self.assertIsNone(self.garde('Bash', command=command), command)

    def test_garde_materiel(self):
        for command in ('dd if=os.iso of=/dev/disk/by-id/usb-Cle_X-0:0 bs=4M', 'cat os.iso > /dev/sdb',
                        'cat os.img | sudo tee /dev/mmcblk0', 'sudo cp os.iso /dev/sdc',
                        'limine bios-install /dev/sdb', 'sudo grub2-install /dev/sda',
                        'ecrire-image build/os.iso /dev/disk/by-id/usb-Cle_X-0:0 --ecrire',
                        'python3 scripts/ecrire_image.py os.iso /dev/disk/by-id/usb-X --ecrire',
                        'sudo flashrom -p internal -w bios.rom', 'fwupdmgr update',
                        'fwupdmgr report-history', 'sudo efibootmgr -o 0001,0002', 'efibootmgr -B -b 0003',
                        'mokutil --disable-validation', 'mokutil --import cle.der'):
            self.assertEqual(self.garde('Bash', command=command), 'ask', command)
        for command in ('ecrire-image build/os.iso /dev/disk/by-id/usb-Cle_X-0:0', 'ls -l /dev/disk/by-id',
                        'lsblk -J /dev/sdb 2>/dev/null', 'limine bios-install build/os.iso',
                        'cp build/os.iso iso/', 'efibootmgr -v', 'efibootmgr', 'mokutil --sb-state',
                        'fwupdmgr get-devices', 'flashrom -p internal -r sauvegarde.rom',
                        'make test 2>&1 | tee build/test.log'):
            self.assertIsNone(self.garde('Bash', command=command), command)

    def depot_git(self):
        def git(*args):
            subprocess.run(['git', '-C', str(self.project), '-c', 'user.name=t', '-c', 'user.email=t@t', *args],
                           check=True, capture_output=True, timeout=30)
        git('init', '-q')
        (self.project / 'src').mkdir()
        (self.project / 'src' / 'a.c').write_text('int a;\n')
        (self.project / '.gitignore').write_text('build/\n')
        git('add', '.gitignore', 'src/a.c')
        git('commit', '-q', '-m', 'init')
        (self.project / '.git' / 'info' / 'exclude').write_text('docs/\n')
        for dossier, fichier in (('build', 'a.o'), ('docs', 'j.md'), ('notes', 'n.txt')):
            (self.project / dossier).mkdir()
            (self.project / dossier / fichier).write_text('x\n')

    def test_garde_rm_travail_local(self):
        self.depot_git()
        for command in ('rm -rf docs', 'rm -rf docs/*', 'rm -r d*', 'rm -rf notes', 'rm -rf build docs'):
            self.assertEqual(self.garde('Bash', command=command), 'ask', command)
        for command in ('rm -rf build', 'rm -rf src', 'rm -rf absent', 'rm -f notes/n.txt'):
            self.assertIsNone(self.garde('Bash', command=command), command)
        (self.project / 'src' / 'a.c').write_text('int b;\n')
        self.assertEqual(self.garde('Bash', command='rm -rf src'), 'ask')

    def test_garde_rm_projets(self):
        self.depot_git()
        libre = self.path / 'libre'
        (libre / 'sous').mkdir(parents=True)
        for command in ('rm -rf *', f'rm -rf {self.project}', f'sudo rm -rf {self.path}', 'rm -rf .git',
                        f'cd {self.path} && rm -rf project'):
            self.assertEqual(self.garde('Bash', command=command), 'ask', command)
        self.assertIsNone(self.garde('Bash', command=f'rm -rf {libre}'))

    def test_garde_git_destructeur(self):
        self.depot_git()
        for command in ('git clean -fdx', 'git clean -fd', 'git worktree remove --force wt'):
            self.assertEqual(self.garde('Bash', command=command), 'ask', command)
        propres = ('git reset --hard HEAD', 'git checkout -- .', 'git restore .', 'git checkout -b x',
                   'git clean -n -d', 'git clean -ndx', 'git worktree remove wt', 'git status', 'git stash')
        for command in propres:
            self.assertIsNone(self.garde('Bash', command=command), command)
        (self.project / 'src' / 'a.c').write_text('int b;\n')
        for command in ('git reset --hard', 'git checkout -- src/a.c', 'git restore src/a.c', 'git switch -f main',
                        'git checkout .'):
            self.assertEqual(self.garde('Bash', command=command), 'ask', command)
        self.assertEqual(self.garde('Bash', cwd=self.path, command=f'git -C {self.project} reset --hard'), 'ask')
        self.assertEqual(self.garde('Bash', cwd=self.path, command='cd project && git reset --hard'), 'ask')
        (self.project / 'src' / 'b.c').write_text('int c;\n')
        for args in (('add', 'src/b.c'), ('-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '-m', 'b')):
            subprocess.run(['git', '-C', str(self.project), *args], check=True, capture_output=True, timeout=30)
        for command in ('git restore --staged src/a.c', 'git checkout -b y', 'git diff', 'git checkout -- src/b.c',
                        'git restore src/b.c'):
            self.assertIsNone(self.garde('Bash', command=command), command)

    def test_garde_secrets_detours(self):
        for command in ('echo $(cat .env)', 'echo `cat .env`', 'source .env', '. .env && env',
                        'find . -name .env -exec cat {} +', "export $(grep -v '^#' .env | xargs)"):
            self.assertEqual(self.garde('Bash', command=command), 'deny', command)
        for command in ('. venv/bin/activate', 'source ~/.bashrc', 'find . -name .env', 'timeout 5s make test',
                        'echo $(date)', 'python3 -c "print(1)"', 'source .env.example',
                        'python3 -c \'open("readme.txt").read()\'', 'echo LmVudg=='):
            self.assertIsNone(self.garde('Bash', command=command), command)

    def test_garde_ecriture_secrets(self):
        for tool, champ, chemin in (
                ('write', 'file_path', 'proj/.env'),
                ('Write', 'path', '/tmp/app/.env.local'),
                ('search_replace', 'file_path', 'src/.env.staging'),
                ('Edit', 'target_file', '/home/a/.ssh/id_ed25519'),
                ('NotebookEdit', 'notebook_path', 'n/.netrc'),
        ):
            self.assertEqual(self.garde(tool, **{champ: chemin}), 'deny', (tool, chemin))
        for tool, chemin in (('write', 'proj/.env.example'), ('Edit', 'src/environment.ts'),
                             ('write', 'notes.md')):
            self.assertIsNone(self.garde(tool, file_path=chemin), (tool, chemin))

    def test_garde_secret_cache(self):
        for command in (
                'python3 -c \'p=".e"+"nv"; open(p).read()\'',
                'python3 -c \'open("\\x2eenv").read()\'',
                'python3 -c \'open(__import__("base64").b64decode("LmVudg==")).read()\'',
                'python3 -c \'open(__import__("base64").b64decode("LmVu"+"dg==")).read()\'',
                'node -e \'require("fs").readFileSync(".e".concat("nv"))\'',
                'perl -e \'open(F,".e"."nv")\'',
                'bash -c \'source ".e""nv"\'',
                'bash -c \'source .env\'',
        ):
            self.assertEqual(self.garde('Bash', command=command), 'deny', command)
        self.assertEqual(self.garde('Bash', command='python3 -c \'open(p).read()\''), 'ask')
        self.assertEqual(self.garde('Bash', command='bash -c \'source "$F"\''), 'ask')

    def test_garde_script_secret(self):
        script = self.project / 'lire.py'
        script.write_text('open(".env").read()\n')
        self.assertEqual(self.garde('Bash', command='python3 lire.py'), 'deny')
        self.assertEqual(self.garde('Bash', command='python3 -- lire.py'), 'deny')
        self.assertEqual(self.garde('Bash', command='python3 -W ignore lire.py'), 'deny')
        self.assertEqual(self.garde('Bash', command='python3 lire.py -c'), 'deny')
        self.assertEqual(
            self.garde('Bash', command='python3 --check-hash-based-pycs always lire.py'), 'deny')
        script.write_text('open(".e" "nv").read()\n')
        self.assertEqual(self.garde('Bash', command='python3 lire.py'), 'deny')
        script.write_text('open(".e"\n"nv").read()\n')
        self.assertEqual(self.garde('Bash', command='python3 lire.py'), 'deny')
        script.write_text('open(__import__("base64").b64decode("LmVudg==")).read()\n')
        self.assertEqual(self.garde('Bash', command='python3 lire.py'), 'deny')
        script.write_text('p=".e"+"nv"\nopen(p).read()\n')
        self.assertEqual(self.garde('Bash', command='python3 lire.py'), 'deny')
        (self.project / 'lire.js').write_text('require("fs").readFileSync(".env")\n')
        self.assertEqual(self.garde('Bash', command='node lire.js'), 'deny')
        self.assertEqual(self.garde('Bash', command='node --require preload.js lire.js'), 'deny')
        (self.project / 'lire.sh').write_text('source .env\n')
        self.assertEqual(self.garde('Bash', command='bash lire.sh'), 'deny')
        self.assertEqual(self.garde('Bash', command='bash -e lire.sh'), 'deny')
        self.assertEqual(self.garde('Bash', command='bash -o pipefail lire.sh'), 'deny')
        (self.project / 'point.sh').write_text('. .env\n')
        self.assertEqual(self.garde('Bash', command='bash point.sh'), 'deny')
        (self.project / 'net.sh').write_text('. .netrc\n')
        self.assertEqual(self.garde('Bash', command='bash net.sh'), 'deny')
        (self.project / 'slash.sh').write_text('. ./.env\n')
        self.assertEqual(self.garde('Bash', command='bash slash.sh'), 'deny')
        (self.project / 'loin.py').write_text(
            'nom = ".env"\n' + ('a' * 100) + '\nopen("readme.txt").read()\n')
        self.assertIsNone(self.garde('Bash', command='python3 loin.py'))
        (self.project / 'pytest').write_text('open(".env").read()\n')
        self.assertIsNone(self.garde('Bash', command='python3 -m pytest'))
        script.write_text('print(1)\n')
        self.assertIsNone(self.garde('Bash', command='python3 lire.py'))
        script.write_text('open("readme.txt").read()\n')
        self.assertIsNone(self.garde('Bash', command='python3 lire.py'))
        script.write_text('open(p).read()\n')
        self.assertEqual(self.garde('Bash', command='python3 lire.py'), 'ask')

    def test_garde_script_secrets_restes(self):
        script = self.project / 'lire.py'
        script.write_text('open(chr(46)+chr(101)+chr(110)+chr(118)).read()\n')
        self.assertEqual(self.garde('Bash', command='python3 lire.py'), 'deny')
        self.assertEqual(
            self.garde('Bash', command='python3 -c \'open(chr(46)+chr(101)+chr(110)+chr(118)).read()\''),
            'deny')
        script.write_text('nom = ".env"\n' + ('a' * 100) + '\nopen(nom).read()\n')
        self.assertEqual(self.garde('Bash', command='python3 lire.py'), 'ask')
        script.write_text('open(os.environ["A"]).read()\n')
        self.assertEqual(self.garde('Bash', command='python3 lire.py'), 'ask')
        script.write_text('Path(os.environ["A"]).read_text()\n')
        self.assertEqual(self.garde('Bash', command='python3 lire.py'), 'ask')
        script.write_text('root = Path(os.environ.get("A"))\n')
        self.assertIsNone(self.garde('Bash', command='python3 lire.py'))
        script.write_text('print(Path(__file__).read_text(encoding="utf-8"))\n')
        self.assertIsNone(self.garde('Bash', command='python3 lire.py'))
        script.write_bytes(b'\0' + b'open(".env").read()\n')
        self.assertEqual(self.garde('Bash', command='python3 lire.py'), 'deny')
        script.write_bytes(b'\0print(1)\n')
        self.assertEqual(self.garde('Bash', command='python3 lire.py'), 'ask')
        gros = self.project / 'gros.py'
        gros.write_bytes(b'print(1)\n' + b'a' * (256 * 1024))
        self.assertEqual(self.garde('Bash', command='python3 gros.py'), 'ask')
        plante = HOOKS / 'zz-lecture-test.py'
        self.addCleanup(plante.unlink, missing_ok=True)
        plante.write_text('open(".env").read()\n')
        self.assertEqual(self.garde('Bash', command=f'python3 {plante}'), 'deny')
        self.assertIsNone(self.garde('Bash', command=f'python3 {HOOKS / "verify.py"}'))
        self.assertIsNone(self.garde('Bash', command=f'bash {HOOKS / "cyber-scan.sh"}'))
        coquille = self.project / 'lire.sh'
        coquille.write_text('. "$(dirname "$0")/ignores.sh"\n')
        self.assertIsNone(self.garde('Bash', command='bash lire.sh'))
        coquille.write_text('source "$F"\n')
        self.assertEqual(self.garde('Bash', command='bash lire.sh'), 'ask')
        script.write_text('open(chr(46)+chr(101)+chr(110)+chr(118)+chr(256)*0)\n')
        self.assertEqual(self.garde('Bash', command='python3 lire.py'), 'deny')
        script.write_text('open(chr(46)+chr(256)*0+chr(101)+chr(110)+chr(118))\n')
        self.assertEqual(self.garde('Bash', command='python3 lire.py'), 'deny')
        eval_chr = (
            'eval(chr(111)+chr(112)+chr(101)+chr(110)+chr(40)+chr(34)'
            '+chr(46)+chr(101)+chr(110)+chr(118)+chr(34)+chr(41)+chr(256)*0)'
        )
        script.write_text(eval_chr + '\n')
        self.assertEqual(self.garde('Bash', command='python3 lire.py'), 'deny')
        self.assertEqual(self.garde('Bash', command="python3 -c '" + eval_chr + "'"), 'deny')
        script.write_text('nom = ".env"\n' + ('a' * 100) + '\nnom.read_text()\n')
        self.assertEqual(self.garde('Bash', command='python3 lire.py'), 'ask')
        script.write_text('p.read_bytes()\n')
        self.assertEqual(self.garde('Bash', command='python3 lire.py'), 'ask')
        script.write_text('Path(nom).read_text()\n')
        self.assertEqual(self.garde('Bash', command='python3 lire.py'), 'ask')
        script.write_text('Path("readme.txt").read_text()\n')
        self.assertIsNone(self.garde('Bash', command='python3 lire.py'))
        script.write_text('p = chr(46)*1+chr(101)+chr(110)+chr(118)\nopen(p).read()\n')
        self.assertEqual(self.garde('Bash', command='python3 lire.py'), 'deny')
        script.write_text('p = chr(47)*2+chr(46)+chr(101)+chr(110)+chr(118)\nopen(p).read()\n')
        self.assertEqual(self.garde('Bash', command='python3 lire.py'), 'deny')
        script.write_text('p = chr(46)*2+chr(101)+chr(110)+chr(118)\nopen(p).read()\n')
        self.assertEqual(self.garde('Bash', command='python3 lire.py'), 'ask')
        script.write_text('p = chr(47)*5+chr(46)+chr(101)+chr(110)+chr(118)\nopen(p).read()\n')
        self.assertEqual(self.garde('Bash', command='python3 lire.py'), 'deny')
        (self.project / 'lire.js').write_text('require("fs").readFileSync(".env")\n')
        (self.project / 'innocent.js').write_text('console.log(1)\n')
        self.assertEqual(self.garde('Bash', command='node --test-reporter spec lire.js'), 'deny')
        self.assertEqual(
            self.garde('Bash', command='node --experimental-strip-types innocent.js lire.js'), 'deny')
        self.assertEqual(self.garde('Bash', command='node --require lire.js'), 'deny')
        self.assertIsNone(self.garde('Bash', command=f'python3 {HOOKS / "dispatch.py"}'))
        self.assertIsNone(self.garde('Bash', command=f'python3 {HOOKS.parent / "verifier"}'))
        plante_attr = HOOKS / 'zz-lecture-attr.py'
        self.addCleanup(plante_attr.unlink, missing_ok=True)
        plante_attr.write_text('nom.read_text()\n')
        self.assertEqual(self.garde('Bash', command=f'python3 {plante_attr}'), 'ask')
        script.write_text('open(".env").read()\n')
        self.assertEqual(self.garde('Bash', command='python3 -m pytest lire.py'), 'deny')
        self.assertEqual(self.garde('Bash', command="python3 -c 'print(1)' lire.py"), 'deny')
        self.assertEqual(self.garde('Bash', command='python3 -m lire'), 'deny')
        script.write_text('print(1)\n')
        self.assertIsNone(self.garde('Bash', command='python3 -W ignore lire.py'))

    def plus_tard(self, chemin, contenu):
        chemin.write_text(contenu)
        moment = time.time() + 2
        os.utime(chemin, (moment, moment))

    def test_code_sans_lanceur_rebloque(self):
        self.call('UserPromptSubmit', prompt='go')
        self.plus_tard(self.project / 'main.py', 'def f():\n    return 1\n')
        result = self.call('Stop')
        self.assertEqual(result.get('decision'), 'block')
        self.assertIn('lanceur', result['reason'])
        suite = self.call('Stop', stop_hook_active=True)
        self.assertEqual(suite.get('decision'), 'block')
        self.assertIn('lanceur', suite['reason'])

    def test_note_sans_lanceur_laisse_passer(self):
        self.call('UserPromptSubmit', prompt='go')
        self.plus_tard(self.project / 'note.md', 'bonjour\n')
        self.assertEqual(self.call('Stop'), {})

    def test_oracle_vide_bloque(self):
        (self.project / 'Makefile').write_text('test:\n\ttrue\n')
        self.call('UserPromptSubmit', prompt='go')
        self.plus_tard(self.project / 'test_vide.py', 'def test_appel():\n    objet()\n')
        result = self.call('Stop')
        self.assertEqual(result.get('decision'), 'block')
        self.assertIn('Oracle vide', result['reason'])
        self.assertIn('test_appel', result['reason'])

    def test_oracle_fort_laisse_passer(self):
        (self.project / 'Makefile').write_text('test:\n\ttrue\n')
        self.call('UserPromptSubmit', prompt='go')
        self.plus_tard(self.project / 'test_fort.py', 'def test_valeur():\n    assert 1 == 1\n')
        self.assertEqual(self.call('Stop'), {})

    def test_oracle_node_strict_laisse_passer(self):
        (self.project / 'Makefile').write_text('test:\n\ttrue\n')
        self.call('UserPromptSubmit', prompt='go')
        self.plus_tard(self.project / 'a.test.js', 'it("a", () => { assert.strictEqual(1, 1) })\n')
        self.assertEqual(self.call('Stop'), {})

    def test_oracle_node_vide_bloque(self):
        (self.project / 'Makefile').write_text('test:\n\ttrue\n')
        self.call('UserPromptSubmit', prompt='go')
        self.plus_tard(self.project / 'a.test.js', 'it("a", () => { foo() })\n')
        result = self.call('Stop')
        self.assertEqual(result.get('decision'), 'block')
        self.assertIn('a.test.js', result['reason'])

    def test_oracle_vide_fonctions(self):
        import oracle_vide
        self.assertEqual(oracle_vide.fonctions_py('def test_appel():\n    objet()\n'), ['test_appel'])
        self.assertEqual(oracle_vide.fonctions_py('def test_valeur():\n    assert 1 == 1\n'), [])
        self.assertEqual(oracle_vide.fonctions_py('def test_nul():\n    assert x is not None\n'), ['test_nul'])
        self.assertEqual(
            oracle_vide.fonctions_py('def test_mixte():\n    assert x is not None\n    assert x == 1\n'), [])
        self.assertEqual(oracle_vide.fonctions_py('def test_vrai():\n    assert x\n'), ['test_vrai'])
        self.assertEqual(
            oracle_vide.fonctions_py('import pytest\ndef test_leve():\n    with pytest.raises(ValueError):\n        f()\n'),
            [])
        self.assertEqual(oracle_vide.lignes_autres('it("a", () => { foo() })\n', 'a.test.js'), ['a'])
        self.assertEqual(oracle_vide.lignes_autres('it("a", () => { expect(1).toBe(1) })\n', 'a.test.js'), [])
        self.assertEqual(oracle_vide.lignes_autres('it("a", () => { assert.strictEqual(1, 1) })\n', 'a.test.js'), [])
        self.assertEqual(
            oracle_vide.lignes_autres('it("a", () => { expect(x).toBeTruthy() })\n', 'a.test.js'), ['a'])
        self.assertEqual(
            oracle_vide.lignes_autres(
                'it("a", () => { expect(1).toBe(1) })\nit("b", () => { foo() })\n', 'a.test.js'),
            ['b'])
        self.assertEqual(oracle_vide.lignes_autres('function testA() { return 1; }\n', 'FooTest.php'), ['testA'])
        self.assertEqual(oracle_vide.lignes_autres('function testA() { assert(1); }\n', 'FooTest.php'), [])
        self.assertEqual(
            oracle_vide.lignes_autres(
                'function testA() { assertSame(1, 1); }\nfunction testB() { return 1; }\n', 'FooTest.php'),
            ['testB'])
        self.assertEqual(
            oracle_vide.lignes_autres('function testA() { assertNotNull($x); }\n', 'FooTest.php'), ['testA'])

    def fausse_config(self, code):
        def git(*args):
            subprocess.run(['git', '-C', str(self.config), '-c', 'user.name=t', '-c', 'user.email=t@t', *args],
                           check=True, capture_output=True, timeout=30)
        self.config.mkdir()
        git('init', '-q')
        (self.config / 'regle.md').write_text('a\n')
        verifier = self.config / 'verifier'
        verifier.write_text(f'#!/bin/sh\necho "KO  ruff"\nexit {code}\n')
        verifier.chmod(0o755)
        git('add', 'regle.md', 'verifier')
        git('commit', '-q', '-m', 'init')

    def modifier_config(self, decalage):
        regle = self.config / 'regle.md'
        regle.write_text('b\n')
        moment = time.time() + decalage
        os.utime(regle, (moment, moment))

    def test_config_modifiee_pendant_le_tour_bloque(self):
        self.fausse_config(1)
        self.call('UserPromptSubmit', prompt='règle')
        self.modifier_config(5)
        result = self.call('Stop')
        self.assertEqual(result.get('decision'), 'block')
        self.assertIn('Config ~/.agents', result['reason'])

    def test_config_sans_debut_de_tour_ignoree(self):
        self.fausse_config(1)
        self.modifier_config(5)
        self.assertEqual(self.call('Stop'), {})

    def test_config_modifiee_avant_le_tour_ignoree(self):
        self.fausse_config(1)
        self.modifier_config(-100)
        self.call('UserPromptSubmit', prompt='règle')
        self.assertEqual(self.call('Stop'), {})

    def test_config_propre_ignoree(self):
        self.fausse_config(1)
        self.call('UserPromptSubmit', prompt='règle')
        self.assertEqual(self.call('Stop'), {})

    def test_config_verifiee_verte(self):
        self.fausse_config(0)
        self.call('UserPromptSubmit', prompt='règle')
        self.modifier_config(5)
        self.assertEqual(self.call('Stop'), {})

    def test_config_gate_recoit_les_fichiers_changes(self):
        self.fausse_config(0)
        faux = self.config / 'verifier'
        faux.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > args.txt\nexit 0\n')
        os.utime(faux, (time.time() - 100, time.time() - 100))
        self.call('UserPromptSubmit', prompt='règle')
        self.modifier_config(5)
        self.assertEqual(self.call('Stop'), {})
        self.assertEqual((self.config / 'args.txt').read_text().split(), ['--rapide', '--pour', 'regle.md'])

    def test_stop_ignore_un_dossier_de_projets(self):
        (self.project / 'app' / '.git').mkdir(parents=True)
        (self.project / 'bad.js').write_text('eval("x");\n')
        self.assertEqual(self.call('Stop'), {})
        (self.project / '.git').mkdir()
        moment = time.time() + 5
        os.utime(self.project / 'bad.js', (moment, moment))
        result = self.call('Stop')
        self.assertEqual(result.get('decision'), 'block')
        self.assertIn('bad.js:1', result['reason'])

    def test_ecriture_dans_un_dossier_de_projets_scanne_le_fichier_seul(self):
        (self.project / 'app' / '.git').mkdir(parents=True)
        (self.project / 'bad.js').write_text('eval("x");\n')
        result = self.call('PostToolUse', tool_input={'file_path': 'bad.js'})
        self.assertIn('CYBER AUTO KO', result['hookSpecificOutput']['additionalContext'])
        self.assertEqual(self.call('Stop'), {})

    def test_shellcheck_apres_ecriture(self):
        if not shutil.which('shellcheck'):
            self.skipTest('shellcheck absent')
        propre = '#!/bin/sh\nset -eu\nprintf "%s\\n" "$1"\n'
        fautif = '#!/usr/bin/env bash\ncible=$1\nrm -rf $cible/*\n'
        (self.project / 'lance.sh').write_text(propre)
        self.assertEqual(self.call('PostToolUse', tool_input={'file_path': 'lance.sh'}), {})
        (self.project / 'lance.sh').write_text(fautif)
        result = self.call('PostToolUse', tool_input={'file_path': 'lance.sh'})
        self.assertIn('SHELLCHECK KO', result['hookSpecificOutput']['additionalContext'])
        self.assertIn('SC2086', result['hookSpecificOutput']['additionalContext'])
        (self.project / 'outil').write_text(fautif)
        result = self.call('PostToolUse', tool_input={'file_path': 'outil'})
        self.assertIn('SHELLCHECK KO', result['hookSpecificOutput']['additionalContext'])
        (self.project / 'outil.py').write_text('#!/usr/bin/env python3\nprint(1)\n')
        self.assertEqual(self.call('PostToolUse', tool_input={'file_path': 'outil.py'}), {})
        (self.project / 'sans_shebang.sh').write_text('echo "x"\n')
        result = self.call('PostToolUse', tool_input={'file_path': 'sans_shebang.sh'})
        self.assertIn('SC2148', result['hookSpecificOutput']['additionalContext'])

    def test_posix_sh_apres_ecriture(self):
        if not shutil.which('shellcheck') or not shutil.which('checkbashisms'):
            self.skipTest('shellcheck ou checkbashisms absent')
        propre = '#!/bin/sh\nset -eu\nkill -s TERM "$1"\n'
        fautif = '#!/bin/sh\nset -eu\nkill -SIGTERM "$1"\n'
        (self.project / 'arret.sh').write_text(propre)
        self.assertEqual(self.call('PostToolUse', tool_input={'file_path': 'arret.sh'}), {})
        (self.project / 'arret.sh').write_text(fautif)
        contexte = self.call('PostToolUse', tool_input={'file_path': 'arret.sh'})['hookSpecificOutput']['additionalContext']
        self.assertIn('POSIX KO', contexte)
        self.assertNotIn('SHELLCHECK KO', contexte)
        (self.project / 'arret.sh').write_text(fautif.replace('#!/bin/sh', '#!/usr/bin/env bash'))
        self.assertEqual(self.call('PostToolUse', tool_input={'file_path': 'arret.sh'}), {})
        (self.project / 'arret.sh').write_text('#!/bin/sh\necho -n "$1"\n')
        contexte = self.call('PostToolUse', tool_input={'file_path': 'arret.sh'})['hookSpecificOutput']['additionalContext']
        self.assertIn('SHELLCHECK KO', contexte)
        self.assertIn('POSIX KO', contexte)

    def test_formatage_apres_ecriture(self):
        if not shutil.which('shfmt'):
            self.skipTest('shfmt absent')
        brut = '#!/usr/bin/env bash\nset -eu\nf() {\necho "$1"\n}\nf "a"\n'
        (self.project / 'lance.sh').write_text(brut)
        result = self.call('PostToolUse', tool_input={'file_path': 'lance.sh'})
        self.assertIn('reformaté par shfmt', result['hookSpecificOutput']['additionalContext'])
        self.assertIn('f()\n{\n\techo "$1"\n}\n', (self.project / 'lance.sh').read_text())
        self.assertEqual(self.call('PostToolUse', tool_input={'file_path': 'lance.sh'}), {})
        (self.project / 'outil').write_text(brut)
        self.call('PostToolUse', tool_input={'file_path': 'outil'})
        self.assertIn('f()\n{', (self.project / 'outil').read_text())
        (self.project / '.editorconfig').write_text('[*.sh]\nindent_style = space\nindent_size = 2\n')
        (self.project / 'lance.sh').write_text(brut)
        self.call('PostToolUse', tool_input={'file_path': 'lance.sh'})
        self.assertIn('f() {\n  echo "$1"\n}\n', (self.project / 'lance.sh').read_text())

    def test_formatage_selon_la_config_du_projet(self):
        c = 'int\tmain(void)\n{\n\treturn (0);\n}\n'
        (self.project / 'main.c').write_text(c)
        self.call('PostToolUse', tool_input={'file_path': 'main.c'})
        self.assertEqual((self.project / 'main.c').read_text(), c)
        python = 'x = {  "a":1 }\n'
        (self.project / 'outil.py').write_text(python)
        self.assertEqual(self.call('PostToolUse', tool_input={'file_path': 'outil.py'}), {})
        self.assertEqual((self.project / 'outil.py').read_text(), python)
        if shutil.which('ruff'):
            (self.project / 'ruff.toml').write_text('line-length = 100\n')
            result = self.call('PostToolUse', tool_input={'file_path': 'outil.py'})
            self.assertIn('reformaté par ruff', result['hookSpecificOutput']['additionalContext'])
            self.assertEqual((self.project / 'outil.py').read_text(), 'x = {"a": 1}\n')
        if shutil.which('prettier'):
            (self.project / 'donnees.json').write_text('{"a":1,\n"b":[1,2]}\n')
            self.assertEqual(self.call('PostToolUse', tool_input={'file_path': 'donnees.json'}), {})
            (self.project / '.prettierrc').write_text('{}\n')
            result = self.call('PostToolUse', tool_input={'file_path': 'donnees.json'})
            self.assertIn('reformaté par prettier', result['hookSpecificOutput']['additionalContext'])
            self.assertEqual((self.project / 'donnees.json').read_text(), '{ "a": 1, "b": [1, 2] }\n')
            (self.project / 'casse.ts').write_text('const x: number = ;\n')
            result = self.call('PostToolUse', tool_input={'file_path': 'casse.ts'})
            self.assertIn('FORMATAGE KO (prettier)', result['hookSpecificOutput']['additionalContext'])

    def test_ctest_lance_la_suite(self):
        if not shutil.which('ctest'):
            self.skipTest('ctest absent')
        (self.project / 'CMakeLists.txt').write_text('project(x)\n')
        result = self.call('Stop')
        self.assertEqual(result.get('decision'), 'block')
        self.assertIn('build CMake absent', result['reason'])
        build = self.project / 'build'
        build.mkdir()
        (build / 'CTestTestfile.cmake').write_text('add_test(ko "/bin/sh" "-c" "echo suite KO; exit 1")\n')
        result = self.call('Stop')
        self.assertEqual(result.get('decision'), 'block')
        self.assertIn('suite KO', result['reason'])
        (build / 'CTestTestfile.cmake').write_text('add_test(ok "/bin/sh" "-c" "exit 0")\n')
        self.assertEqual(self.call('Stop'), {})

    def test_make_check_sans_cible_test(self):
        (self.project / '.mode-side-project').touch()
        (self.project / 'Makefile').write_text('check:\n\t@echo verif KO; exit 1\n')
        result = self.call('Stop')
        self.assertEqual(result.get('decision'), 'block')
        self.assertIn('verif KO', result['reason'])
        (self.project / 'Makefile').write_text('check:\n\t@echo verif OK\n')
        self.assertEqual(self.call('Stop'), {})


    def test_session_start_purge_les_vieux_etats(self):
        racine = self.path / 'state'
        vieux = racine / 'ancienne-session'
        recent = racine / 'session-recente'
        for dossier in (vieux, recent):
            dossier.mkdir(parents=True)
            (dossier / 'ended').touch()
            (dossier / 'ko').write_text('x')
        ancien = time.time() - 10 * 86400
        os.utime(vieux / 'ended', (ancien, ancien))
        self.assertEqual(self.call('SessionStart'), {})
        self.assertFalse(vieux.exists())
        self.assertTrue((recent / 'ko').is_file())

    def test_garde_git_lent_demande_dans_le_delai(self):
        faux = self.path / 'bin'
        faux.mkdir()
        (faux / 'git').write_text('#!/bin/sh\nsleep 2\ncase "$3" in rev-parse) pwd ;; esac\nexit 0\n')
        (faux / 'git').chmod(0o755)
        self.env['PATH'] = str(faux) + ':' + self.env['PATH']
        for nom in ('a', 'b', 'c', 'd', 'e'):
            (self.project / nom).mkdir()
        debut = time.monotonic()
        result = self.call('PreToolUse', tool_name='Bash',
                           tool_input={'command': 'rm -rf a b c d e'})
        duree = time.monotonic() - debut
        self.assertEqual(result['hookSpecificOutput']['permissionDecision'], 'ask')
        self.assertIn('git ne répond pas', result['hookSpecificOutput']['permissionDecisionReason'])
        self.assertLess(duree, 10)

    def etat_prepare(self):
        self.etat.mkdir(parents=True, exist_ok=True, mode=0o700)
        return self.etat

    def test_garde_pose_et_leve_sa_marque(self):
        self.call('PreToolUse', tool_name='Bash', tool_input={'command': 'ls'})
        self.assertFalse((self.etat / 'garde-encours').exists())

    def test_garde_interrompu_tient_le_stop(self):
        self.etat_prepare().joinpath('garde-encours').touch()
        result = self.call('Stop', reason='end_turn')
        self.assertEqual(result['decision'], 'block')
        self.assertIn('garde a été interrompu', result['reason'])
        self.assertFalse((self.etat / 'garde-encours').exists())

    def test_garde_interrompu_signale_au_prompt(self):
        self.etat_prepare().joinpath('garde-encours').touch()
        result = self.call('UserPromptSubmit', prompt='continue')
        self.assertIn('garde a été interrompu',
                      result['hookSpecificOutput']['additionalContext'])
        self.assertFalse((self.etat / 'garde-encours').exists())

    def test_evenement_retire_tient_le_stop(self):
        degradee = json.loads(json.dumps(self.saine))
        del degradee['hooks']['events']['Stop']
        self.moteur.write_text(json.dumps(degradee), encoding='utf-8')
        result = self.call('SessionStart', source='startup')
        self.assertIn('Harnais dégradé',
                      result['hookSpecificOutput']['additionalContext'])
        result = self.call('Stop', reason='end_turn')
        self.assertEqual(result['decision'], 'block')
        self.assertIn('Harnais dégradé', result['reason'])

    def test_hooks_desactives_degradent(self):
        degradee = json.loads(json.dumps(self.saine))
        degradee['hooks']['enabled'] = False
        self.moteur.write_text(json.dumps(degradee), encoding='utf-8')
        result = self.call('SessionStart', source='startup')
        self.assertIn('désactivés', result['hookSpecificOutput']['additionalContext'])

    def test_retablissement_leve_le_drapeau(self):
        degradee = json.loads(json.dumps(self.saine))
        del degradee['hooks']['events']['PreToolUse']
        self.moteur.write_text(json.dumps(degradee), encoding='utf-8')
        self.call('SessionStart', source='startup')
        self.assertTrue((self.etat / 'harnais-degrade').exists())
        self.moteur.write_text(json.dumps(self.saine), encoding='utf-8')
        result = self.call('UserPromptSubmit', prompt='suite')
        self.assertFalse((self.etat / 'harnais-degrade').exists())
        self.assertNotIn('Harnais dégradé', json.dumps(result))

    def test_sans_enregistrement_silencieux(self):
        self.env['AGENT_MOTEUR_HOOKS'] = str(self.path / 'absent.json')
        result = self.call('SessionStart', source='startup')
        self.assertEqual(result, {})

    def test_lien_symbolique_vers_secret_refuse(self):
        (self.path / 'cible').mkdir()
        (self.path / 'cible' / '.env').write_text('CLE=1\n')
        (self.project / 'lien').symlink_to(self.path / 'cible' / '.env')
        for entree in ({'file_path': str(self.project / 'lien')},
                       {'command': 'cat ' + str(self.project / 'lien')}):
            out = self.call('PreToolUse', tool_name='Read' if 'file_path' in entree else 'Bash',
                            tool_input=entree)
            self.assertEqual(out['hookSpecificOutput']['permissionDecision'], 'deny', entree)

    def test_marqueur_disable_refuse_partout(self):
        marqueur = self.config / 'hooks' / 'disable-tests-locaux'
        marqueur.parent.mkdir(parents=True, exist_ok=True)
        for outil, entree in (('Write', {'file_path': str(marqueur), 'content': ''}),
                              ('Bash', {'command': 'touch ' + str(marqueur)}),
                              ('Bash', {'command': 'echo x > ' + str(marqueur)}),
                              ('Bash', {'command': 'rm -f ' + str(marqueur)})):
            out = self.call('PreToolUse', tool_name=outil, tool_input=entree)
            self.assertEqual(out['hookSpecificOutput']['permissionDecision'], 'deny', entree)

    def test_catalogue_secrets_etendu(self):
        for relatif in ('.kube/config', '.docker/config.json', '.npmrc', 'server-private.pem'):
            chemin = self.path / relatif
            chemin.parent.mkdir(parents=True, exist_ok=True)
            chemin.write_text('x\n')
            out = self.call('PreToolUse', tool_name='Read', tool_input={'file_path': str(chemin)})
            self.assertEqual(out['hookSpecificOutput']['permissionDecision'], 'deny', relatif)

    def test_shellcheck_ko_puis_repare_tient_le_stop(self):
        script = self.project / 'bof.sh'
        script.write_text('#!/bin/bash\ncat $1\n')
        self.call('UserPromptSubmit', prompt='go')
        self.call('PostToolUse', tool_input={'file_path': str(script)})
        result = self.call('Stop', reason='end_turn')
        self.assertEqual(result['decision'], 'block')
        self.assertIn('qualité', result['reason'])
        script.write_text('#!/bin/bash\ncat "$1"\n')
        self.call('PostToolUse', tool_input={'file_path': str(script)})
        result = self.call('Stop', reason='end_turn')
        self.assertNotIn('qualité', result.get('reason', ''))

    def test_config_inverifiable_tient_le_stop(self):
        (self.config / '.git').mkdir(parents=True)
        self.call('UserPromptSubmit', prompt='go')
        result = self.call('Stop', reason='end_turn')
        self.assertEqual(result['decision'], 'block')
        self.assertIn('invérifiable', result['reason'])

    def test_verrou_ecrivain_inter_sessions(self):
        cible = self.project / 'a.txt'
        cible.write_text('')
        self.call('PostToolUse', tool_input={'file_path': str(cible)})
        out = self.call('PreToolUse', tool_name='Write', session_id='autre-session',
                        tool_input={'file_path': str(self.project / 'b.txt'), 'content': ''})
        self.assertEqual(out['hookSpecificOutput']['permissionDecision'], 'deny')
        self.assertIn('un seul écrivain', out['hookSpecificOutput']['permissionDecisionReason'])
        out = self.call('PreToolUse', tool_name='Write',
                        tool_input={'file_path': str(self.project / 'b.txt'), 'content': ''})
        self.assertEqual(out, {})
        self.etat.mkdir(parents=True, exist_ok=True, mode=0o700)
        locks = self.path / 'state' / 'locks'
        for fichier in locks.glob('*.json'):
            texte = json.loads(fichier.read_text(encoding='utf-8'))
            texte['ts'] -= 7 * 3600
            fichier.write_text(json.dumps(texte), encoding='utf-8')
        out = self.call('PreToolUse', tool_name='Write', session_id='autre-session',
                        tool_input={'file_path': str(self.project / 'b.txt'), 'content': ''})
        self.assertEqual(out, {})

    def test_gitleaks_projet_tient_le_stop(self):
        self.call('UserPromptSubmit', prompt='go')
        jeton = 'ghp_' + '16C7e42F292c6912E7710c838347Ae178B4a'
        (self.project / 'cle.js').write_text('tok = "' + jeton + '"\n')
        result = self.call('Stop', reason='end_turn')
        self.assertEqual(result['decision'], 'block')
        self.assertIn('SECRETS KO', result['reason'])

    def test_environnement_des_tests_epure(self):
        code = ('import sys; sys.path.insert(0, ' + repr(str(HOOKS)) + '); from lanceur import environnement_epure; '
                'env = environnement_epure({"GH_TOKEN": "x", "SSH_AUTH_SOCK": "y", "PATH": "/bin", "CI": "1"}); '
                'assert "GH_TOKEN" not in env and "SSH_AUTH_SOCK" not in env and env["CI"] == "1", env')
        process = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True,
                                 timeout=30, check=False)
        self.assertEqual(process.returncode, 0, process.stderr)


def tearDownModule():
    shutil.rmtree(FIXTURES, ignore_errors=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
