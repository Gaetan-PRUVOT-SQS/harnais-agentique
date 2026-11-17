import subprocess
import sys
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

import pytest
import yaml

RACINE = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / 'fixtures'
_chargeur = SourceFileLoader('verifier', str(RACINE / 'verifier'))
verifier = module_from_spec(spec_from_loader('verifier', _chargeur))
_chargeur.exec_module(verifier)


def test_budget_exclut_les_skills_manuels():
    assert verifier.entree_listing('x', {'description': 'abc', 'disable-model-invocation': True}) == 0


def test_budget_compte_nom_description_et_when_to_use():
    assert verifier.entree_listing('ab', {'description': 'cde', 'when_to_use': 'f'}) == 6


@pytest.mark.parametrize(('longueur', 'attendu'), [(1535, 1535), (1536, 1536), (1537, 1536), (4000, 1536)])
def test_budget_plafond_par_description(longueur, attendu):
    assert verifier.entree_listing('', {'description': 'x' * longueur}) == attendu


@pytest.mark.parametrize(('total', 'ok'), [(950, True), (951, False), (0, True)])
def test_budget_limite_a_95_pour_cent(total, ok):
    assert verifier.verdict_budget(total, 1000)[0] is ok


def test_budget_sur_une_fausse_config():
    ok, message = verifier.controle_budget(FIXTURES / 'propre' / 'skills', FIXTURES / 'claude')
    attendu = (len('ok') + len('Fait une chose. Use when testing.')
               + len('anthropic-skills:partage') + len('Skill du compte.')
               + len('outil:aide') + len('Skill de plugin.'))
    assert ok
    assert f'listing {attendu} caractères' in message


def test_budget_ignore_les_plugins_inactifs():
    settings = {'enabledPlugins': {'a@p': True, 'b@p': False}}
    installes = {'plugins': {'a@p': [{'installPath': 'a'}], 'b@p': [{'installPath': 'b'}]}}
    assert list(verifier.plugins_actifs(settings, installes, Path('/p'))) == [('a', Path('/p/a'))]


def test_budget_sans_variable_reprend_le_plafond_local():
    ok, message = verifier.controle_budget(
        FIXTURES / 'propre' / 'skills', FIXTURES / 'budget-sans-variable')
    assert ok
    assert '230000' in message


def test_budget_sans_dossier_claude():
    ok, message = verifier.controle_budget(
        FIXTURES / 'propre' / 'skills', FIXTURES / 'absent-liens')
    assert ok
    assert '230000' in message


def test_frontmatter_bloc_replie():
    donnees = verifier.frontmatter('---\nname: a\ndescription: >-\n  texte\n  long\n---\n# A\n')
    assert donnees == {'name': 'a', 'description': 'texte long'}


@pytest.mark.parametrize('texte', ['# pas de frontmatter\n', '---\nname: a\n', '---\n- liste\n---\n'])
def test_frontmatter_invalide(texte):
    with pytest.raises((ValueError, TypeError)):
        verifier.frontmatter(texte)


def test_frontmatter_yaml_casse():
    with pytest.raises(yaml.YAMLError):
        verifier.frontmatter('---\ndescription: [non fermé\n---\n')


def test_structure_propre():
    assert list(verifier.problemes_structure(FIXTURES / 'propre' / 'skills', FIXTURES / 'propre' / 'liens')) == []


def test_structure_sans_dossier_claude():
    assert list(verifier.problemes_structure(FIXTURES / 'propre' / 'skills', FIXTURES / 'absent-liens')) == []


def test_agents_propres():
    assert list(verifier.problemes_agents(FIXTURES / 'propre' / 'agents', FIXTURES / 'propre' / 'agents-liens')) == []


def test_agents_sans_dossier_claude():
    assert list(verifier.problemes_agents(FIXTURES / 'propre' / 'agents', FIXTURES / 'absent-liens')) == []


def test_agents_abimes():
    agents = FIXTURES / 'abime' / 'agents'
    problemes = set(verifier.problemes_agents(agents, FIXTURES / 'abime' / 'agents-liens'))
    assert problemes == {
        'nom-faux.md : name « autre » différent du fichier',
        'sans-description.md : description vide',
        'ecrivain.md : outil d\'écriture : un seul écrivain',
        'sans-outils.md : liste d\'outils absente',
        'non-lie.md : lien absent ou faux dans ' + str(FIXTURES / 'abime' / 'agents-liens'),
        'parasite.txt : fichier parasite dans agents/',
        'yaml-casse.md : frontmatter invalide (while parsing a flow sequence)',
        f'mort.md : lien mort ou hors de {agents}',
    }


