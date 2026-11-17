# DESIGN.md

Contrat visuel pour les agents. Un projet avec une UI tient le sien à la racine.
S'il manque, celui-ci s'applique. Le fichier du projet prime sur les sections
qu'il remplit. AGENTS.md prime sur tout.

## Lecture

Avant d'écrire ou de relire une UI : ce fichier, puis le `DESIGN.md` du projet
s'il existe, puis les images de référence qu'il cite. Goût : skill
`frontend-design`. Accessibilité : `wcag` et `web-design-guidelines`. Pile :
`react-spa` ou `android-ui-engineering`.

## Rôles

L'écrivain unique écrit le code. Une revue liste les écarts, elle ne patch pas
le CSS. Celui qui fabrique une image ou une vidéo n'est pas celui qui la note.
Palette, police, variante retenue, musique : L'auteur tranche.

## Projet

À remplir dans le `DESIGN.md` du projet, pas ici. Ce fichier maison n'invente pas de marque.

- Nom, public, travail de l'écran
- Direction en une phrase, et ce qui est interdit
- Palette nommée : hex et rôle (fond, surface, texte, accent, succès, erreur)
- Polices et rôles : display, body, ui, mono
- Échelle de type, unité d'espacement, rayons
- Composants : quand les utiliser
- Voix des libellés : français, phrase, sans brochure
- Fiches (logo, icône, personnage) et chemins des fichiers de référence
- Verrouillé : ce qu'on ne change pas sans demander

Tant que ces champs sont vides, on s'arrête et on les fait remplir. On ne pose
pas une charte par habitude.

Défauts à ne pas poser tout seuls : fond crème `#F4F1EA` avec accent terracotta
`#D97757` ; fond presque noir avec un seul accent vert acide ou vermillon ; kit
de cartes SaaS identiques (même rayon, même ombre grise) ; Inter, Geist ou
`system-ui` pris par facilité ; un mot du titre en italique ou en couleur ;
eyebrow en capitales au-dessus de chaque titre.

## Cohérence

Une description texte ne tient pas une marque. La première image validée sert
de référence, avec sa fiche. Un logo se génère sans le nom écrit dedans : le
mot est posé en code. Les chemins des assets sont dans ce fichier.

## Revue

Oracle : capture de l'app qui tourne, comparée à ce contrat et aux maquettes.
Une lecture du CSS ne suffit pas. Contraste, focus clavier, `prefers-reduced-motion`,
états vides et erreur. Si le layout a bougé : un viewport large et un étroit.

## Hors pile

Pas de connecteur Higgsfield, pas d'agent designer, pas de skill nouveau, tant
que l'auteur ne le demande pas.
