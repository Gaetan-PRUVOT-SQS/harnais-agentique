---
name: linux-serveur
description: >-
  Administration d'un serveur Linux : nginx, systemd, pare-feu, SELinux, SSH, logs, DNS. Use when a service won't start, a port is unreachable, nginx returns 502/504 or a VPS is hardened.
---

# Serveur Linux

Diagnostiquer de bas en haut, une couche à la fois, avec une commande
qui prouve chaque étape.

## Diagnostic d'un service injoignable

1. Le processus tourne ? `systemctl status <svc>`, `journalctl -u <svc> -n 50`
2. Il écoute ? `ss -tlnp | grep <port>` : `127.0.0.1` n'est pas joignable
   de l'extérieur, `0.0.0.0` ou `::` l'est.
3. Il répond en local ? `curl -v http://127.0.0.1:<port>/`
4. Le pare-feu laisse passer ? `sudo ufw status verbose`
5. Le nom pointe au bon endroit ? `dig +short <domaine>` ou `getent hosts`
6. De l'extérieur : `curl -v https://<domaine>/`

S'arrêter à la première étape qui échoue.

## systemd

- Unité perso dans `/etc/systemd/system/<app>.service` avec `User=` non root,
  `WorkingDirectory=`, `EnvironmentFile=` pour les secrets,
  `Restart=on-failure`.
- Après modification : `sudo systemctl daemon-reload`, puis `restart`.
- `systemctl enable --now` seulement si le service doit survivre au reboot.
- Bac à sable par unité : `NoNewPrivileges=yes`, `ProtectSystem=strict`
  avec `ReadWritePaths=` pour le seul dossier de données, `ProtectHome=yes`,
  `PrivateTmp=yes`, `PrivateDevices=yes`, `CapabilityBoundingSet=` vide,
  `RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX`,
  `SystemCallFilter=@system-service`, `MemoryDenyWriteExecute=yes` (sauf
  JIT : Node, Java). Chaque directive se teste service lancé.
- Mesure : `systemd-analyze security <app>.service` donne une note
  d'exposition et la liste de ce qui reste ouvert ; on la note avant et
  après.
- Surcharge d'une unité livrée : `systemctl edit <svc>` (drop-in dans
  `/etc/systemd/system/<svc>.service.d/`), jamais une modification du
  fichier de `/usr/lib/systemd/system`, écrasé à la mise à jour.

## nginx

- Tester avant de recharger : `sudo nginx -t && sudo systemctl reload nginx`.
- 502 : le backend ne répond pas (étapes 1 à 3 sur le backend).
  504 : il répond trop lentement. 403 : droits sur les fichiers ou `root`.
- Reverse proxy : `proxy_pass http://127.0.0.1:<port>;` avec
  `proxy_set_header Host $host;` et `X-Forwarded-For`, `X-Forwarded-Proto`.
- Logs : `/var/log/nginx/error.log` d'abord.
- TLS : certbot, redirection 80 vers 443, `server_tokens off;`.

## Durcissement de base

- SSH par clé, `PermitRootLogin no`, `PasswordAuthentication no`, garder
  une session ouverte pendant le test de la nouvelle config.
- `ufw default deny incoming`, n'ouvrir que 22, 80, 443 et ce que le brief
  demande. Autoriser SSH avant `ufw enable`.
- Fedora et RHEL : firewalld plutôt qu'ufw (`firewall-cmd --permanent
  --add-service=https`, puis `--reload`) ; SELinux reste en enforcing.
  Un refus se lit (`sudo ausearch -m avc -ts recent`) et se corrige par le
  bon contexte (`restorecon -Rv <dossier>`, `semanage port -a -t
  http_port_t -p tcp 8080`, `setsebool -P`), jamais par
  `setenforce 0`.
- Fedora Workstation : la zone par défaut `FedoraWorkstation` laisse
  entrer TCP et UDP de 1025 à 65535. Un serveur de dev qui écoute sur
  `0.0.0.0` est donc joignable depuis le réseau local : écouter sur
  `127.0.0.1`, ou passer l'interface dans une zone plus fermée.
- Bases de données sur `127.0.0.1`, jamais exposées.
- Mises à jour de sécurité : `unattended-upgrades` sur Debian ou Ubuntu ;
  `dnf5-plugin-automatic` et `dnf-automatic.timer` sur Fedora.
- FreeBSD : `pf` pour le pare-feu, services déclarés dans `/etc/rc.conf`
  (`sysrc nom_enable=YES`), mises à jour par `freebsd-update` et `pkg
  upgrade`, alertes de sécurité par `pkg audit -F` ; un service exposé
  tourne dans une jail.

## Garde-fous

- sudo selon AGENTS.md : pas de mot de passe écrit dans un fichier.
- Avant d'éditer un fichier de `/etc`, copie `.bak` datée.
- Ne pas couper SSH, le pare-feu ou le réseau d'une machine distante sans
  accès de secours.
