# Cadre agile (référence)

Charger ce fichier si l'auteur demande Scrum, Kanban, une user story, un DoD formel, ou une explication de l'agile.

Le `SKILL.md` reste la règle du quotidien. Ici : vocabulaire et cadres, sans théâtre.

## Manifeste (valeurs)

Travailler en préférant, à gauche :

1. Les personnes et les interactions, plutôt que les processus et les outils
2. Un logiciel qui fonctionne, plutôt qu'une documentation exhaustive
3. La collaboration avec le client, plutôt que la négociation contractuelle
4. L'adaptation au changement, plutôt que le suivi d'un plan

La colonne de droite n'est pas interdite. Elle ne gagne pas contre un incrément qui marche.

## Douze principes (ce qu'on en fait ici)

| Principe | Action agent |
|----------|----------------|
| Livrer tôt et souvent | Premier incrément dans la session, pas à la fin du projet |
| Accueillir le changement | Le brief nouveau gagne, même tard |
| Livrer fréquemment | Tranches verticales, chacune démontrable |
| Métier + dev ensemble | Montrer à l'auteur, pas disparaître derrière un plan |
| Faire confiance | Pas de gold plating pour « avoir l'air pro » |
| Face à face | Une démo courte > un roman dans le chat |
| Logiciel qui marche = mesure | Voir `SKILL.md` |
| Rythme soutenable | Pas cinq modules à 2h du matin |
| Excellence technique | Niveau senior (`pratiques-dev-senior`), pas un framework inventé |
| Simplicité | Maximiser le travail **non** fait (YAGNI) |
| Auto-organisation | Choisir la plus petite tranche utile, sans attendre 40 tickets |
| Inspecter / adapter | Après chaque incrément : garder, jeter, ajuster |

## Scrum : seulement si ça colle

Scrum suppose : une équipe, un Product Owner, un timebox (sprint), un objectif de sprint, un incrément potentiellement livrable.

**Utiliser** si l'auteur demande explicitement un sprint, un backlog d'équipe, ou un livrable « on travaille en Scrum ».

**Ne pas inventer** sur un projet solo, un fix, un composant unique.

Événements (si Scrum est vraiment en cours) :

- **Sprint** : timebox. Un Sprint Goal, pas une liste fourre-tout.
- **Planning** : quoi dans **ce** sprint, assez petit pour un incrément.
- **Daily** : 3 fichiers HTML n'ont pas besoin d'un daily markdown.
- **Review** : démontrer l'incrément à l'auteur. Demander le feedback. Adapter.
- **Rétro** : une ou deux actions concrètes, pas un slide.

Artefacts : Product Backlog, Sprint Backlog, Increment.
Engagements : Product Goal, Sprint Goal, Definition of Done.

Empirisme : transparence, inspection, adaptation. Sans ça, les rituels ne servent à rien.

## Kanban : flux

Utile en solo / agent : visualiser, **limiter le WIP**, finir avant de commencer.

Politique par défaut ici : **WIP = 1 incrément**.

Pas besoin de colonnes Jira pour respecter ça.

## User stories (si on en écrit)

Format : *En tant que [qui], je veux [quoi], afin de [pourquoi métier].*

INVEST : Independent, Negotiable, Valuable, Estimable, Small, Testable.

Critères d'acceptation : liste visible / pas visible, ou Given / When / Then si l'auteur le demande.

Découper si : pas testable seule, pas démontrable, « et » trop de fois, ou plus d'une session.

Les story points, velocité, burndown : seulement si l'auteur les demande comme livrable. Pas pour piloter un agent solo.

## Definition of Ready vs Done

- **Ready** : critères d'acceptation clairs, assez petit, dépendances connues. Sinon on ne commence pas.
- **Done** : voir le minimum dans `SKILL.md`. On n'élargit pas le DoD avec ce que l'incrément n'utilise pas (design system, BEM, couches « pour plus tard »). L'a11y réelle de l'UI livrée en fait partie.

## Review vs rétro

- Review = **le produit** (ça marche ? on garde ?).
- Rétro = **la façon de travailler** (une friction, une action).

Ne pas confondre les deux. Ne pas produire un compte-rendu de rétro pour un collapse de 40 lignes, sauf demande.
