from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

import image_disque as im
import qemu_test as qt

ICI = Path(__file__).parent
GABARIT = ICI.parent.parent / 'osdev-c' / 'templates' / 'i686-multiboot'
SORTIE = ICI / 'build' / 'test-image'


def test_plan_aligne_et_ordonne() -> None:
    plan = im.planifier(64, 32)
    assert plan.bios_debut == im.MIO
    assert plan.esp_debut == 2 * im.MIO
    assert plan.racine_debut == plan.esp_debut + 32 * im.MIO
    assert plan.racine_debut % im.ALIGNEMENT == 0
    assert plan.racine_debut + plan.racine_taille + im.FIN_RESERVEE == plan.taille


@pytest.mark.parametrize(('taille', 'esp'), [(64, 4), (36, 32)])
def test_plan_refuse_les_tailles_impossibles(taille: int, esp: int) -> None:
    with pytest.raises(im.Erreur):
        im.planifier(taille, esp)


def test_config_limine() -> None:
    texte = im.config_limine('velum', 'multiboot1', True, 'console=ttyS0')
    assert texte.startswith('timeout: 0\nserial: yes\n')
    assert '/velum\n    protocol: multiboot1\n    path: boot():/boot/kernel.elf\n' in texte
    assert '    cmdline: console=ttyS0\n' in texte
    assert texte.endswith('    module_path: boot():/boot/initrd.cpio\n')
    assert 'module_path' not in im.config_limine('v', 'limine', False, '')


def test_gpt_trois_partitions() -> None:
    commande = im.commande_gpt(Path('d.img'), im.planifier(64, 32))
    assert commande[:2] == ['sgdisk', '-o']
    assert '1:4096:69631' in commande
    assert '3:2048:4095' in commande
    assert '3:EF02' in commande and '1:EF00' in commande


outils = ['sgdisk', 'mformat', 'mkfs.ext2', 'cpio', 'debugfs', 'i686-elf-gcc', 'qemu-system-x86_64']
bout_en_bout = pytest.mark.skipif(
    any(shutil.which(o) is None for o in outils), reason='outils de fabrication absents'
)


@bout_en_bout
def test_image_demarre_en_bios_et_uefi() -> None:
    subprocess.run(['make', '-s', '-C', str(GABARIT), 'PROFIL=release', 'all'], check=True)
    noyau = GABARIT / 'build' / 'release-v0' / 'kernel.elf'
    image = SORTIE / 'disque.img'
    try:
        code = im.main(
            [
                '--noyau',
                str(noyau),
                '--racine',
                str(ICI / 'fixtures' / 'racine'),
                '--initrd',
                str(ICI / 'fixtures' / 'initrd'),
                '--sortie',
                str(image),
            ]
        )
        assert code == 0
        motd = subprocess.run(
            ['debugfs', '-R', 'cat /etc/motd', f'{image}?offset={34 * im.MIO}'],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        assert motd == 'bienvenue\n'
        for mode in ([], ['--uefi']):
            lancement = subprocess.run(
                [
                    'python3',
                    str(ICI / 'qemu_test.py'),
                    '--disque',
                    str(image),
                    '--arch',
                    'x86_64',
                    '--attendu',
                    'kmain OK',
                    '--echec',
                    'PANIC',
                    '--delai',
                    '60',
                    '--journal',
                    str(SORTIE / 'serie.log'),
                    *mode,
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            assert lancement.returncode == 0, lancement.stderr
            assert 'module `boot():/boot/initrd.cpio`' in qt.lire(SORTIE / 'serie.log')
    finally:
        shutil.rmtree(SORTIE, ignore_errors=True)
        subprocess.run(['make', '-s', '-C', str(GABARIT), 'clean'], check=False)
