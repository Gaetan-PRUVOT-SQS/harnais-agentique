# Feature : image-disque et qemu-test

Date : 2026-09-29

## Métier

- Besoin : un système de type Unix démarre depuis un disque qui porte un
  chargeur, un noyau, un initrd et une racine. Il faut fabriquer cette
  image sans root, la démarrer en BIOS et en UEFI, et juger le résultat
  sur la série de façon fiable, pour chaque architecture.
- Qui est concerné : L'auteur et l'agent à chaque `make test` d'un projet
  noyau ; le gabarit Unix-like s'appuie sur les deux outils.
- Impact si on ne le fait pas : images faites à la main, tests qui coupent
  trop tôt (vu : le démarrage BIOS par Limine passe de 1 s à 7 ou 8 s quand la machine compile en même temps) ou
  qui ratent un marqueur à cause des séquences ANSI de Limine en UEFI.

## Ce qu'on fait

- `image-disque --noyau K --sortie IMG [--racine D] [--initrd D]` : GPT
  avec ESP en FAT (Limine BIOS et UEFI, `limine.conf`, noyau, initrd cpio),
  racine en ext2 remplie depuis un dossier, partition de démarrage BIOS.
- `qemu-test (--noyau|--disque|--iso) [--arch] [--uefi] [--attendu]
  [--echec] [--delai]` : QEMU sans écran, série dans un fichier, verdict
  sur marqueurs, KVM si possible.
- Fichiers touchés : `scripts/image_disque.py`, `scripts/qemu_test.py`,
  `scripts/test_image_disque.py`, `scripts/test_qemu_test.py`,
  `scripts/fixtures/{racine,initrd,serie-ansi.log}`, liens
  `~/.local/bin/image-disque` et `~/.local/bin/qemu-test`.

## Choix techniques

| Choix | Pourquoi | Alternative rejetée | Impact métier |
|-------|----------|---------------------|---------------|
| GPT avec ESP, racine et partition BIOS (EF02) | Limine ne s'installe pas en BIOS sur GPT sans partition de démarrage BIOS (erreur vue) ; numéro 3 pour garder ESP en 1 et racine en 2 | MBR | une seule image pour BIOS et UEFI, anciens et récents PC |
| `mformat -i img@@offset -T`, `mkfs.ext2 -E offset= -d` | écrire une partition dans un fichier sans monter, donc sans root | `losetup` et `mount` | aucun mot de passe, reproductible |
| Limine épinglé (`LIMINE_DIR`, 12.9.1 par défaut) | même chargeur partout, version notée | GRUB | image hybride BIOS et UEFI en une commande |
| initrd cpio `newc`, liste triée, `--reproducible`, propriétaire 0 | format simple à lire côté noyau, même archive à chaque build | tar | initrd reproductible |
| Série dans un fichier lu par sondage | un tuyau perd ou bloque la sortie quand QEMU est tué | `-serial stdio` et grep | verdict fiable |
| Séquences ANSI retirées avant la recherche | en UEFI, Limine écrit chaque caractère avec une séquence de position | chercher dans le texte brut | un marqueur n'est jamais raté |
| Premier marqueur rencontré (réussite ou échec) décide | un `FAIL` avant `PASS` est un échec | le premier trouvé dans n'importe quel ordre | pas de faux vert |
| KVM pour x86 si `/dev/kvm`, sinon TCG, `--sans-kvm` pour forcer | rapide en local, même comportement sans KVM | TCG toujours | tests en quelques secondes |
| Logique pure testée, test de bout en bout qui fabrique et démarre une image en BIOS et en UEFI | la preuve réelle reste dans la suite | tests unitaires seuls | régression visible sur le vrai chemin |

## Traçabilité

| Fichier | Fonction / bloc | Justifié par |
|---------|-----------------|--------------|
| `image_disque.py` | `planifier`, `commande_gpt` | GPT et partition BIOS |
| `image_disque.py` | `remplir_esp`, `ecrire_racine` | écriture à un décalage, sans root |
| `image_disque.py` | `config_limine`, `LIMINE` | Limine épinglé |
| `image_disque.py` | `cpio` | initrd reproductible |
| `qemu_test.py` | `lire`, `ANSI` | séquences ANSI retirées, série dans un fichier |
| `qemu_test.py` | `verdict` | premier marqueur décide |
| `qemu_test.py` | `accel` | KVM ou TCG |
| `test_image_disque.py` | `test_image_demarre_en_bios_et_uefi` | test de bout en bout |