def test_description_a_la_limite():
    assert verifier.probleme_description('a' * 1024) is None
    assert verifier.probleme_description('a' * 1025) == 'description de 1025 caractères, plafond 1024'
    assert verifier.probleme_description('   ') == 'description vide'


def test_structure_abimee():
    problemes = set(verifier.problemes_structure(FIXTURES / 'abime' / 'skills', FIXTURES / 'abime' / 'liens'))
    assert problemes == {
        'description-longue : description de 1025 caractères, plafond 1024',
        'nom-faux : name « autre » différent du dossier',
        'parasite.txt : fichier parasite dans skills/',
        'sans-description : description vide',
        'sans-skill : SKILL.md absent',
        'yaml-casse : frontmatter invalide (while parsing a flow sequence)',
        f'mort : lien mort ou hors de {FIXTURES / "abime" / "skills"}',
    }


@pytest.mark.parametrize(('etats', 'attendu'), [
    (['OK', 'OK'], ('Bilan : tout est vert', 0)),
    (['OK', 'NL'], ('Bilan : 0 KO, 1 non lancés', 3)),
    (['KO', 'NL', 'OK'], ('Bilan : 1 KO, 1 non lancés', 1)),
])
def test_bilan_distingue_ko_et_non_lance(etats, attendu):
    assert verifier.bilan(etats) == attendu


@pytest.mark.parametrize(('ok', 'attendu'), [(True, 'OK'), (False, 'KO'), (None, 'NL')])
def test_etat_des_controles(ok, attendu):
    assert verifier.etat(ok) == attendu


@pytest.mark.parametrize(('code', 'sortie', 'attendu'), [
    (0, '', True),
    (1, 'échec', False),
    (3, '', None),
    (2, 'tests non lancés : SDK absent\nmake: *** Error 3', None),
    (0, 'tests non lancés', True),
])
def test_verdict_code_suit_la_convention_des_hooks(code, sortie, attendu):
    assert verifier.verdict_code(code, sortie) is attendu


TOUT_LE_CODE = {
    'hooks (verify.py)', 'tests du verifier', 'ruff', 'shellcheck', 'checkbashisms',
    'baseline (cyber-scan)', 'secrets (gitleaks)', 'sast (semgrep)',
    'hooks zcode : python isolé', 'permissions : secrets sans le hook', 'harnais : CLAUDE.md étranger',
    'règle de test : phrases décisives',
}
SKILLS = {
    'skills : structure et liens', 'skills : budget du listing', 'secrets (gitleaks)',
}
AGENTS = {'agents : structure et liens'}
REGLE_TESTS = {'règle de test : phrases décisives'}


@pytest.mark.parametrize(('chemin', 'attendu'), [
    ('memory/projets/sqscore.md', set()),
    ('docs/justifications/a.md', set()),
    ('AGENTS.md', REGLE_TESTS),
    ('DESIGN.md', {'tests du verifier'}),
    ('regles/bas-niveau.md', set()),
    ('hooks/dispatch.py', TOUT_LE_CODE),
    ('hooks/gate-config-stop.sh', TOUT_LE_CODE),
    ('tests/test_verifier.py', TOUT_LE_CODE),
    ('verifier', TOUT_LE_CODE),
    ('pyproject.toml', TOUT_LE_CODE),
    ('agents/relecteur.md', AGENTS),
    ('skills/x/SKILL.md', SKILLS),
    ('skills/iso-29119/SKILL.md', SKILLS | REGLE_TESTS),
    ('skills/tests-regression-auto/SKILL.md', SKILLS | REGLE_TESTS),
    ('skills/iso-29119/docs/justifications/iso-29119.md', SKILLS),
    ('skills/x/scripts/lance.sh', SKILLS | {'shellcheck', 'checkbashisms'}),
    ('skills/x/scripts/outil', SKILLS | {'shellcheck', 'checkbashisms'}),
    ('skills/x/templates/main.c', SKILLS | {'hooks (verify.py)'}),
    ('skills/x/scripts/outil.py', SKILLS),
    ('skills/validation-gate/SKILL.md', SKILLS | {'tests du verifier'}),
    ('.cyber-ignore', {'baseline (cyber-scan)'}),
    ('.gitleaksignore', {'secrets (gitleaks)'}),
])
def test_pour_choisit_les_controles_selon_le_fichier(chemin, attendu):
    assert verifier.noms_pour(chemin) == attendu


