---
name: fichiers-unix
description: >-
  Fichiers d'un noyau de type Unix : descripteurs, VFS, droits, /dev, tuyaux, initrd cpio, ext2, cache de blocs, MBR et GPT. Use when implementing open/read/write, path lookup or a filesystem.
---

# Fichiers de type Unix

« Tout est fichier » repose sur trois tables et une interface commune. Le
reste (ext2, tuyaux, /dev) se branche dessous. Les images de test se
fabriquent sur l'hôte et se vérifient avec les outils de l'hôte.

Voisins : processus-unix (fork partage les fichiers ouverts),
pilotes-materiel (ATA, AHCI, virtio-blk, NVMe), integration-systeme
(`image-disque`), gestion-memoire (cache), noyau-securite (entrées non
fiables), os-confidentialite (droits), unix-freebsd-linux (leçons de
FreeBSD et Linux).

## Trois tables

- Par processus : table des descripteurs (entier vers fichier ouvert,
  drapeau `FD_CLOEXEC`).
- Fichier ouvert (partagé après `fork` et `dup`) : inode, position, mode
  (`O_RDONLY`, `O_WRONLY`, `O_RDWR`, `O_APPEND`, `O_NONBLOCK`), compteur.
- Inode en mémoire, un par fichier actif : type, taille, droits, uid et
  gid, liens, opérations de son système de fichiers, compteur.
- Conséquence : `dup` et `fork` partagent la position, deux `open` du même
  fichier non.
- Tout appel qui crée un descripteur accepte `O_CLOEXEC` (`open`, `pipe2`,
  `dup3`, `accept4`) ; la libc le pose par défaut.

## VFS

- Interface commune : `lookup`, `create`, `read`, `write`, `getdents`,
  `truncate`, `unlink`, `mkdir`, `rmdir`, `rename`, `stat`. ramfs,
  ext2, devfs et tuyaux la remplissent.
- Montages : table point de montage vers racine du système monté ; la
  résolution traverse les montages ; `..` à la racine d'un montage remonte
  au parent.
- Résolution : absolue depuis la racine, relative depuis le dossier
  courant ; `.`, `..`, `//` ; composant de `NAME_MAX` au plus, chemin de
  `PATH_MAX` ; droit x sur chaque dossier traversé ; liens symboliques plus
  tard, avec une profondeur limitée (`ELOOP`).
- Noms : ni `/` ni octet nul ; longueur et contenu validés avant tout.
  POSIX.1-2024 : `open` doit échouer avec `EILSEQ` si le dernier
  composant n'est pas un nom portable et ne peut pas être créé, et il est
  encouragé à refuser la création d'un nom qui contient un saut de ligne.
- Appels `*at` (descripteur de dossier) dès la première version ; `open`
  n'en est qu'un cas. Résolution bornée en option (idée de
  `O_RESOLVE_BENEATH` chez FreeBSD et `RESOLVE_BENEATH` d'`openat2` chez
  Linux) : vérifiée à chaque composant, ni `..` au-dessus du dossier de
  départ, ni chemin absolu, ni lien qui sort. C'est la base d'un bac à
  sable par dossier.
- Cache de noms plus tard, si la mesure le demande.

## Droits

- Mode (type, rwx pour propriétaire, groupe, autres), uid et gid réels et
  effectifs, `umask`. Root passe les droits, sauf l'exécution sans aucun
  bit x. Pas de setuid au début (moindre privilège).
- Droits vérifiés à l'ouverture ; le fichier ouvert garde son mode.

## Fichiers spéciaux

- `/dev` par un système dédié : `console`, `tty`, `null`, `zero`,
  `random` (pool de noyau-securite), disques et partitions.
- Tuyau : tampon circulaire d'au moins 4 Kio, lecteurs et écrivains
  comptés. Lecture sur tuyau vide : attente tant qu'un écrivain existe,
  sinon 0 (fin de fichier). Écriture sans lecteur : SIGPIPE et `EPIPE`.
  Écritures de moins de `PIPE_BUF` atomiques.
