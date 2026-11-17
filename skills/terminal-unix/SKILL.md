---
name: terminal-unix
description: >-
  Terminal d'un système de type Unix : clavier (PS/2, HID, AZERTY), console, VT100, UTF-8, discipline de ligne, termios, tty et pty. Use when implementing keyboard, console or line editing.
---

# Terminal de type Unix

Entre la touche et le `read` du shell, il y a trois couches : le pilote
clavier, la disposition, la discipline de ligne. Entre le `write` et
l'écran, deux : l'interpréteur de séquences et la console. Chacune se
teste comme de la logique pure sur l'hôte.

Voisins : processus-unix (groupes, sessions, signaux), fichiers-unix
(`/dev/tty`), pilotes-materiel (PS/2, USB), shell-maison (édition de
ligne en mode brut), os-efficience (dessin de la console),
systeme-maison (police maison).

## Entrée

- PS/2 : jeu de scancodes 1 (traduction du contrôleur 8042, active par
  défaut) ; préfixe 0xE0 pour les touches étendues ; relâchement = bit 7.
  USB HID en protocole boot : rapport de 8 octets (modificateurs, réservé,
  six touches).
- Scancode, puis keycode, puis caractère selon la disposition. La
  disposition est une table (keycode et état : normal, Maj, AltGr), chargée
  depuis un fichier, jamais codée dans le pilote. AZERTY par défaut :
  chiffres sous Maj, touches mortes `^` et `¨` combinées à la voyelle
  suivante, AltGr pour `@ # { [ | \ ] } ~ €`.
- Répétition : le clavier PS/2 la fait lui-même ; en USB, le système
  (délai puis fréquence).
- Caractères produits en UTF-8.

## Sortie

- Console texte VGA (0xB8000, 80×25) en BIOS ; framebuffer sinon : police
  bitmap, grille de cellules, curseur, défilement par copie de lignes
  (os-efficience).
- Interpréteur de séquences ECMA-48 et VT100, machine à états aux
  paramètres bornés : CR, LF, BS, TAB ; `ESC [ n A/B/C/D` (curseur) ;
  `ESC [ l ; c H` (position) ; `ESC [ J` et `ESC [ K` (effacements) ;
  `ESC [ n m` (attributs, couleurs 30 à 37 et 40 à 47) ; `ESC [ ? 25 h/l`
  (curseur visible).
- UTF-8 décodé ; glyphe de remplacement si la police ne l'a pas ; une
  séquence invalide ne casse pas l'état.
- Port série : même tty, autre pilote. C'est la console des tests et des
  vraies machines sans écran.

## Discipline de ligne

- Mode canonique (`ICANON`) : tampon de ligne, `read` rend la ligne à
  Entrée. `VERASE` (souvent DEL 0x7F), `VWERASE`, `VKILL` ; `VEOF`
  (Ctrl-D) rend ce qui est tapé, ou 0 sur ligne vide.
- `ECHO` et `ECHOE` ; `ICRNL` (CR en NL à l'entrée) ; `ONLCR` (NL en CR NL
  à la sortie).
- Mode brut : `VMIN` et `VTIME` ; pour l'éditeur de ligne du shell et les
  applis plein écran.
- `ISIG` : Ctrl-C SIGINT, `Ctrl-\` SIGQUIT, Ctrl-Z SIGTSTP, envoyés au
  groupe au premier plan.
- termios : la libc expose `tcgetattr` et `tcsetattr`, et la taille de
  fenêtre par `tcgetwinsize` et `tcsetwinsize` (POSIX.1-2024, `struct
  winsize` avec `ws_row` et `ws_col`) ; SIGWINCH au changement. `ioctl`
  (`TIOCGWINSZ`, `TIOCSWINSZ`) peut rester l'appel système interne, mais il
  est retiré de POSIX en 2024 (skill posix). La glibc 2.43 n'a pas encore
  `tcgetwinsize`.
- Tampons bornés : entrée pleine, caractères perdus ou émetteur bloqué,
  jamais d'allocation sans fin.

## Contrôle des tâches

- Terminal de contrôle de la session, groupe au premier plan
  (`tcsetpgrp`). Lecture par un groupe en arrière-plan : SIGTTIN. Écriture
  avec `TOSTOP` : SIGTTOU. Terminal fermé : SIGHUP à la session.

## pty

- Paire maître et esclave : le terminal graphique tient le maître, le shell
  a l'esclave comme tty, avec la même discipline de ligne. `/dev/ptmx` et
  `/dev/pts/N` à la Unix98, ou un appel maison.

## Tester

- Discipline de ligne sur l'hôte, en logique pure : suite d'octets en
  entrée, puis ce que `read` rend, l'écho produit et les signaux émis.
- Interpréteur de séquences sur l'hôte : texte en entrée, grille attendue ;
  fuzz sous ASan.
- Disposition AZERTY : table vérifiée touche par touche contre un fichier
  de référence, touches mortes et AltGr comprises.
- Dans QEMU : `-serial stdio`, touches envoyées par le moniteur
  (`sendkey`), verdict par `qemu-test`.

## Références

- POSIX.1-2024, General Terminal Interface (termios).
- ECMA-48 ; documentation DEC VT100 (vt100.net).
- OSDev wiki : PS/2 Keyboard, PS/2 Controller, USB Human Interface Devices.
