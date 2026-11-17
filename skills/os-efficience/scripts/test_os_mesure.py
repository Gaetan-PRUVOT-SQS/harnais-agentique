from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

import pytest

ICI = Path(__file__).parent


def charger():
    chargeur = SourceFileLoader('os_mesure', str(ICI / 'os-mesure'))
    module = module_from_spec(spec_from_loader('os_mesure', chargeur))
    chargeur.exec_module(module)
    return module


om = charger()


@pytest.mark.parametrize('seuil', [1, 2, 3, 17, 63, 64])
def test_dichotomie_trouve_le_seuil(seuil):
    appels = []

    def essai(mio):
        appels.append(mio)
        return mio >= seuil

    assert om.plus_petit_qui_passe(essai, 1, 64) == seuil
    assert len(appels) <= 6
    assert 64 not in appels


def test_dichotomie_intervalle_reduit():
    assert om.plus_petit_qui_passe(lambda mio: True, 5, 5) == 5


def test_marqueur_lu_dans_la_sortie_serie():
    assert om.marqueur_vu(str(ICI / 'fixtures' / 'serie-ok.log'), 'kmain OK')
    assert not om.marqueur_vu(str(ICI / 'fixtures' / 'serie-ko.log'), 'kmain OK')
    assert not om.marqueur_vu(str(ICI / 'fixtures' / 'absente.log'), 'kmain OK')
