---
name: poste-dev
description: >-
  Parallélisme, ccache, lld et KVM selon le poste mesuré dans specs.md. Use when compiling, linking, choosing a job count, or launching QEMU or an Android emulator on this machine.
---

# Poste de dev

Les chiffres mesurés sont dans `~/.agents/memory/machine/specs.md`. On les relit, on ne les récite pas de mémoire. S'ils divergent de `nproc` et `free -h`, on remesure et on met la fiche à jour.

Ce skill dit comment s'en servir. Il ne change pas le niveau du code (`pratiques-dev-senior`) ni les flags du langage (`rust`, `gcc`, le Makefile du projet).

## Jobs

12 threads, environ 14,5 Gio. Un `gcc -j12` tient quand la RAM libre est large. Un `rustc` ou un link C++ sur les 12 threads en même temps peut faire swapper, et le swap est un fichier sur le même NVMe.

- `MemAvailable` au-dessus de 8 Gio, et rien d'autre de gros (émulateur Android, Gradle, QEMU en TCG) : `-j12`.
- Entre 4 et 8 Gio libres, ou un de ces gros à côté : `-j8`.
- En dessous de 4 Gio : `-j4`.
- Jamais plus que `nproc`.

`make -jN -Otarget` quand on lance make nous-mêmes. Un Makefile qui fixe déjà son `-j` garde le sien. Cargo, sur une crate ordinaire, garde son défaut (`nproc`). Un gros workspace : `-j8`.

Si `free` montre du swap qui monte pendant le build, on coupe les jobs. On ne « pousse » pas jusqu'à remplir les 4 Gio.

## Cache et lien

- gcc et les cross apt passent par ccache : `/usr/lib/ccache` est inséré devant `/usr/bin` dans le bloc workflow de `~/.bashrc`, après l'activation de mise, pour que le clang de mise reste devant. On ne vide pas le cache. 5 Gio suffisent.
- Le clang de mise n'est pas un lien ccache. Rebuild répété : `ccache clang`.
- Le lien hôte Rust (`x86_64-unknown-linux-gnu`) utilise LLD, via `~/.cargo/config.toml`. gcc et clang du système acceptent `-fuse-ld=lld`. Un crate de contrôle, effacé ensuite, a lié : la section `.comment` du binaire dit `Linker: LLD 23.1.1`, celle livrée avec rustc 1.99 (la LLD Ubuntu est la 21.1.8). Un projet qui a déjà son linker (script de lien, freestanding, cross) ne reçoit pas ce flag : la config cargo ne vise que la cible hôte.
- Pas de `mold` sur la machine. On ne l'installe pas pour un build.
- Pas de `-march=native`, pas de `target-cpu=native`, pas de `RUSTFLAGS` global. Ça casse le cross, le freestanding et un binaire reproductible. `znver3` seulement si le binaire reste sur cette machine et que le projet l'écrit dans ses propres flags.

## QEMU et Android

- Test x86 sur cet hôte : KVM (`-enable-kvm` ou `-accel kvm`). `/dev/kvm` est ouvert pour l'utilisateur. Le TCG sur la même arch est réservé à une comparaison explicite.
- arm, aarch64, riscv : TCG, c'est le seul mode. Un de ces QEMU compte comme un gros à côté d'un `-j12`.
- Émulateur Android : image x86_64, KVM. On ne le démarre pas en même temps qu'un `-j12` ou qu'un gros Gradle. Si on écrit le `gradle.properties` d'un projet : `org.gradle.workers.max=8` et un tas autour de 4 Gio, pour laisser la place à l'émulateur. Pas de `gradle.properties` global.

## Où builder

Sur le NVMe, dans les dossiers de build du projet (`build/`, `target/`). Pas de disque mémoire, pas de copie vers `/tmp` (`tests-locaux`). Il y a une RTX 2050 en prime on-demand, mais pas de toolkit CUDA (`nvcc`) : on ne suppose pas `nvcc`.

## Références

- Fiche : `~/.agents/memory/machine/specs.md`, mesure du 2026-10-27.
- ccache 4.12.3, LLD Ubuntu 21.1.8, pilote `intel_pstate`.
