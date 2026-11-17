# Exemples de commits

Commande type (après `status` / `diff` / `log`, fichiers listés un par un) :

```bash
git add -- src/components/Collapse.jsx src/components/Collapse.css
git commit -m "Collapse fermé par défaut, on voit d'abord le titre"
```

Un message sur plusieurs lignes passe par un fichier ou un HEREDOC, jamais
par plusieurs `-m`. C'est rare : une ligne suffit presque toujours.

## Bons messages

```
Passage à Alpine, on ne garde que le matériel
Collapse fermé par défaut, on voit d'abord le titre
Faute sur le bouton Connexion
node_modules sort du suivi git
Les .env ne partent plus sur GitHub
```

## Mauvais messages

```
feat(ui): implement accessible accordion
Ajoute le composant Collapse, corrige le style et met à jour la doc
Update files
WIP
fix
Generated with Claude Code
```

Le deuxième sonne comme un outil : verbe systématique, énumération, phrase
lissée.

## PR (sur ordre)

Titre FR, même style qu'un message de commit.

Corps :

```
## Résumé
Le panneau des fiches est fermé par défaut.

## Comment tester
- [ ] Ouvrir une fiche logement : le panneau est fermé
- [ ] Clic sur le titre : le texte s'ouvre, la flèche tourne
```

Aucun trailer d'assistant. Aucune mention d'IA. Aucune info personnelle dans
un dépôt public.
