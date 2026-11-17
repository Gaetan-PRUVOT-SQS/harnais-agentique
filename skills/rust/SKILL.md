---
name: rust
description: >-
  Écrire, relire ou déboguer du Rust : édition 2024, clippy, erreurs, unsafe, dépendances. Use when writing, reviewing or debugging Rust (.rs, Cargo.toml, Cargo.lock).
---

# Rust

Le code suit pratiques-dev-senior, norme-cybersecurite, iso-29119 et tests-locaux. Ce skill ajoute ce que Rust change. Un dépôt déjà là garde son édition, ses lints et son style. On ne migre pas vers 2024 sans demande.

Voisins : systeme-maison (pas de crate tierce si le projet l'interdit), posix et abi-and-calling-conventions pour le FFI C, interface-rust pour le choix du toolkit.

## Édition et toolchain

- Crate neuve : `edition = "2024"`. `cargo new` le met déjà. Le défaut du poste est rustc 1.99 (mise). On ne fait pas `rustup default nightly`. Un nightly à côté ne sert qu'à Miri (`cargo +nightly miri`). Si le dépôt a `rust-toolchain.toml`, c'est elle qui commande pour ce dépôt.
- Sans clé `edition`, Cargo retombe sur 2015. On ne livre pas un manifeste sans édition.
- Édition 2024, ce qui casse du code qui compilait en 2021 :
  - une opération unsafe dans un `unsafe fn` veut son propre bloc `unsafe` (`unsafe_op_in_unsafe_fn`, warn par défaut). On la passe en deny.
  - `extern` et certains attributs (`no_mangle`, `export_name`, `link_section`) sont unsafe : `unsafe extern` et `#[unsafe(no_mangle)]`.
  - `std::env::set_var` et `remove_var` sont unsafe. Les appeler une fois des threads lancés est indéfini sur certaines plateformes. On ne s'en sert pas pour de la config après le démarrage.
  - un `impl Trait` en position de retour capture toutes les durées de vie en scope. `use<...>` retire celles qu'on ne veut pas.
  - les temporaires d'un `if let` et d'une expression de queue meurent plus tôt. Une référence qui tenait en 2021 peut pendre.
  - `gen` est un mot-clé.
- Depuis Rust 1.99, dans une crate 2024, `default-features = false` sur une dépendance héritée du workspace écrase la valeur du workspace. L'unification reste : un membre qui laisse les défauts les rallume pour tout le monde.
- Passage d'édition, seulement sur demande : `cargo update`, `cargo fix --edition`, puis la clé `edition`, puis `cargo test`. On relit le diff. `cargo fix` ne prouve pas que le contrat unsafe tient.

## Forme

- `cargo fmt` avec les options stables de rustfmt. Pas d'option nightly dans `rustfmt.toml` si le dépôt n'en a pas déjà.
- Avant de dire le travail fini : `cargo test` et `cargo clippy --all-targets --all-features` avec `CARGO_BUILD_WARNINGS=deny` (Cargo 1.97 et après). `--no-deps` sur une crate du workspace quand les dépendances ne sont pas à nous.
- `clippy::all` est le jeu par défaut. On n'active pas `pedantic` ni `restriction` en bloc. `restriction` se prend lint par lint.
- `#[allow]` est local, avec la raison en une ligne, quand un lint a tort sur ce code. Pas de `allow` de crate pour faire taire un vrai défaut.
- Identifiants en anglais, comme la bibliothèque standard. Textes vus par l'utilisateur dans la langue du projet.

## Erreurs

- Une bibliothèque expose un type d'erreur qui implémente `std::error::Error`, `Display` et `Debug`, avec `source` quand il y a une cause. `thiserror` convient. `anyhow` reste dans le binaire, pas dans la signature publique.
- `?` propage. L'exemple de doc publique utilise `?`.
- `unwrap` et `expect` sur une entrée (utilisateur, fichier, réseau, parse, index venu d'ailleurs) sont un défaut. `expect` ne reste que pour un invariant cassé, et le message dit lequel.
- Un index externe passe par `get`. L'indexation `[]` panique.
- `panic` et `unwrap` dans un test, oui. Dans `Drop`, non.
- La doc publique d'une fonction dit ce qui renvoie `Err`, ce qui panique, et le contrat unsafe. Le reste des commentaires suit AGENTS.md. Les choix de conception vont dans `docs/justifications/`.

## Entiers

En dev, un dépassement panique. En release, il wrappe en silence. Le profil ne fixe pas le comportement.

Dès qu'un dépassement est possible (taille, index, protocole, argent, compteur), l'opération est explicite : `checked_*` (`None` si ça déborde), `saturating_*`, `wrapping_*`, ou `Wrapping` / `Saturating`.

Un `as` qui tronque une valeur non fiable est un bug tant qu'il n'est pas testé. On convertit par `TryFrom` quand l'échec doit se voir.

On ne met pas `overflow-checks = false`. `panic = "abort"` seulement si le projet l'a déjà choisi et que c'est écrit.

## API

Pour une crate publiée ou réutilisée. Une appli fermée n'a pas besoin de rustdoc sur chaque type privé.

- Casse de la RFC 430 : `snake_case` pour fonctions et modules, `CamelCase` pour types et traits, `SCREAMING_SNAKE_CASE` pour les constantes.
- `as_` emprunte pas cher, `to_` peut coûter, `into_` consomme. Un getter a le nom du champ, sans préfixe `get_`.
- On prend ce qu'on stocke. `&str`, `impl AsRef<Path>`, `impl Read` par valeur. On ne demande pas `String` pour ne faire que lire.
- Champs d'une struct stable : privés, constructeur, accesseurs. Un enum public qui va grandir est `#[non_exhaustive]`.
- Newtype plutôt qu'un `String` ou un `bool` qui veut dire trois choses.
- `Deref` seulement pour un pointeur intelligent.
- `Debug` sur tout type public. `Copy` seulement si la copie est un memcpy bon marché et que le type n'a pas d'identité.
- `Send` et `Sync` quand le type peut l'être. `NonNull<T>` et les pointeurs nus sont `!Send` et `!Sync` (rustc 1.99) : un tampon qui les possède a un `unsafe impl` borné par `T: Send` et `T: Sync`, avec le contrat dans `// SAFETY:`. `PhantomData<T>` règle le dropck, il ne rend pas un `NonNull` `Send`.
- Traits courants dérivés quand ils ont un sens : `Clone`, `PartialEq`, `Eq`, `Hash`. Pas de borne de trait sur la struct si seul un impl en a besoin.
- `#[must_use]` sur un builder et sur un type dont ignorer la valeur est un bug.
- Dépendance publique d'une crate `>= 1.0` : elle-même en `>= 1.0`. Licence par défaut de l'écosystème : `MIT OR Apache-2.0`, sauf choix du projet. systeme-maison prime si le système maison interdit le tiers.

## Unsafe

Pas de comportement indéfini. Le code safe ne peut pas en créer si le unsafe autour est correct.

- Crate sans FFI, sans registre matériel et sans trou de perf mesuré : `#![forbid(unsafe_code)]` à la racine.
- Sinon le unsafe est petit, dans un module qui rend une API safe, ou une fonction `unsafe` dont les préconditions sont toutes écrites. Un appelant safe ne doit pas pouvoir casser l'invariant.
- Chaque bloc a un commentaire `// SAFETY:` qui dit l'invariant tenu. `undocumented_unsafe_blocks` est en deny dès qu'il y a du unsafe. C'est l'exception à la règle des commentaires. Le texte peut être en français, le mot `SAFETY` reste.
- `mem::forget`, `Box::leak` et `ManuallyDrop` ne servent pas à esquiver un `Drop`. `from_raw` ne reprend que ce que `into_raw` a donné, une fois.

Aliasing, assez pour coder. Stacked Borrows est le contrôle Miri par défaut. Tree Borrows se lance avec `-Zmiri-tree-borrows`. On ne désactive ni l'un ni l'autre (`-Zmiri-disable-stacked-borrows` rate les alias). Les deux modèles bougent : on s'en tient à ce qu'ils refusent tous les deux.

- Une référence safe (`&T`, `&mut T`) vise de la mémoire initialisée du bon type. On n'en crée pas vers un trou. Tant que ce n'est pas écrit, c'est un pointeur nu ou un `MaybeUninit`.
- Créer un `&mut T` réserve l'accès unique pour toute sa durée. Aucun autre pointeur ne lit ni n'écrit cette zone pendant ce temps. On ne garde pas une copie du pointeur pour s'en servir pendant que le `&mut` vit.
- Créer un `&T` interdit d'écrire par un autre alias pendant que ce partage vit, sauf mutabilité intérieure (`UnsafeCell`).
- Un pointeur reste dans l'allocation qui l'a produit (`alloc`, `Box`, un slice). On ne le déréférence pas hors bornes, ni après `dealloc`. L'adresse juste après le bloc ne se déréférence pas. On ne mélange pas deux allocations.
- `ptr::read` emporte la valeur : l'appelant la possède, le créneau ne sera plus `Drop`. `ptr::write` écrit sans détruire l'ancien contenu (le créneau était vide, ou on a déjà décidé de fuir l'ancienne valeur). `copy` et `copy_nonoverlapping` déplacent des octets sans `Drop`. `drop_in_place` détruit. On choisit selon qui possède la valeur.
- `assume_init` seulement quand chaque octet exigé par le type est écrit. Dans un tampon, seul le préfixe `len` l'est.
- Un pointeur fabriqué depuis un entier n'a pas de provenance. On ne l'invente pas. `with_addr` garde la provenance du pointeur d'origine.
- `dealloc` reprend le même layout que `alloc`. On ne lui passe pas une référence.
- ZST : `NonNull::dangling()` aligné suffit. On n'alloue pas une taille nulle, on `Drop` quand même les éléments logiques.

Preuve relançable : `~/.agents/skills/rust/preuve` (`rawbuf`). `cargo test`, clippy en erreurs, puis `cargo +nightly miri test`, puis `MIRIFLAGS="-Zmiri-tree-borrows" cargo +nightly miri test`. Si le nightly ou Miri manque, on le dit, on n'annonce pas un vert.

Cas qui dépasse cette liste : le Rustonomicon et les Unsafe Code Guidelines. On ne complète pas l'aliasing de mémoire.

## FFI

- Types C seulement à la frontière. Alias `c_int`, `c_char`, selon le cas. Pas d'enum Rust, pas de type qui implémente `Drop`, pas de référence Rust vers une donnée dont C garde un pointeur mutable.
- Pointeur entrant vérifié (non nul, aligné, vivant le temps de l'appel) avant d'en faire une référence.
- Pointeur de fonction : `extern "C"` et `unsafe`, et on teste qu'il n'est pas nul.
- Un panic ne traverse pas vers C : `catch_unwind` dans le wrapper, code d'erreur côté C.
- Qui alloue libère. C'est écrit à côté de la fonction.
- `bindgen` ou `cbindgen` pour un gros en-tête. On relit le bord.

## Fils et async

- On ne garde pas un `MutexGuard` de `std` à travers un `.await`. Le verrou est lâché avant. `tokio::sync::Mutex` seulement si le garde doit vraiment traverser le await.
- Pas de bloquant sur le runtime (fichier, sommeil, gros calcul). `spawn_blocking` ou un thread dédié.
- Un mutex empoisonné : on propage, ou `into_inner` si l'invariant tient encore.
- `Rc<RefCell<_>>` pour un graphe ou un intérieur partagé sur un seul fil. `clone` pour faire taire l'emprunteur est un défaut de découpage.

## Dépendances

- Le moins possible. Pas de version `*`. Pas de dépôt git ni de `[patch]` sans une raison écrite.
- Avant d'ajouter une crate : elle est maintenue, la licence colle au projet, et on a regardé le unsafe du bord qu'on appelle.
- `Cargo.lock` est versionné. On ne plaque pas un plafond de version dans `Cargo.toml` pour figer l'arbre. Un `cargo update` sur une branche ou en CI voit les dernières versions compatibles.
- Avant livraison, s'il y a des dépendances : `cargo audit` (base RustSec). L'outil manque : `cargo install cargo-audit --locked`, puis on relance. Une alerte connue est un incident. `cargo deny` si le dépôt l'a déjà, ou si les licences et les crates bannies comptent.
- Feature : le minimum. Une feature qui change un type public se comporte mal avec l'unification Cargo.

## Tests

Dans le dépôt, sortie dans `target/`. `cargo test`, puis clippy comme plus haut, puis `cargo fmt --check`.

- Tests unitaires à côté du code, `tests/` pour l'API publique, doctests sur les exemples publics d'une bibliothèque.
- Les noms portent le cas (limite, erreur, overflow, entrée vide). Techniques : iso-29119. Un parseur ou de l'arithmétique à risque gagne des valeurs limites. `proptest` seulement si l'espace d'entrée est le risque.
- Unsafe : un cas qui tient l'invariant, et un cas qui refuse l'entrée illégale au bord safe.

## On s'arrête

- `unsafe` ou micro-optimisation sans mesure (`cargo bench` du projet, ou un test de perf déjà là).
- `unwrap` sur un chemin qui peut échouer en prod.
- Shell construit par une chaîne. Un processus externe passe par `std::process::Command` et des arguments séparés.
- Secret dans le code ou dans `Cargo.toml`.
- Copie du projet ou essai hors du dépôt.

## Références

- API guidelines : <https://rust-lang.github.io/api-guidelines/checklist.html> (équipe libs, recommandations).
- Édition 2024 : <https://doc.rust-lang.org/edition-guide/rust-2024/> (stable en 1.85). `cargo new` : édition par défaut 2024.
- Clippy : <https://doc.rust-lang.org/clippy/usage.html>. `CARGO_BUILD_WARNINGS=deny`.
- Cargo.lock : <https://blog.rust-lang.org/2023/08/29/committing-lockfiles/> et <https://doc.rust-lang.org/cargo/guide/cargo-toml-vs-cargo-lock.html>.
- ANSSI, Secure Rust Guidelines : <https://anssi-fr.github.io/rust-guide/> (le guide se dit unstable). Règles citées : LANG-ARITH, LANG-UNSAFE, LANG-UNSAFE-ENCP, LANG-DROP-NO-PANIC, DENV-CARGO-LOCK, DENV-AUTOFIX, LIBS-AUDIT.
- Unsafe : <https://doc.rust-lang.org/nomicon/> (dont Send et Sync), <https://rust-lang.github.io/unsafe-code-guidelines/>. Miri : <https://github.com/rust-lang/miri> (Stacked Borrows par défaut, Tree Borrows en `-Zmiri-tree-borrows`).
- Advisories : <https://rustsec.org/>, `cargo audit`.
