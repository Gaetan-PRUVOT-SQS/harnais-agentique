from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

import ecrire_image as ei

MIO = 1 << 20
LIMITE = ei.TAILLE_MAX_GIO * ei.GIO
ICI = Path(__file__)


def cle(**champs: Any) -> ei.Disque:
    disque: ei.Disque = {
        'name': 'sdb',
        'path': '/dev/sdb',
        'type': 'disk',
        'tran': 'usb',
        'rm': True,
        'size': 16 * ei.GIO,
        'model': 'Cle',
        'serial': 'X1',
        'mountpoints': [None],
        'children': [
            {
                'name': 'sdb1',
                'path': '/dev/sdb1',
                'type': 'part',
                'tran': 'usb',
                'size': 16 * ei.GIO - MIO,
                'mountpoints': [None],
            }
        ],
    }
    disque.update(champs)
    return disque


def disque_systeme() -> ei.Disque:
    racine = {'name': 'luks', 'type': 'crypt', 'mountpoints': ['/', '/home']}
    return {
        'name': 'nvme0n1',
        'path': '/dev/nvme0n1',
        'type': 'disk',
        'tran': 'nvme',
        'rm': False,
        'size': 238 * ei.GIO,
        'mountpoints': [],
        'children': [
            {'name': 'nvme0n1p1', 'type': 'part', 'mountpoints': ['/boot/efi']},
            {'name': 'nvme0n1p2', 'type': 'part', 'mountpoints': [None], 'children': [racine]},
        ],
    }


def disques_internes() -> list[str]:
    if not ei.PAR_ID.is_dir():
        return []
    return sorted(
        str(p)
        for p in ei.PAR_ID.iterdir()
        if p.name.startswith(('nvme-', 'ata-')) and '-part' not in p.name
    )


def test_cle_usb_acceptee() -> None:
    assert ei.refus_cible(cle(), 64 * MIO, None, LIMITE) == []


def test_cle_usb_sans_bit_amovible_acceptee() -> None:
    assert ei.refus_cible(cle(rm=False), 64 * MIO, None, LIMITE) == []


def test_partition_refusee() -> None:
    raisons = ei.refus_cible(cle(type='part', path='/dev/sdb1'), 64 * MIO, None, LIMITE)
    assert any('disque entier' in r for r in raisons)


def test_disque_systeme_refuse_meme_monte_sous_luks() -> None:
    raisons = ei.refus_cible(disque_systeme(), 64 * MIO, None, LIMITE)
    assert any('transport nvme' in r for r in raisons)
    assert any('/boot/efi' in r and '/home' in r for r in raisons)


def test_cle_montee_par_le_bureau_refusee() -> None:
    enfant = {'name': 'sdb1', 'type': 'part', 'mountpoints': ['/run/media/g/CLE']}
    raisons = ei.refus_cible(cle(children=[enfant]), 64 * MIO, None, LIMITE)
    assert raisons == [r for r in raisons if 'udisksctl unmount' in r]
    assert len(raisons) == 1


def test_carte_sd_acceptee_emmc_refusee() -> None:
    carte = cle(name='mmcblk0', path='/dev/mmcblk0', tran=None)
    assert ei.refus_cible(carte, 64 * MIO, 'SD', LIMITE) == []
    assert ei.refus_cible(carte, 64 * MIO, 'MMC', LIMITE) != []
    assert ei.refus_cible(carte, 64 * MIO, None, LIMITE) != []


def test_image_plus_grande_que_la_cle() -> None:
    raisons = ei.refus_cible(cle(size=8 * MIO), 64 * MIO, None, LIMITE)
    assert any('image de' in r for r in raisons)


def test_gros_disque_refuse_sauf_limite_levee() -> None:
    gros = cle(size=2000 * ei.GIO)
    assert any('--taille-max' in r for r in ei.refus_cible(gros, MIO, None, LIMITE))
    assert ei.refus_cible(gros, MIO, None, 4000 * ei.GIO) == []


@pytest.mark.parametrize(
    ('chemin', 'attendu'),
    [
        ('/dev/sdb', 'by-id'),
        ('/dev/disk/by-path/pci-0000:00:14.0-usb-0:1:1.0-scsi-0:0:0:0', 'by-id'),
        ('/dev/disk/by-idx/usb-X', 'by-id'),
        ('/dev/disk/by-id/usb-Cle_X1-0:0-part1', 'partition'),
    ],
)
def test_chemin_refuse(chemin: str, attendu: str) -> None:
    raison = ei.refus_chemin(chemin)
    assert raison is not None
    assert attendu in raison


def test_chemin_par_id_accepte() -> None:
    assert ei.refus_chemin('/dev/disk/by-id/usb-Cle_X1-0:0') is None


def test_commande_sans_injection_et_pkexec_si_besoin() -> None:
    piege = '/home/g/os "; rm -rf ~ #.iso'
    directe = ei.commande_ecriture(piege, '/dev/sdb', 42, True, '/usr/bin/sh')
    assert directe == ['/usr/bin/sh', '-c', ei.ECRITURE, 'ecrire-image', piege, '/dev/sdb', '42']
    elevee = ei.commande_ecriture(piege, '/dev/sdb', 42, False, '/usr/bin/sh')
    assert elevee == ['pkexec', *directe]


def test_script_verifie_la_relecture() -> None:
    assert 'conv=fsync' in ei.ECRITURE
    assert 'blockdev --flushbufs' in ei.ECRITURE
    assert 'cmp -n "$3"' in ei.ECRITURE


def test_points_de_montage_ignore_les_vides() -> None:
    assert ei.points_de_montage({'mountpoints': None}) == []
    assert ei.points_de_montage(cle()) == []


def test_main_image_absente(capsys: pytest.CaptureFixture[str]) -> None:
    code = ei.main([str(ICI.with_name('absente.iso')), '/dev/disk/by-id/usb-X'])
    assert code == 1
    assert "n'est pas un fichier" in capsys.readouterr().err


def test_main_refuse_dev_sdx(capsys: pytest.CaptureFixture[str]) -> None:
    assert ei.main([str(ICI), '/dev/sdb']) == 1
    assert '/dev/disk/by-id/' in capsys.readouterr().err


def test_main_cible_debranchee(capsys: pytest.CaptureFixture[str]) -> None:
    assert ei.main([str(ICI), '/dev/disk/by-id/usb-Absente_0-0:0']) == 1
    assert 'aucun périphérique bloc' in capsys.readouterr().err


def test_main_refuse_le_vrai_disque_du_poste(capsys: pytest.CaptureFixture[str]) -> None:
    internes = disques_internes()
    if not internes:
        pytest.skip('aucun disque interne visible dans /dev/disk/by-id')
    assert ei.main([str(ICI), internes[0]]) == 1
    erreur = capsys.readouterr().err
    assert 'cible refusée' in erreur
    assert 'ni clé USB ni carte SD' in erreur


def test_ecrire_refuse_si_la_cible_a_change() -> None:
    with pytest.raises(ei.Refus, match='changé de nœud'):
        ei.ecrire(ICI, '/dev/disk/by-id/usb-Absente_0-0:0', '/dev/sdz', 1)


def test_taille_max_nulle_refusee() -> None:
    with pytest.raises(SystemExit):
        ei.analyser(['a.iso', '/dev/disk/by-id/usb-X', '--taille-max', '0'])