def _blocs_clotures(texte, langue):
    blocs = []
    lignes = None
    for ligne in texte.splitlines():
        if lignes is None:
            if ligne.strip() == f'```{langue}':
                lignes = []
            continue
        if ligne.strip() == '```':
            blocs.append('\n'.join(lignes))
            lignes = None
            continue
        lignes.append(ligne)
    return blocs


def test_echantillon_validation_sans_redirection():
    texte = (RACINE / 'skills/validation-gate/SKILL.md').read_text(encoding='utf-8')
    blocs = _blocs_clotures(texte, 'bash')
    assert len(blocs) == 1
    bloc = blocs[0]
    assert '<' not in bloc
    assert bloc.startswith('set -euo pipefail\n')
    assert 'PACK' in bloc
    assert 'COUVERTURE' in bloc
    assert 'SEUIL' in bloc
    assert '<slug>' in texte
    fini = subprocess.run(['bash', '-n'], input=bloc, text=True, capture_output=True, check=False)
    assert fini.returncode == 0, fini.stderr


class _Fin:
    def __init__(self, code=0, stdout='', stderr=''):
        self.returncode = code
        self.stdout = stdout
        self.stderr = stderr


def test_controles_rapides_branchent_les_scans():
    controles = dict(verifier.controles_rapides())
    assert controles['baseline (cyber-scan)'] is verifier.controle_baseline
    assert controles['secrets (gitleaks)'] is verifier.controle_secrets
    assert controles['sast (semgrep)'] is verifier.controle_sast


def test_scans_ciblent_hooks_et_skills(monkeypatch):
    appels = []

    def faux_run(argv, **kwargs):
        appels.append((list(argv), kwargs.get('env', {})))
        return _Fin()

    monkeypatch.setattr(verifier.subprocess, 'run', faux_run)
    assert verifier.controle_baseline()[0] is True
    assert verifier.controle_secrets()[0] is True
    assert verifier.controle_sast()[0] is True
    assert [appel[0][-1] for appel in appels] == [
        str(verifier.RACINE / 'hooks'),
        str(verifier.RACINE / 'verifier'),
        str(verifier.RACINE / 'hooks'),
        str(verifier.RACINE / 'skills'),
        str(verifier.RACINE / 'hooks'),
    ]
    baseline = appels[0][0]
    assert baseline[:2] == ['bash', str(verifier.RACINE / 'hooks/cyber-scan.sh')]
    assert baseline[2:4] == ['--root', str(verifier.RACINE)]
    assert appels[1][0][2:4] == ['--root', str(verifier.RACINE)]
    secrets = appels[2][0]
    assert secrets[:6] == ['gitleaks', 'dir', '--no-banner', '--redact', '--exit-code', '2']
    assert '-r' not in secrets and '-f' not in secrets
    sast = appels[4][0]
    configs = [sast[i + 1] for i, arg in enumerate(sast) if arg == '--config']
    assert configs == ['p/python', 'p/owasp-top-ten']
    assert 'p/bash' not in sast
    assert '--json-output' not in sast
    assert appels[4][1]['SEMGREP_SEND_METRICS'] == 'off'
    assert appels[4][1]['PYTHONDONTWRITEBYTECODE'] == '1'


def test_secret_trouve_reste_ko(monkeypatch):
    def faux_run(argv, **kwargs):
        return _Fin(2, stdout='leak')

    monkeypatch.setattr(verifier.subprocess, 'run', faux_run)
    ok, sortie = verifier.controle_secrets()
    assert ok is False
    assert sortie.count('leak') == 2


def test_sast_en_echec_reste_ko(monkeypatch):
    def faux_run(argv, **kwargs):
        return _Fin(1, stdout='finding')

    monkeypatch.setattr(verifier.subprocess, 'run', faux_run)
    ok, sortie = verifier.controle_sast()
    assert ok is False
    assert 'finding' in sortie


def test_nosemgrep_du_lanceur_nomme_la_regle():
    texte = (RACINE / 'hooks/lanceur.py').read_text(encoding='utf-8')
    lignes = [ligne for ligne in texte.splitlines() if 'nosemgrep' in ligne]
    assert lignes == ['        command,  # nosemgrep: dangerous-subprocess-use-tainted-env-args']


