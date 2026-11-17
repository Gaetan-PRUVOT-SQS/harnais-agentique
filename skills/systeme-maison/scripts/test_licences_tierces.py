from __future__ import annotations

import shutil
from pathlib import Path

import pytest

import licences_tierces as lt

ICI = Path(__file__).parent
EXEMPLE = ICI.parent / 'exemples' / 'projet-reuse'
FIXTURES = ICI / 'fixtures'


def fichier(chemin: str, *licences: str) -> lt.Fichier:
    return {'path': chemin, 'spdx_expressions': [{'value': v} for v in licences]}


def test_tout_maison() -> None:
    maison, tiers, refuses = lt.classer(
        [fichier('a.c', 'GPL-2.0-or-later')], 'GPL-2.0-or-later', set()
    )
    assert (maison, tiers, refuses) == (['a.c'], {}, [])


def test_tiers_refuse_par_defaut_puis_autorise() -> None:
    fichiers = [fichier('a.c', 'GPL-2.0-or-later'), fichier('t/b.c', 'MIT')]
    _, tiers, refuses = lt.classer(fichiers, 'GPL-2.0-or-later', set())
    assert tiers == {'MIT': ['t/b.c']}
    assert refuses == ['t/b.c']
    assert lt.classer(fichiers, 'GPL-2.0-or-later', {'MIT'})[2] == []


def test_expressions_composees() -> None:
    double = fichier('c.c', 'GPL-2.0-or-later', 'MIT')
    assert lt.expression(double) == 'GPL-2.0-or-later AND MIT'
    assert lt.classer([double], 'GPL-2.0-or-later', {'MIT'})[2] == []
    avec = fichier('d.c', 'GPL-3.0-or-later WITH GCC-exception-3.1')
    assert lt.identifiants(lt.expression(avec)) == {'GPL-3.0-or-later', 'GCC-exception-3.1'}
    assert lt.classer([avec], 'MIT', {'GPL-3.0-or-later'})[2] == ['d.c']


@pytest.mark.parametrize(
    'texte',
    [
        '# it under the terms of the GNU General Public License as published by',
        ' * Permission is hereby granted, free of charge, to any person',
        '/* SPDX-License-Identifier: BSD-2-Clause */',
        'Copyright (c) 1994 Someone',
    ],
)
def test_textes_de_licence_reperes(texte: str) -> None:
    assert lt.marqueurs_trouves(texte)


def test_code_ordinaire_sans_marqueur() -> None:
    assert lt.marqueurs_trouves('int\tun(void)\n{\n\treturn (1);\n}\n') == []


def test_readme_hors_recherche() -> None:
    assert not lt.est_source(Path('README.md'))
    assert lt.est_source(Path('Makefile'))
    assert lt.est_source(Path('boot.S'))


reuse_requis = pytest.mark.skipif(shutil.which('reuse') is None, reason='reuse absent')


@reuse_requis
def test_exemple_refuse_le_mit_sauf_autorise(capsys: pytest.CaptureFixture[str]) -> None:
    assert lt.main(['--licence-projet', 'GPL-2.0-or-later', '--dir', str(EXEMPLE)]) == 1
    assert 'licence tierce non autorisée : tiers/mini/deux.c' in capsys.readouterr().out
    assert (
        lt.main(
            ['--licence-projet', 'GPL-2.0-or-later', '--autorisees', 'MIT', '--dir', str(EXEMPLE)]
        )
        == 0
    )
    assert 'code tiers MIT : tiers/mini/deux.c' in capsys.readouterr().out


@reuse_requis
def test_copie_non_declaree_trouvee(capsys: pytest.CaptureFixture[str]) -> None:
    dossier = FIXTURES / 'copie-non-declaree'
    assert lt.main(['--licence-projet', 'MIT', '--dir', str(dossier)]) == 1
    sortie = capsys.readouterr().out
    assert 'copie non déclarée ? src/copie.py' in sortie
    assert 'src/propre.py' not in sortie.split('copie non déclarée')[-1]


@reuse_requis
def test_projet_sans_reuse_non_conforme(capsys: pytest.CaptureFixture[str]) -> None:
    assert lt.main(['--licence-projet', 'MIT', '--dir', str(FIXTURES / 'sans-reuse')]) == 1
    assert 'non conforme REUSE' in capsys.readouterr().out


def exception(chemin: str, *marqueurs: str, raison: str = 'donnée') -> dict[str, object]:
    return {'chemin': chemin, 'marqueurs': list(marqueurs), 'raison': raison}


def test_exception_ne_tolere_que_ses_marqueurs() -> None:
    exceptions = lt.analyser_exceptions(
        {'exception': [exception('a.py', 'Permission is hereby granted')]}
    )
    soupcons = {'a.py': ['Permission is hereby granted', 'SPDX-License-Identifier']}
    restants, appliquees, perimees = lt.appliquer_exceptions(soupcons, exceptions)
    assert restants == {'a.py': ['SPDX-License-Identifier']}
    assert (appliquees, perimees) == (['a.py'], [])


def test_exception_insensible_a_la_casse() -> None:
    exceptions = lt.analyser_exceptions({'exception': [exception('a.py', 'Copyright (c)')]})
    assert lt.appliquer_exceptions({'a.py': ['COPYRIGHT (C)']}, exceptions)[0] == {}


def test_exception_perimee_signalee() -> None:
    exceptions = lt.analyser_exceptions(
        {'exception': [exception('a.py', 'Copyright (c)', 'SPDX-License-Identifier')]}
    )
    _, _, perimees = lt.appliquer_exceptions({'a.py': ['Copyright (c)']}, exceptions)
    assert perimees == ['a.py : spdx-license-identifier']
    assert lt.appliquer_exceptions({}, exceptions)[2] != []


@pytest.mark.parametrize(
    'donnees',
    [
        {'exception': [exception('a.py', 'Copyright (c)', raison='  ')]},
        {'exception': [exception('a.py')]},
        {'exception': [exception('a.py', 'bonjour')]},
        {'exception': [exception('', 'Copyright (c)')]},
        {'exception': [{'chemin': 'a.py', 'marqueurs': ['Copyright (c)']}]},
        {'exception': [exception('a.py', 'Copyright (c)'), exception('a.py', 'Copyright (c)')]},
        {'autre': []},
    ],
)
def test_exceptions_mal_formees_refusees(donnees: dict[str, object]) -> None:
    with pytest.raises(lt.Erreur):
        lt.analyser_exceptions(donnees)


def test_fichier_explicite_absent_refuse() -> None:
    with pytest.raises(lt.Erreur):
        lt.lire_exceptions(FIXTURES / 'inexistant.toml', True)
    assert lt.lire_exceptions(FIXTURES / 'inexistant.toml', False) == {}


@reuse_requis
def test_exception_declaree_acceptee(capsys: pytest.CaptureFixture[str]) -> None:
    dossier = FIXTURES / 'exception-declaree'
    assert lt.main(['--licence-projet', 'MIT', '--dir', str(dossier)]) == 0
    assert 'exception déclarée : src/cherche.py (motif recherché' in capsys.readouterr().out
    vide = FIXTURES / 'copie-non-declaree' / 'REUSE.toml'
    assert (
        lt.main(['--licence-projet', 'MIT', '--dir', str(dossier), '--exceptions', str(vide)]) == 1
    )
