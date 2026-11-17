---
name: os-confidentialite
description: >-
  Confidentialité dès la conception de VelumOS : permissions d'appli, isolation, pages à zéro, W^X, zéro télémétrie. Use when writing a syscall, the loader, IPC, files, network or logs.
---

# OS privé par défaut

Pendant d'os-efficience : la vitesse ne doit jamais s'acheter en ouvrant
une fuite. Durcissement du noyau lui-même (canari, UBSan, SMEP/SMAP,
spéculation, copies user) : noyau-securite. Le skill norme-cybersecurite reste valable pour le code hôte ;
ici on parle du noyau et des applis de notre OS. Chaque règle doit avoir
un test qui la prouve (liste dans `docs/charte.md` du projet).

## Principes

- Moindre privilège : une appli n'a que ce qu'elle déclare (masque de
  permissions dans son en-tête, 0 = rien), le noyau refuse le reste. Idée
  proche de `pledge`/`unveil` d'OpenBSD et des capacités de seL4 ou
  Fuchsia : le droit est donné explicitement, jamais supposé.
- Capacités sur descripteurs, idée de Capsicum (FreeBSD) : une appli en
  bac à sable n'a plus accès aux noms globaux (chemins absolus, pid) et
  chaque descripteur porte des droits qui ne font que diminuer. Un fichier
  choisi par l'utilisateur arrive comme descripteur ouvert par le système.
  Côté Linux, mêmes buts avec `no_new_privs`, seccomp et Landlock
  (unix-freebsd-linux).
- Accord de l'utilisateur pour le sensible : réseau, écriture de fichiers,
  capture d'écran, périphériques bruts.
- Rien ne sort sans raison : pas de réseau au démarrage, pas de
  télémétrie, pas de donnée utilisateur dans les journaux série.
- Aucun pistage en arrière-plan : pas d'identifiant unique (ni machine,
  ni utilisateur), pas de rapport de plantage envoyé, pas de vérification
  de mise à jour automatique, aucun service réseau à l'écoute par défaut.
- OS libre : sources publiques, build reproductible (versions épinglées),
  image de base sans firmware propriétaire ; les firmwares tiers (Wi-Fi,
  GPU) restent séparés et installés seulement sur choix de l'utilisateur.

## Règles noyau

- Isolation : un espace d'adressage par appli, page 0 jamais mappée,
  noyau inaccessible en ring 3 (bit U/S des pages). Pas d'appli en ring 0.
- Appels système : vérifier le numéro, les permissions, et **chaque
  pointeur** reçu (dans l'espace user, taille sans débordement
  `addr + len`, page présente) avant de lire ou d'écrire. Copier les
  données dans le noyau avant de les vérifier, pour éviter qu'une autre
  tâche les change entre la vérification et l'usage.
- Retourner une erreur, jamais faire planter le noyau sur une entrée
  d'appli. Pas d'adresse noyau dans les valeurs rendues (ni dans les
  messages d'erreur).
- Mémoire : toute page donnée à une appli arrive à zéro (sinon fuite de
  données d'une autre appli). Effacer les tampons sensibles après usage
  (mot de passe, clé) avec une écriture que le compilateur ne supprime
  pas (`volatile` ou barrière).
- Entrées : clavier et souris seulement à la fenêtre active ; une appli
  ne lit ni l'écran ni les fenêtres des autres sans la permission capture.
- W^X : code en lecture/exécution, données sans exécution. En i686, le
  bit NX demande le paging PAE ; en attendant, au moins code en lecture
  seule. SMEP/SMAP si le CPU les a (CPUID), pour que le noyau n'exécute
  ni ne lise la mémoire user par accident.
- Intégrité : vérifier l'en-tête et la somme d'une appli avant de la
  charger ; plus tard, signature.
- DMA : sans IOMMU (VT-d, AMD-Vi, SMMU), un périphérique qui fait du DMA
  lit et écrit toute la RAM. Bus master activé seulement pour les
  périphériques pilotés ; plus tard, IOMMU pour confiner chacun à ses
  tampons, d'abord les ports externes (Thunderbolt, USB4, ExpressCard).
- Tables du firmware (ACPI, DTB) et descripteurs USB : entrées non
  fiables, bornes et sommes vérifiées avant usage (pilotes-materiel).
- Aléa : RDRAND/RDSEED si présents (CPUID), mélangés à un pool, pour les
  futures clés et l'ASLR ; jamais un compteur ou l'heure seule.

## Tests à écrire avec chaque fonctionnalité

- Appel système sans la permission : refusé.
- Pointeur nul, pointeur noyau, `addr + len` qui déborde : erreur propre.
- Page fraîchement allouée : que des zéros.
- Appli qui lit la mémoire d'une autre ou la page 0 : faute, noyau vivant.
- Appli en arrière-plan : ne reçoit aucune touche.
- Exécution d'une page de données (dès que NX existe) : faute.

## Journaux et debug

- `kprintf` série utile au développement, mais aucune donnée utilisateur
  (texte tapé, contenu de fichier) ; build de livraison avec les traces
  bavardes coupées.
- Le port série et gdb sont des outils de dev : pas d'accès à distance au
  débogueur dans une image livrée.
