---
name: pile-reseau
description: >-
  Réseau d'un OS maison : pilote de carte (e1000, virtio-net), Ethernet, ARP, IPv4, UDP, DHCP, TCP, sockets, pcap QEMU. Use when writing a NIC driver or network stack, or debugging packets.
---

# Pile réseau

Chaque couche ne connaît que ses voisines : la carte ne sait rien d'IP,
TCP ne sait rien de la carte. Tout paquet reçu est une entrée hostile. Et
VelumOS étant privé par défaut, rien ne part ni n'écoute sans accord.

Voisins : pilotes-materiel (DMA, anneaux), reseau-fond (adresses,
masques, routes), os-confidentialite (accord, rien à l'écoute),
noyau-securite, fichiers-unix (un socket est un descripteur),
processus-unix, gestion-memoire (pools de tampons).

## Ordre

1. Pilote de carte : e1000 (QEMU émule un 82540EM) ou virtio-net ;
   rtl8139 est plus simple mais ancien.
2. Ethernet et ARP.
3. IPv4 et ICMP echo : ping de la passerelle QEMU.
4. UDP, client DHCP, client DNS.
5. TCP.
6. Sockets : `socket`, `bind`, `connect`, `listen`, `accept`, `send`,
   `recv`, `close`, `poll`.
7. IPv6 plus tard.

## Pilote de carte

- Anneaux de descripteurs RX et TX en mémoire DMA (adresses physiques,
  alignement du manuel), tampons préalloués, index de tête et de queue, bit
  « descriptor done » ; scrutation d'abord, interruptions ensuite.
- Adresse MAC lue dans la carte ; promiscuité seulement en debug.
- Interface vers la pile : `envoyer(trame)` et un rappel `recevoir(trame)`.

## Règles des paquets

- Ordre réseau big-endian : `htons`, `ntohl` partout ; en-têtes packed
  avec `_Static_assert` (c-bas-niveau).
- Paquet reçu = entrée hostile : longueur minimale avant de lire un
  en-tête, longueurs déclarées au plus égales à la longueur reçue, IHL d'au
  moins 5, options bornées, offset TCP d'au moins 5, fragments refusés au
  début (ou réassemblage borné en mémoire et en temps), sommes de contrôle
  vérifiées.
- Somme de contrôle Internet (RFC 1071) : complément à un sur 16 bits,
  pseudo-en-tête pour UDP et TCP.
- Tampons de paquets avec marge devant pour ajouter les en-têtes sans
  copie ; pool préalloué et compté.

## ARP, IPv4, ICMP, UDP, DHCP, DNS

- ARP : cache avec expiration, requêtes en attente limitées, réponse
  seulement pour notre adresse.
- IPv4 d'hôte (pas de routage) : TTL, table avec passerelle par défaut ;
  ICMP echo ; port inaccessible pour un UDP sans socket.
- UDP : démultiplexage par port ; ports éphémères aléatoires.
- DHCP : DISCOVER, OFFER, REQUEST, ACK, bail et renouvellement ; lancé
  seulement quand l'utilisateur active le réseau.
- DNS : requête A, identifiant et port source aléatoires, réponse validée
  (même question), pointeurs de compression bornés (sinon boucle).

## TCP

- Machine à états de la RFC 9293 : LISTEN, SYN-SENT, SYN-RECEIVED,
  ESTABLISHED, FIN-WAIT-1 et 2, CLOSE-WAIT, CLOSING, LAST-ACK, TIME-WAIT.
- Séquence initiale imprévisible (RFC 6528), comparaisons modulo 2^32 par
  différence signée, fenêtre, MSS, retransmission avec RTO (RFC 6298) et
  recul exponentiel. Nagle, ACK différé et contrôle de congestion
  (RFC 5681) ensuite.
- Ressources bornées : file de SYN limitée, tampons plafonnés, TIME-WAIT
  limité ; RST accepté seulement dans la fenêtre (RFC 5961).
- File de SYN pleine : SYN cookies (RFC 4987 ; syncache et syncookies de
  FreeBSD, `net.ipv4.tcp_syncookies` de Linux), l'état de la connexion
  voyage dans la séquence initiale au lieu d'occuper la mémoire.

## Sockets

- Un socket est un fichier ouvert : `read`, `write` et `close` marchent ;
  bloquant par défaut, `EAGAIN` en non bloquant ; `poll` pour attendre
  plusieurs descripteurs, puis une file d'événements unique à la `kqueue`
  (unix-freebsd-linux). `SOCK_CLOEXEC` et `accept4` dès le départ.
- Boucle locale 127.0.0.1 sans carte : tests sans réseau.
- Rien n'écoute par défaut ; écouter ou émettre demande la permission
  réseau de l'appli (os-confidentialite).

## Tester

- Hôte : parseurs et constructeurs de paquets testés sur des trames
  capturées (fixtures pcap) et corrompues, sous ASan et en fuzz.
- QEMU : `-netdev user,id=n0 -device e1000,netdev=n0` (passerelle
  10.0.2.2, DNS 10.0.2.3, adresse donnée par DHCP 10.0.2.15) ;
  `hostfwd=tcp::5555-:80` dans `-netdev` pour joindre un serveur de l'OS
  depuis l'hôte (`nc localhost 5555`).
- Capture : `-object filter-dump,id=f0,netdev=n0,file=build/net/trafic.pcap`,
  puis `tcpdump -nr build/net/trafic.pcap`, sans root (vérifié le
  2026-09-29).
- Cas : ping, DHCP complet, résolution DNS, connexion TCP, transfert
  d'1 Mio avec pertes injectées par le pilote en debug (QEMU ne perd rien),
  fermeture des deux côtés, RST ; paquets tronqués, longueurs mensongères,
  options invalides.

## Références

- RFC 826 (ARP), 791 (IPv4), 792 (ICMP), 768 (UDP), 9293 (TCP), 6298,
  6528, 5961, 5681, 1071, 2131 (DHCP), 1035 (DNS).
- Intel « PCI/PCI-X Family of Gigabit Ethernet Controllers Software
  Developer's Manual » (8254x, e1000) ; spécification virtio (OASIS).
- lwIP (BSD-3-Clause) : à lire pour comprendre, pas à copier.
