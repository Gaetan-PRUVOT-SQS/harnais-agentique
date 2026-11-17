# Harnais local

Ce fichier prime sur le reste du skill. `~/.agents/AGENTS.md` prime sur ce fichier.

Les fichiers gérés par `rea setup` (`SKILL.md` et `references/`) restent ceux du paquet `rea-agents` 6.8.0. L'identité du skill est alignée (version 49). On ne les réécrit pas.

## Place

Dossier canonique : `~/.agents/skills/reverse-engineer-anything`. Grok lit `~/.agents/skills` directement.

Les skills de maintenance du dépôt REA (`rea-changelog-update`, `rea-ci-tests-audit`, `rea-tool-design`, `rea-analysis-optimization`) ne sont pas installés.

## Quand

Binaire livré, paquet, capture, ou comportement que le source du dépôt ne montre pas. Un dépôt source se lit avec les outils habituels, sans REA.

## MCP

REA 6.8.0 est installé (`rea` global, Node lts 24.22.2). Le serveur MCP `rea` est dans `~/.grok/config.toml`. La commande est ce binaire, avec l'argument `mcp`.

Ne pas relancer `rea setup`. Ne pas passer `--install-hopper`. Ne pas installer Hopper, IDA, Frida, JADX ni Kuna. Frida est une dépendance optionnelle du paquet : son script d'installation a été refusé, on ne l'autorise pas.

Cette session Grok ne voit les outils qu'après un redémarrage. `rea doctor` vérifie l'enregistrement. Il ne prouve pas que la session déjà ouverte est connectée.

Le fournisseur natif utilise Ghidra 12.1.4 (`GHIDRA_INSTALL_DIR`) et Temurin 25 (`JAVA_HOME`), seulement dans l'environnement du serveur. Le lien `~/.local/opt/ghidra/current` reste sur 12.2 pour le skill `ghidra`. Un `rea` lancé sans ces deux variables voit 12.2, et le doctor refuse cette version.

## Cible

La cible est un chemin ou un processus nommé dans la demande. Pas de choix d'appli à la place de l'auteur, pas de machine distante, pas de service partagé.

L'inspection statique d'un fichier local est le défaut. L'attache, l'instrumentation, le lancement ou la mutation d'un processus attend une demande qui le nomme.

## Pratiques

Pour une cible déjà nommée. On s'arrête dès que la question a sa réponse.

Identification d'abord, avant Ghidra ou une analyse REA qui ouvre le programme. On note dans le dossier de preuves la sortie de `file`, la taille, le SHA-256, et la version de chaque outil (`rea --version`, Ghidra 12.1.4 pour REA, Ghidra 12.2 pour le skill ghidra). L'original reste intact. Une copie de travail, s'il en faut une, reste dans ce dossier.

Chaque phrase du compte rendu porte l'un de ces trois mots : observation, inférence, inconnu. Une observation est un octet, un en-tête, une chaîne ou un condensat lu sur le fichier. Une inférence est le pseudo-code du décompilateur, un nom deviné, un comportement supposé. Un inconnu reste ouvert, avec ce qui manque pour le trancher. L'analyse statique ne montre pas une exécution. Une chaîne ou un nom de fichier ne suffit pas à dire ce que le programme fait.

Le plus petit outil d'abord : `file`, `readelf`, `objdump`, `strings`, puis un outil REA en résumé, puis seulement la page qui répond, ou Ghidra headless sur la fonction qui compte. On ne relance pas la même analyse sans une entrée qui a changé.

Un fait qui décide la conclusion se recoupe avec un second outil qui ne partage pas le même code. Condensat avec `sha256sum`. Build-id avec `readelf -n`. Type avec `file`. L'écart se note.

Lancer, attacher, instrumenter ou dépaqueter en exécutant attend une demande qui nomme la cible. Jamais sur l'hôte. Pas de résolution DNS, pas de visite d'URL, pas d'écriture d'un contournement. Reconstruire dans un dépôt attend une demande du tour.

Sources tenues courtes. NIST SP 800-86 : collecte, examen, analyse, rapport, condensat, copie de travail, et parfois aucune conclusion ne sort encore des données. La note du guide fait passer SHA-1 vers SHA-256. ISO/IEC 27037:2012 : identification et préservation. ISO/IEC 27042:2015 : analyse notée, rejouable. REA 6.8.0, `SKILL.md` : observation, inférence, inconnu, résumé d'abord, le statique ne prouve pas une exécution. `analyzeHeadless -import` importe le fichier. Le script du skill ghidra ne le lance pas.

## Écriture

Un seul écrivain. Pas de workers parallèles sur le projet, pas de worktree, pas de copie du dépôt, pas de `/tmp`.

Les preuves vont dans un dossier désigné dans la demande, ou dans `~/rea-evidence/<cible>/`, hors du dépôt. Dans un dépôt git, seulement un dossier choisi et ignoré par git.

Le skill explique. Il ne commit pas. Écrire une reconstruction dans un projet seulement si la demande du tour le demande.

## Délégation

Lecture du dépôt ou d'un rapport : un sous-agent en lecture, un seul niveau. Le parent garde les conclusions et les fichiers.
