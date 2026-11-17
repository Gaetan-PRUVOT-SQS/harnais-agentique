---
name: interface-rust
description: Choisir une interface Rust (gtk-rs, iced, egui, Slint, Tauri, Dioxus). Use when choosing or wiring a desktop, web, bureau or embedded frontend.
---

# Interface Rust

Le langage, l'édition, clippy, l'unsafe et les dépendances : skill rust. Ici, on choisit le toolkit et on le branche. Une appli déjà branchée reste sur son toolkit. On ne la migre pas sans demande.

Voisins : rust, norme-cybersecurite (entrées, fichiers, liens), wcag quand le brief vise un niveau.

## Décider

Un seul toolkit. On n'en ajoute pas un second pour un écran.

- Linux, look du système, ou projet déjà sur GTK : gtk-rs. libadwaita seulement si le brief veut le style GNOME. Relm4 seulement s'il est déjà là.
- L'UI existe déjà en HTML (React, Vite) et le bureau doit tourner sur plusieurs OS : Tauri. Le Rust sert aux commandes, aux fichiers et au système. L'écran reste la page.
- Outil interne, panneau, peu d'écrans : egui.
- Produit bureau écrit en Rust, écrans qui restent : iced, si le brief accepte le trou d'accessibilité ou si AccessKit y est vraiment branché (relecture avant de trancher).
- La même UI sur un ordinateur et sur l'écran d'un appareil : Slint. La licence se choisit avant d'ajouter la crate.
- Une UI en Rust pour le web, le bureau et le mobile : Dioxus. L'empaquetage bureau est un shell, le sien ou Tauri.
- Xilem, GPUI, Makepad, Floem, Perry : brief expérimental qui les nomme. Pas une livraison par défaut.

Dioxus dessine. Tauri affiche une page et expose des commandes. Les deux étages se combinent. On n'en prend pas un pour faire le travail de l'autre.

## gtk-rs

Widgets du système, lecteurs d'écran via AT-SPI, dialogues natifs. À l'aise sur Linux. Windows et macOS ne sont pas le même niveau de fini.

Un texte venu d'ailleurs passe par `set_text`. Pas de `set_markup`. Un lien sort d'une allowlist (tel, mailto déjà contrôlé, https du domaine prévu). On porte les libellés, les routes et les décisions d'un prototype web. On ne porte pas son CSS.

## Rendu Rust

iced, egui et Slint dessinent eux-mêmes. L'accessibilité vient d'un arbre sémantique, pas des pixels.

AccessKit est la couche partagée (Windows, macOS, AT-SPI, Android, iOS). Au 2026-09-06 : egui, Slint, xilem, GTK 4.18 l'avaient. iced et floem ne l'avaient pas. Le support GPUI n'était pas dans la version que Zed publie, et Zed le coupait. Avant un produit qui doit être lu par un lecteur d'écran, on relit l'état du toolkit. Un trou encore ouvert : on change de toolkit, ou le brief l'accepte par écrit.

## Slint

Trois licences au choix, dans `LICENSE.md` du dépôt. Pas MIT OR Apache-2.0 par défaut.

- Royalty-free 2.0 : bureau, mobile et web, propriétaire, gratuit, avec attribution (widget AboutSlint ou badge). L'embarqué est exclu.
- GPLv3 : logiciel libre, embarqué compris. Le binaire du produit est GPL. Les fichiers à nous peuvent garder un en-tête MIT ou Apache-2.0.
- Commercial : propriétaire, embarqué compris.

Embarqué : une machine qui fait une tâche dans un plus gros système (écran d'appareil, caisse, tableau de bord). Une appli parmi d'autres sur un PC ou un téléphone n'en est pas une. systeme-maison prime si le projet interdit le tiers.

## Tauri

L'UI est dans le WebView du système (WebKitGTK, WebView2, WKWebView). Chaque commande Rust est nommée dans une capability Tauri 2. Une commande absente n'est pas appelable. Le frontend ne construit pas un shell et ne reçoit pas `eval`. CSP, protocoles custom et fichiers restent dans l'appli. Un fichier choisi par l'utilisateur a un plafond lu avant le contenu.

## Brancher

- Le domaine n'importe pas le toolkit. La lib se teste sans ouvrir de fenêtre.
- Un seul fil UI. `Rc<RefCell<_>>` : skill rust. Un callback copie ce qu'il lui faut, lâche l'emprunt, puis rappelle le toolkit. Un appel qui peut rentrer (signal, dialogue, idle) ne garde pas le `Ref`.
- Fichier choisi : taille avant lecture, nom de base à l'écran, chemin jamais passé à un shell. `Command` et arguments séparés : skill rust.
- Liste : vignettes. Le fichier d'origine s'ouvre avec la fiche. On ne charge pas toute la galerie au premier écran.
- Un écran n'est pas fini si seule la vue-modèle est testée. Le domaine a ses tests. Une sonde sans bureau (xvfb pour GTK) lit les libellés qui décident. Le parcours qu'on n'a pas cliqué reste nommé.

## On s'arrête

- Migrer le toolkit en place, ou en poser un second à côté.
- Ajouter Slint sans avoir tranché bureau ou embarqué, libre ou propriétaire.
- `set_markup`, `eval`, ou une commande Tauri ouverte à toute la page.
- Dire l'écran accessible parce que le texte est à l'écran, sur un toolkit dont l'arbre n'est pas branché.

## Sources

- Slint, `LICENSE.md` et la licence royalty-free 2.0, dépôt slint-ui/slint, lus le 2026-10-20.
- AccessKit, état par toolkit : <https://goldstrikearch.github.io/rust-gui-desktop-ecosystem-state/>, 2026-09-06. À relire avant de trancher l'accessibilité.
- AccessKit, adaptateurs : <https://lib.rs/crates/accesskit> (0.25.1 au 2026-09-25).