- Non bloquant : `EAGAIN`.

## Initrd

- cpio `newc` : magic `070701`, treize champs hexadécimaux de 8
  caractères, nom, alignement sur 4, fin sur `TRAILER!!!`. Décodé dans un
  ramfs au boot : racine disponible avant tout pilote disque.
  `image-disque --initrd` le fabrique, de façon reproductible.
- ramfs : inodes en mémoire, données en pages.

## ext2 depuis sa spec

- Superbloc à l'octet 1024 (magic 0xEF53), bloc de `1024 <<
  s_log_block_size`, groupes et leur table de descripteurs, bitmaps de
  blocs et d'inodes, table d'inodes (`s_inode_size` en révision 1), inode
  racine 2, 12 blocs directs puis indirect, double et triple, entrées de
  dossier de longueur variable (`rec_len`, `name_len`, type). Tout en
  little-endian.
- Lecture seule d'abord. Écriture ensuite : allocation de blocs et
  d'inodes, compteurs du superbloc et des groupes, ordre des écritures qui
  laisse un système réparable après coupure.
- Fonctions du superbloc : refuser de monter en écriture si une fonction
  incompat ou ro_compat inconnue est présente ; fabriquer les images de
  test avec les seules fonctions gérées (`mkfs.ext2 -O ^dir_index`...).
- Tout champ lu du disque est une entrée non fiable : numéros de bloc et
  d'inode bornés, `rec_len` vérifié (sinon boucle sans fin ou lecture hors
  tampon).

## Couche bloc

- Pilote bloc qui lit et écrit des secteurs : ATA PIO d'abord, puis AHCI ;
  virtio-blk sous QEMU ARM et RISC-V ; NVMe (pilotes-materiel).
- Partitions : MBR (quatre entrées à 0x1BE, signature 0x55AA) et GPT
  (en-tête au LBA 1, signature `EFI PART`, CRC32 de l'en-tête et des
  entrées vérifiés, entrées de 128 octets, GUID de type). Chaque partition
  devient un périphérique.
- Cache de blocs : tampons indexés par (périphérique, bloc), LRU, marqués
  sales, écrits par `sync` et périodiquement ; un propriétaire à la fois.
- Erreur d'écriture différée : gardée sur l'inode et rendue au `fsync` de
  chaque fichier ouvert (un `dup` partage le rapport), jamais effacée
  après un seul rapport (leçon de « fsyncgate », PostgreSQL 2018, et de
  l'`errseq_t` de Linux).
- Pile de périphériques bloc à la GEOM (FreeBSD) : partition, chiffrement
  ou miroir sont des périphériques bloc qui en enveloppent un autre, avec
  la même interface.
- Côté appli, remplacer un fichier se fait par `nom.tmp`, `fsync`,
  `rename`, puis `fsync` du dossier : le noyau garantit que `rename` est
  atomique.
- Vrai disque : aucune écriture avant tous les tests sur image.

## Tester

- Images fabriquées sur l'hôte (`image-disque --racine`, `mkfs.ext2 -d`),
  lues par le noyau et comparées au contenu attendu. Après une écriture du
  noyau : `debugfs` pour relire, `e2fsck -fn` pour vérifier, sur l'hôte.
- Parseurs cpio, ext2, MBR et GPT aussi sur l'hôte avec ASan, nourris
  d'images tronquées et corrompues.
- Cas : `/`, `//a/./b/../c`, nom de 255 octets, chemin trop long, fichier
  vide, gros fichier (indirect double), dossier de milliers d'entrées,
  `rename` dans le même dossier, lecture après la fin, `lseek` au-delà puis
  écriture (trou), tuyau plein puis vide, fermeture du dernier écrivain.

## Références

- Dave Poirier, « The Second Extended File System » : nongnu.org/ext2-doc
- POSIX.1-2024 (open, read, pipe, rename) ; `man 5 cpio` (format newc) ;
  spécification UEFI (GPT).
- xv6 : `fs.c`, `file.c`, `pipe.c` (couches nettes, licence MIT : lire,
  ne pas copier).
