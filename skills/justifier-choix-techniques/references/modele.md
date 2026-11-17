# Feature : <nom court>

Date : YYYY-MM-DD

## Métier

- Besoin :
- Qui est concerné :
- Impact si on ne le fait pas :

## Ce qu'on fait

- Comportement visible :
- Fichiers touchés :

## Choix techniques

| Choix | Pourquoi | Alternative rejetée | Impact métier |
|-------|----------|---------------------|---------------|
| | | | |

## Traçabilité

| Fichier | Fonction / bloc | Justifié par (section ou choix) |
|---------|-----------------|----------------------------------|
| | | |

## Tests

Copier `~/.agents/skills/iso-29119/modeles/section-tests.md` (risques,
conception, critères de fin, résultat), à la taille du risque.

## Notes

(optionnel, une ou deux phrases, pas un roman)

---

# Exemple rempli (Collapse)

Date : 2026-08-20

## Métier

- Besoin : afficher ou cacher la description d'un logement sans quitter la page
- Qui est concerné : visiteur qui lit une fiche logement
- Impact si on ne le fait pas : texte trop long, page illisible, brief non respecté

## Ce qu'on fait

- Comportement visible : panneau fermé au départ ; clic sur le titre ouvre/ferme ; la flèche tourne
- Fichiers touchés : `src/components/Collapse.jsx`, `src/components/Collapse.css`

## Choix techniques

| Choix | Pourquoi | Alternative rejetée | Impact métier |
|-------|----------|---------------------|---------------|
| `button` dans le header | clavier + clic, élément cliquable clair | `div` cliquable | le visiteur peut ouvrir au clavier |
| fermé par défaut (`false`) | la page reste courte au chargement | ouvert par défaut | on voit d'abord titre + infos clés |
| animation `grid-template-rows` 0fr → 1fr | hauteur suit le texte, pas de coupure | `max-height: 0` / `999px` | ouverture fluide, texte toujours entier |
| flèche SVG qui tourne | l'état ouvert/fermé se voit sans lire | changer le texte « ouvrir/fermer » | le visiteur comprend d'un coup d'œil |

## Traçabilité

| Fichier | Fonction / bloc | Justifié par |
|---------|-----------------|--------------|
| `Collapse.jsx` | `useState(false)` | fermé par défaut |
| `Collapse.jsx` | `toggleCollapse` | ouvrir/fermer au clic |
| `Collapse.jsx` | `<button>` du header | `button` dans le header |
| `Collapse.css` | `.collapse-body` + `grid-template-rows` | animation 0fr → 1fr |
| `Collapse.css` | `.collapse-chevron.open` | flèche qui tourne |
