from __future__ import annotations

import shutil
from pathlib import Path

import pytest

import qemu_test as qt


@pytest.mark.parametrize(
    ('texte', 'attendu'),
    [
        ('boot\nPASS\n', 'ok'),
        ('boot\nFAIL gdt\nPASS\n', 'echec'),
        ('PASS\nFAIL plus tard\n', 'ok'),
        ('boot\n', None),
        ('', None),
    ],
)
def test_verdict(texte: str, attendu: str | None) -> None:
    assert qt.verdict(texte, 'PASS', 'FAIL') == attendu


def test_sequences_ansi_retirees() -> None:
    journal = Path(__file__).parent / 'fixtures' / 'serie-ansi.log'
    assert qt.lire(journal) == 'multiboot1: ok\nkmain OK\n'


def test_sans_texte_d_echec() -> None:
    assert qt.verdict('FAIL\n', 'PASS', '') is None


def test_kvm_seulement_pour_x86() -> None:
    assert qt.accel('x86_64', True) == ['-accel', 'kvm', '-accel', 'tcg']
    assert qt.accel('riscv64', True) == ['-accel', 'tcg']
    assert qt.accel('i386', False) == ['-accel', 'tcg']


def test_commande_disque_bios(tmp_journal: Path) -> None:
    arguments = qt.analyser(['--disque', 'd.img', '--arch', 'i386', '--', '-smp', '2'])
    cmd = qt.commande(arguments, tmp_journal, False)
    assert cmd[0] == 'qemu-system-i386'
    assert cmd[-4:-2] == ['-drive', 'file=d.img,format=raw']
    assert cmd[-2:] == ['-smp', '2']
    assert f'file:{tmp_journal}' in cmd


def test_commande_riscv_noyau(tmp_journal: Path) -> None:
    arguments = qt.analyser(['--noyau', 'k.elf', '--arch', 'riscv64'])
    cmd = qt.commande(arguments, tmp_journal, True)
    assert cmd[1:3] == ['-M', 'virt']
    assert cmd[cmd.index('-bios') : cmd.index('-bios') + 2] == ['-bios', 'default']
    assert cmd[-2:] == ['-kernel', 'k.elf']


def test_uefi_refuse_sur_i386(tmp_journal: Path) -> None:
    arguments = qt.analyser(['--disque', 'd.img', '--arch', 'i386', '--uefi'])
    with pytest.raises(qt.Erreur):
        qt.commande(arguments, tmp_journal, False)


def faux_firmware(dossier: Path, nom: str) -> tuple[Path, Path]:
    dossier.mkdir(parents=True, exist_ok=True)
    code, modele = dossier / f'{nom}_CODE.fd', dossier / f'{nom}_VARS.fd'
    code.write_bytes(b'code')
    modele.write_bytes(b'vars ' + nom.encode())
    return code, modele


def test_uefi_x86_64_prend_le_premier_firmware_present(
    tmp_journal: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dossier = tmp_journal.parent / 'firmware'
    absent = (dossier / 'absent_CODE.fd', dossier / 'absent_VARS.fd')
    present = faux_firmware(dossier, 'present')
    monkeypatch.setitem(
        qt.FIRMWARES, 'x86_64', (absent, present, faux_firmware(dossier, 'suivant'))
    )
    copie = dossier / 'vars.fd'
    try:
        options = qt.firmware_uefi('x86_64', copie)
        assert options[1] == f'if=pflash,format=raw,unit=0,readonly=on,file={present[0]}'
        assert options[3] == f'if=pflash,format=raw,unit=1,file={copie}'
        assert copie.read_bytes() == b'vars present'
    finally:
        shutil.rmtree(dossier)


def test_uefi_firmware_absent_cite_les_emplacements(
    tmp_journal: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dossier = tmp_journal.parent / 'firmware-absent'
    paires = (
        (dossier / 'a_CODE.fd', dossier / 'a_VARS.fd'),
        (dossier / 'b_CODE.fd', dossier / 'b_VARS.fd'),
    )
    monkeypatch.setitem(qt.FIRMWARES, 'x86_64', paires)
    with pytest.raises(qt.Erreur, match=r'a_CODE\.fd.*b_CODE\.fd'):
        qt.firmware_uefi('x86_64', dossier / 'vars.fd')


@pytest.fixture
def tmp_journal() -> Path:
    return Path(__file__).parent / 'build' / 'qemu-test' / 'serie.log'