def test_scanner_absent_nest_pas_vert(monkeypatch):
    def faux_run(argv, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(verifier.subprocess, 'run', faux_run)
    for controle in (verifier.controle_baseline, verifier.controle_secrets, verifier.controle_sast):
        ok, sortie = controle()
        assert ok is None
        assert 'non lancé' in sortie


def test_pour_garde_l_ordre_des_controles():
    controles = [('ruff', None), ('skills : budget du listing', None), ('hooks (verify.py)', None)]
    choisis = verifier.controles_pour(['skills/x/SKILL.md', 'hooks/garde.py'], controles)
    assert [nom for nom, _ in choisis] == ['ruff', 'skills : budget du listing', 'hooks (verify.py)']


def test_pour_sans_fichier_ne_garde_rien():
    assert verifier.controles_pour([], [('ruff', None)]) == []


def test_pour_developpe_un_dossier():
    racine = FIXTURES / 'propre'
    fichiers = list(verifier.fichiers_changes(['skills/', 'skills/ok/SKILL.md', 'absent.md'], racine))
    assert fichiers == ['skills/ok/SKILL.md', 'skills/ok/SKILL.md', 'absent.md']


def hooks_valides(racine=RACINE):
    evenements = {}
    for evenement, delai in verifier.DELAIS_HOOKS.items():
        groupe = {'hooks': [{
            'type': 'command',
            'command': verifier.commande_hook(racine, evenement),
            'timeout': delai,
        }]}
        if evenement in verifier.FILTRES_HOOKS:
            groupe['matcher'] = verifier.FILTRES_HOOKS[evenement]
        evenements[evenement] = [groupe]
    return {'hooks': {'enabled': True, 'events': evenements}}


def test_hooks_isoles_acceptes():
    assert list(verifier.problemes_hooks(hooks_valides(), RACINE)) == []


def test_hooks_desactives_refuses():
    donnees = hooks_valides()
    donnees['hooks']['enabled'] = False
    assert 'enabled: true attendu' in list(verifier.problemes_hooks(donnees, RACINE))


def test_hooks_nus_refuses():
    donnees = hooks_valides()
    donnees['hooks']['events']['PreToolUse'][0]['hooks'][0]['command'] = (
        f'python3 {RACINE / "hooks" / "dispatch.py"} PreToolUse'
    )
    assert list(verifier.problemes_hooks(donnees, RACINE)) == [
        f'PreToolUse : commande python3 {RACINE / "hooks" / "dispatch.py"} PreToolUse',
    ]


def test_hooks_delai_voisin_refuse():
    donnees = hooks_valides()
    donnees['hooks']['events']['PreToolUse'][0]['hooks'][0]['timeout'] = 9
    assert 'PreToolUse : délai 9' in list(verifier.problemes_hooks(donnees, RACINE))


def test_hooks_evenement_absent():
    donnees = hooks_valides()
    del donnees['hooks']['events']['Stop']
    assert 'Stop : absent' in list(verifier.problemes_hooks(donnees, RACINE))


def test_hooks_status_message_refuse():
    donnees = hooks_valides()
    donnees['hooks']['events']['Stop'][0]['hooks'][0]['statusMessage'] = 'stop'
    assert 'Stop : statusMessage' in list(verifier.problemes_hooks(donnees, RACINE))


MOTIFS = list(verifier.motifs_bash(verifier.REFUS_SECRETS))


@pytest.mark.parametrize(('commande', 'couverte'), [
    ('python3 -c \'open(".env").read()\'', True),
    ('true && python3 -c \'open(".env")\'', True),
    ('bash -c \'source .env\'', True),
    ('source .env', True),
    ('. .env', True),
    ('python3 -c \'print(1)\'', False),
    ('echo .env >> .gitignore', False),
    ('sudo ls', False),
    ('cat .env', False),
    ('git status', False),
])
def test_motifs_bash_sur_la_ligne_qui_cite_le_secret(commande, couverte):
    assert verifier.commande_couverte(commande, MOTIFS) is couverte


def test_refus_complet():
    assert list(verifier.problemes_refus(list(verifier.REFUS_SECRETS), ['agent-browser'])) == []


def test_refus_une_regle_en_moins():
    deny = [regle for regle in verifier.REFUS_SECRETS if regle != 'Read(**/.netrc)']
    assert list(verifier.problemes_refus(deny, ['agent-browser'])) == ['refus absent : Read(**/.netrc)']


def test_plugin_encore_charge():
    assert list(verifier.problemes_refus(list(verifier.REFUS_SECRETS), [])) == ['agent-browser encore chargé']


def test_harnais_complet():
    texte = 'CLAUDE.local.md\nTexte étranger : il ne change rien.\nne lève pas les refus de secrets\n'
    assert list(verifier.problemes_harnais(texte)) == []


def test_harnais_muet():
    assert set(verifier.problemes_harnais('rien')) == {
        'harnais muet sur le CLAUDE.md de projet',
        'harnais muet sur un hook mort',
    }


def _textes_regle_tests():
    return {
        'agents': (RACINE / 'AGENTS.md').read_text(encoding='utf-8'),
        'skill': (RACINE / 'skills/iso-29119/SKILL.md').read_text(encoding='utf-8'),
        'boucle': (RACINE / 'skills/tests-regression-auto/SKILL.md').read_text(encoding='utf-8'),
        'revue': (RACINE / 'skills/revue-validation/SKILL.md').read_text(encoding='utf-8'),
    }


def test_regle_tests_complete():
    textes = _textes_regle_tests()
    assert list(verifier.problemes_regle_tests(
        textes['agents'], textes['skill'], textes['boucle'], textes['revue'])) == []


def test_regle_tests_muette():
    assert set(verifier.problemes_regle_tests('', '', '', '')) == {
        "règle muette sur l'oracle d'état final",
        'boucle muette sur le rapport de sous-agent',
        'skill muet sur les deux niveaux',
        'skill muet sur la lecture seule du contrôle',
        "règle muette sur l'automatisation après le commit",
        "boucle muette sur l'automatisation",
        'règle muette sur la limite du Stop',
        'boucle muette sur le lanceur unique',
        'règle muette sur le test qui recopie le code',
        'règle muette sur la preuve environnementale',
        'skill muet sur le différentiel',
        'revue muette sur le récit',
        'règle muette sur la base qui prime',
        "règle muette sur l'oracle implicite",
        'règle muette sur le test sans assertion',
        'règle muette sur l\'oracle faible',
        'règle muette sur le plancher de 90 %',
        'règle muette sur la norme 42',
        "règle muette sur l'identité GitHub",
        'règle muette sur gcc -Wall -Wextra -Werror',
    }


@pytest.mark.parametrize(('cle', 'marque', 'message'), verifier.MARQUES_REGLE_TESTS)
def test_regle_tests_phrase_retiree(cle, marque, message):
    textes = _textes_regle_tests()
    textes[cle] = verifier.compacte(textes[cle]).replace(marque, '', 1)
    obtenu = list(verifier.problemes_regle_tests(
        textes['agents'], textes['skill'], textes['boucle'], textes['revue']))
    assert obtenu == [message]


def test_controle_regle_tests_sur_la_config():
    ok, message = verifier.controle_regle_tests()
    assert ok
    assert message == '20 phrases'


PHRASE_PLANCHER = 'au moins 90 % sur chaque couverture rapportée'
FICHIERS_PLANCHER = (
    'AGENTS.md',
    'skills/iso-29119/SKILL.md',
    'skills/iso-29119/modeles/section-tests.md',
    'skills/pratiques-dev-senior/SKILL.md',
    'skills/feature-test-pipeline/SKILL.md',
    'skills/validation-gate/SKILL.md',
    'skills/pratiques-agiles/SKILL.md',
    'skills/tests-regression-auto/SKILL.md',
    'skills/justifier-choix-techniques/SKILL.md',
)


PHRASE_GCC = 'le code C se compile avec gcc -Wall -Wextra -Werror'
FICHIERS_GCC = (
    'AGENTS.md',
    'skills/gcc/SKILL.md',
    'skills/c-systems/SKILL.md',
    'skills/make/SKILL.md',
    'skills/osdev-c/SKILL.md',
    'skills/pratiques-dev-senior/SKILL.md',
)


def test_gcc_avertissements_relus():
    for relatif in FICHIERS_GCC:
        texte = (RACINE / relatif).read_text(encoding='utf-8')
        assert PHRASE_GCC in verifier.compacte(texte), relatif


def test_plancher_couverture_relu():
    for relatif in FICHIERS_PLANCHER:
        texte = (RACINE / relatif).read_text(encoding='utf-8')
        assert PHRASE_PLANCHER in verifier.compacte(texte), relatif


def test_unit_testing_ne_fixe_plus_80():
    brut = '\n'.join(
        (RACINE / relatif).read_text(encoding='utf-8')
        for relatif in (
            'skills/unit-testing/SKILL.md',
            'skills/unit-testing/references/patterns.md',
        )
    )
    assert 'branches: 80' not in brut
    assert 'fail_under = 80' not in brut
    assert 'fail-under=80' not in brut
    assert '80% line' not in brut
    assert 'branches: 90' in brut
    assert 'fail_under = 90' in brut
    assert 'fail-under=90' in brut


def test_pour_une_note_de_memoire_ne_lance_rien():
    fini = subprocess.run([sys.executable, str(RACINE / 'verifier'), '--rapide', '--pour', 'memory/projets/x.md'],
                          capture_output=True, text=True, timeout=60, check=False)
    assert fini.returncode == 0
    assert fini.stdout.startswith('Rien à vérifier pour : memory/projets/x.md')
