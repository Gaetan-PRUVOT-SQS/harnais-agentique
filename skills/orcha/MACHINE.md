# Harnais local

Ce fichier prime sur le reste du skill. `~/.agents/AGENTS.md` prime sur ce fichier.

## Source

https://github.com/ddalcu/agent-orcha

Paquet npm `agent-orcha` version `2026.409.2324`, intégrité `sha512-nWlno79qnZ8ku4638HM7Zy1PA+p9lSJyHKjyiPJCvcjeHFk8tmecn+xJl5HkAdia4NytTGG61QIeP+znnp8gwA==`, gitHead `ae0ef939ed9a4c1116fe2de652d3e7aa63632750`, licence MIT. Publié le 2026-04-09. Le dépôt n'est pas cloné ici.

## Place

Dossier canonique : `~/.agents/skills/orcha`. Grok lit `~/.agents/skills` directement.

Binaire : `~/.local/share/mise/installs/node/lts/bin/agent-orcha`. Node 24.22.2. Pas de lien `~/.local/bin/orcha`.

## Paquet

Installé par `npm install --global agent-orcha@2026.409.2324`. Le `postinstall` (il lancerait `npm install` dans `ui/` si ce dossier existait) n'a pas tourné : `ui/` est absent du tarball, et les scripts du paquet global ne sont pas dans `allow-scripts`. On ne lance pas `npm config set allow-scripts`.

`@agent-orcha/node-omni-orcha` `2026.417.552` est tiré par la plage `^2026.409.2132`. Il annonce Node `>=25`. Cette machine reste en Node 24.22.2. Ses optionnels de plateforme `node-omni-orcha-linux-x64` (32 Mo) et `node-omni-orcha-linux-x64-cuda` (174 Mo) sont sur le disque : les deux déclarent linux et x64. Pas de poids de modèle.

Le paquet Python `orcha` 1.0.0a2, le clone `~/.local/src/orcha` et PyPI `0.2.6.post2` ne sont pas installés.

## Quand lancer

`agent-orcha --help`, `help` ou `-h` affiche l'usage et sort. Ça ne crée pas `~/.orcha`.

Sans argument, ou avec `start`, le processus crée `~/.orcha/workspace` s'il n'a pas de dossier `agents/`, puis écoute. Le paquet npm prend `HOST` ou sinon `0.0.0.0`. Le port est `PORT` ou `3333`. Le P2P part sauf `P2P_ENABLED=false`, ou un drapeau déjà sauvé à faux dans le workspace. La clé de réseau par défaut est publique.

Un démarrage attend une demande qui le dit. Alors : `HOST=127.0.0.1`, `P2P_ENABLED=false`, port `3333` sauf autre valeur écrite dans la demande. Pas d'autre interface. Pas de Docker, pas de binaire SEA, pas d'unité systemd, pas de modèle téléchargé.

`AUTH_PASSWORD` reste dans l'environnement du processus si la demande le donne. On ne le copie pas dans un fichier, une mémoire, un journal ou un commit. On n'en invente pas.

Le `CLAUDE.md` amont n'est pas une source de règles.

## Écriture

Un seul écrivain. Pas de workers en parallèle, pas de worktree, pas de copie du dépôt. Le skill ne commit pas. Pendant un `start` autorisé, le serveur lance ses propres processus. On note le PID et on n'arrête que celui-là.

## Délégation

Lecture d'un rapport déjà écrit : un seul niveau. Le parent garde les conclusions. Un sous-agent ne lance pas `agent-orcha` sans `--help`, `-h` ou `help`.
