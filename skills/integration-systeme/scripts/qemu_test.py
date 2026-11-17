#!/usr/bin/env python3
"""Démarre un système dans QEMU sans écran et juge sa sortie série.

qemu-test (--noyau ELF | --disque IMG | --iso ISO) [--arch i386] [--uefi]
          [--attendu PASS] [--echec FAIL] [--delai 60] [--memoire 128M]
          [--journal build/qemu-test/serie.log] [-- ARGS_QEMU...]
    Code 0 si le texte attendu apparaît, 1 sur le texte d'échec, un arrêt
    de QEMU ou le délai dépassé. KVM si possible, sinon émulation.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ARCHS = ('i386', 'x86_64', 'aarch64', 'riscv64', 'arm')
ANSI = re.compile(r'\x1b\[[0-9;=?]*[A-Za-z]')
EDK2 = Path('/usr/share/edk2')
FIRMWARES: dict[str, tuple[tuple[Path, Path], ...]] = {
    'x86_64': (
        (EDK2 / 'ovmf/OVMF_CODE.fd', EDK2 / 'ovmf/OVMF_VARS.fd'),
        (Path('/usr/share/OVMF/OVMF_CODE_4M.fd'), Path('/usr/share/OVMF/OVMF_VARS_4M.fd')),
    ),
    'aarch64': (
        (EDK2 / 'aarch64/QEMU_EFI-pflash.raw', EDK2 / 'aarch64/vars-template-pflash.raw'),
        (Path('/usr/share/AAVMF/AAVMF_CODE.fd'), Path('/usr/share/AAVMF/AAVMF_VARS.fd')),
    ),
    'riscv64': (
        (EDK2 / 'riscv/RISCV_VIRT_CODE.fd', EDK2 / 'riscv/RISCV_VIRT_VARS.fd'),
        (
            Path('/usr/share/qemu-efi-riscv64/RISCV_VIRT_CODE.fd'),
            Path('/usr/share/qemu-efi-riscv64/RISCV_VIRT_VARS.fd'),
        ),
    ),
}


class Erreur(Exception):
    pass


def machine(arch: str) -> list[str]:
    if arch == 'x86_64':
        return ['-M', 'q35']
    if arch == 'aarch64':
        return ['-M', 'virt', '-cpu', 'cortex-a72']
    if arch == 'arm':
        return ['-M', 'virt', '-cpu', 'cortex-a15']
    if arch == 'riscv64':
        return ['-M', 'virt']
    return []


def accel(arch: str, kvm: bool) -> list[str]:
    if kvm and arch in ('i386', 'x86_64'):
        return ['-accel', 'kvm', '-accel', 'tcg']
    return ['-accel', 'tcg']


def firmware_present(arch: str) -> tuple[Path, Path]:
    paires = FIRMWARES.get(arch)
    if paires is None:
        raise Erreur(f'UEFI non géré pour {arch}')
    for code, modele in paires:
        if code.is_file() and modele.is_file():
            return code, modele
    raise Erreur('firmware UEFI absent : ' + ', '.join(str(code) for code, _ in paires))


def firmware_uefi(arch: str, vars_copie: Path) -> list[str]:
    code, modele = firmware_present(arch)
    shutil.copyfile(modele, vars_copie)
    return [
        '-drive',
        f'if=pflash,format=raw,unit=0,readonly=on,file={code}',
        '-drive',
        f'if=pflash,format=raw,unit=1,file={vars_copie}',
    ]


def source(arguments: argparse.Namespace) -> list[str]:
    if arguments.noyau:
        return ['-kernel', str(arguments.noyau)]
    if arguments.iso:
        return ['-cdrom', str(arguments.iso)]
    if arguments.arch in ('aarch64', 'riscv64', 'arm'):
        return [
            '-drive',
            f'file={arguments.disque},format=raw,if=none,id=d0',
            '-device',
            'virtio-blk-device,drive=d0',
        ]
    return ['-drive', f'file={arguments.disque},format=raw']


def commande(arguments: argparse.Namespace, journal: Path, kvm: bool) -> list[str]:
    cmd = [
        f'qemu-system-{arguments.arch}',
        *machine(arguments.arch),
        *accel(arguments.arch, kvm),
        '-m',
        arguments.memoire,
        '-display',
        'none',
        '-no-reboot',
        '-serial',
        f'file:{journal}',
        '-monitor',
        'none',
    ]
    if arguments.uefi:
        cmd += firmware_uefi(arguments.arch, journal.with_name('vars.fd'))
    elif arguments.arch == 'riscv64':
        cmd += ['-bios', 'default']
    return [*cmd, *source(arguments), *arguments.qemu]


def verdict(texte: str, attendu: str, echec: str) -> str | None:
    position_ok = texte.find(attendu)
    position_ko = texte.find(echec) if echec else -1
    if position_ko != -1 and (position_ok == -1 or position_ko < position_ok):
        return 'echec'
    if position_ok != -1:
        return 'ok'
    return None


def lire(journal: Path) -> str:
    if not journal.is_file():
        return ''
    return ANSI.sub('', journal.read_text(errors='replace')).replace('\r', '')


def attendre(proc: subprocess.Popen[bytes], journal: Path, arguments: argparse.Namespace) -> str:
    fin = time.monotonic() + arguments.delai
    while time.monotonic() < fin:
        resultat = verdict(lire(journal), arguments.attendu, arguments.echec)
        if resultat:
            return resultat
        if proc.poll() is not None:
            return verdict(lire(journal), arguments.attendu, arguments.echec) or 'arret'
        time.sleep(0.1)
    return 'delai'


def analyser(argv: list[str]) -> argparse.Namespace:
    qemu: list[str] = []
    if '--' in argv:
        i = argv.index('--')
        argv, qemu = argv[:i], argv[i + 1 :]
    parseur = argparse.ArgumentParser(
        prog='qemu-test', description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    cible = parseur.add_mutually_exclusive_group(required=True)
    cible.add_argument('--noyau', type=Path)
    cible.add_argument('--disque', type=Path)
    cible.add_argument('--iso', type=Path)
    parseur.add_argument('--arch', choices=ARCHS, default='i386')
    parseur.add_argument('--uefi', action='store_true')
    parseur.add_argument('--attendu', default='PASS')
    parseur.add_argument('--echec', default='FAIL')
    parseur.add_argument('--delai', type=float, default=60)
    parseur.add_argument('--memoire', default='128M')
    parseur.add_argument('--journal', type=Path, default=Path('build/qemu-test/serie.log'))
    parseur.add_argument('--sans-kvm', action='store_true')
    arguments = parseur.parse_args(argv)
    arguments.qemu = qemu
    return arguments


def main(argv: list[str]) -> int:
    arguments = analyser(argv)
    journal: Path = arguments.journal
    journal.parent.mkdir(parents=True, exist_ok=True)
    journal.unlink(missing_ok=True)
    kvm = not arguments.sans_kvm and os.access('/dev/kvm', os.R_OK | os.W_OK)
    try:
        cmd = commande(arguments, journal, kvm)
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except (Erreur, FileNotFoundError) as erreur:
        print(f'qemu-test : {erreur}', file=sys.stderr)
        return 1
    debut = time.monotonic()
    try:
        resultat = attendre(proc, journal, arguments)
    finally:
        proc.terminate()
        _, erreurs = proc.communicate()
    duree = time.monotonic() - debut
    if resultat == 'ok':
        print(f'qemu-test : « {arguments.attendu} » en {duree:.1f} s ({"KVM" if kvm else "TCG"})')
        return 0
    print(
        f'qemu-test : {resultat} après {duree:.1f} s, fin du journal {journal} :', file=sys.stderr
    )
    print('\n'.join(lire(journal).splitlines()[-15:]), file=sys.stderr)
    if resultat == 'arret' and erreurs:
        print(erreurs.decode(errors='replace')[-500:], file=sys.stderr)
    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
