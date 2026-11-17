# Feature : passer sur du vrai matériel sans risque

Date : 2026-09-29

## Métier

- Besoin : VelumOS vise des PC anciens et récents, des portables, des cartes
  ARM et RISC-V. Tôt ou tard, il faut écrire une image sur une clé USB ou une
  carte SD et démarrer une vraie machine. C'est le geste le plus dangereux du
  projet : une lettre de travers dans `/dev/sdX` et c'est le disque du poste
  qui est effacé. Même risque avec le firmware (flashrom, variables EFI).
- Qui est concerné : L'auteur et l'agent, à chaque test sur vraie machine.
- Impact si on ne le fait pas : disque du poste ou disque de sauvegarde
  effacé, portable rendu inutilisable par une écriture de firmware, sans
  retour possible.

## Ce qu'on fait

- Comportement visible :
  - `ecrire-image IMAGE /dev/disk/by-id/usb-...` vérifie la cible et affiche
    ce qu'il écrirait, sans rien toucher. Avec `--ecrire`, il écrit, vide le
    cache du disque et relit la clé pour la comparer à l'image.
  - La garde des hooks demande confirmation pour toute écriture sur un
    disque (y compris via `/dev/disk/by-...`, `cp`, `tee`, redirection
    `>`, `grub2-install`, `limine`, `bmaptool`), pour `ecrire-image
    --ecrire`, et pour ce qui touche au firmware (`flashrom` en écriture,
    `fwupdmgr` qui installe, `efibootmgr` qui modifie, `mokutil` qui
    modifie).
- Fichiers touchés : `scripts/ecrire_image.py`, `scripts/test_ecrire_image.py`,
  `scripts/pyproject.toml`, lien `~/.local/bin/ecrire-image`,
  `~/.agents/hooks/garde.py`, `~/.agents/hooks/verify.py`.

## Choix techniques

| Choix | Pourquoi | Alternative rejetée | Impact métier |
|-------|----------|---------------------|---------------|
| Cible donnée par `/dev/disk/by-id/` seulement | le nom porte le modèle et le numéro de série et ne change pas au branchement suivant | accepter `/dev/sdb` | on sait quelle clé on vise, `/dev/sdb` peut devenir le disque de sauvegarde |
| Transport `usb`, ou carte SD (`/sys/block/mmcblkN/device/type` = `SD`) | seuls supports voulus pour un test ; l'eMMC interne d'un portable est aussi `mmcblk` mais de type `MMC` | se fier au bit `RM` | certaines clés rapides annoncent `RM=0`, et `RM` ne distingue pas SD et eMMC |
| Refus si une partition est montée, à n'importe quel niveau (LUKS, LVM) | le disque du système a toujours quelque chose de monté ; une clé montée par GNOME serait corrompue | liste fixe de disques interdits | protège le poste quel que soit son schéma de disques |
| Limite de taille à 256 Gio (`--taille-max` pour la lever) | au-delà, c'est plutôt un disque de sauvegarde USB | pas de limite | une erreur de clé ne coûte pas une sauvegarde |
| Simulation par défaut, `--ecrire` explicite | l'agent vérifie la cible sans risque, l'écriture reste un geste voulu | écrire directement | l'auteur voit la cible avant tout octet écrit |
| Cible relue juste avant `dd` | une clé débranchée puis remplacée change de nœud | résoudre une seule fois | pas d'écriture sur un disque arrivé entre-temps |
| `dd conv=fsync oflag=direct`, `blockdev --flushbufs`, puis `cmp -n` | la clé est vraiment écrite, et la relecture ne vient pas du cache | faire confiance au code retour de `dd` | une clé défaillante se voit tout de suite, pas devant la machine de test |
| `pkexec` si le nœud n'est pas inscriptible | sudo sans terminal ne marche pas depuis l'agent ; pkexec ouvre la fenêtre de mot de passe GNOME | mot de passe dans un script | aucun mot de passe écrit nulle part, un humain valide |
| Script shell constant, chemins en arguments positionnels | un chemin avec espace ou guillemet ne peut pas s'injecter dans la commande | construire une chaîne | pas d'injection de commande en root |
| Logique de décision pure (`refus_cible`, `refus_chemin`) testée avec pytest | le cas « vraie clé » ne se rejoue pas en test ; les décisions, si | tester en écrivant sur un loop device | tests rapides, sans root, sans disque |
| Garde : `ask` sur firmware et disques | ces écritures sont irréversibles hors du projet (AGENTS.md) | `deny` | l'auteur garde la main, l'agent ne bloque pas un geste voulu |

## Traçabilité

| Fichier | Fonction / bloc | Justifié par |
|---------|-----------------|--------------|
| `scripts/ecrire_image.py` | `refus_chemin` | cible par `/dev/disk/by-id/` |
| `scripts/ecrire_image.py` | `refus_cible`, `points_de_montage` | transport, montages, limite de taille |
| `scripts/ecrire_image.py` | `type_mmc` | carte SD contre eMMC |
| `scripts/ecrire_image.py` | `commande_ecriture` | dd, flushbufs, cmp ; pkexec ; arguments positionnels |
| `scripts/ecrire_image.py` | `ecrire` | cible relue juste avant `dd` |
| `scripts/ecrire_image.py` | `main`, `--ecrire` | simulation par défaut |
| `scripts/test_ecrire_image.py` | tous les tests | logique pure testée |
| `hooks/garde.py` | `DISQUE`, `REDIRECTION_DISQUE`, `OUTILS_DISQUE` | garde disques |
| `hooks/garde.py` | `touche_firmware` | garde firmware |
| `hooks/verify.py` | `test_garde_materiel` | garde disques et firmware |

## Notes

Un portable Samsung pouvait être rendu inutilisable en 2013 par des
écritures de variables EFI depuis Linux : d'où la garde sur `efibootmgr` et
`mokutil`, pas seulement sur flashrom.
