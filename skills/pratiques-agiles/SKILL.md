---
name: pratiques-agiles
description: >-
  Use when planning, slicing, scoping or claiming work done: one useful increment, acceptance criteria, YAGNI, no unasked extras. Triggers: agile, user story, DoD, DevOps, DORA, "tant que tu y es".
---

# Pratiques agiles (PERMANENT)

## Invariant

**PERMANENT jusqu'à nouvel ordre explicite de l'auteur.**

On livre de la valeur par **tranches qui marchent**, adaptées à la taille du problème.

Violer la lettre, c'est violer l'esprit.

**REQUIRED:** si l'auteur demande Scrum, Kanban, stories, DoD formel, ou « c'est quoi l'agile » → `references/cadre.md`.

**REQUIRED:** dès qu'un projet a un pipeline, un déploiement, une prod ou une exploitation, ou si l'auteur demande du DevOps, du CI/CD, des métriques DORA, des tests avant déploiement, un post-mortem ou de l'infra as code → `references/devops.md`.

## Mesure du progrès

Un incrément **démontrable** (l'utilisateur voit un résultat). Pas un plan, pas un socle, pas un board, pas cinq modules à 40 %.

## Un incrément

1. **Critères d'acceptation** écrits **avant** le code (visible / pas visible). Ils sont la base de test : chaque critère est couvert par au moins un modèle et un cas de test (`iso-29119`).
2. **Tranche verticale** : un parcours bout en bout, pas « tous les modèles puis tous les écrans ».
3. **WIP = 1** : un incrément ouvert. Pas auth + dashboard + paiements en parallèle.
4. Assez petit pour le montrer dans **cette** session. Trop gros → découper.
5. **DoD** tenue avant de dire « c'est fait ».

Découper dès que : pas démontrable seul, plus d'une session, ou « et aussi » dans la même phrase.

## Plan court

Pour un changement incertain ou sur plusieurs fichiers : fichiers, ordre, tests qui prouvent. Écrit avant le code, puis on code sans attendre un accord. Si ça dérape, on réécrit ce plan avant de patcher au jugé. Un diff d'une phrase se code directement. Le plan ne prouve rien : la sortie fraîche prouve.

`AGENTS.md` porte la même règle. S'il contredit ce fichier, il prime.

## Automatisation

Après le commit, une passe. Un contrôle encore manuel qui peut devenir un cas stable entre dans la suite du projet. Le reste est nommé. Pas de tâche de fond, pas de worktree, pas de nouveau pipeline. Les bandes DORA ne sont pas un quota (`references/devops.md`).

Un contrôle qui revient entre dans la suite, et ce cas se relance sans question. S'il n'y a rien à ajouter, on le dit en une ligne. Une horloge, un gateway ou une livraison vers un chat attend une demande explicite : rien ne s'arme en silence, et un cas de suite n'en crée pas un autre. `AGENTS.md` porte la même règle.

## Boucle

Le critère mesurable de la tranche est fixé avant d'agir, et il inclut la preuve fraîche. On s'arrête quand il est tenu. Le même appel en échec ne se relance pas tel quel. Pas de chantier hors demande, pas de boucle de fond.

On garde le candidat qu'une commande mesure le meilleur. Un score moins bon, ou pas mesuré, ne le remplace pas. Pas de population ni de boucle d'évolution : graine, évaluateur, sortie et budget restent ceux que la demande nomme. `AGENTS.md` porte la même règle.

`AGENTS.md` porte la même règle. S'il contredit ce fichier, il prime.

## Definition of Done (minimum)

- Critères d'acceptation tenus
- Vérifié maintenant (sortie fraîche citée, tests → `tests-locaux`)
- Critères de fin des tests tenus, au moins 90 % sur chaque couverture rapportée (`iso-29119`)
- Rien hors brief
- Code au niveau senior (`pratiques-dev-senior`)
- Feature nouvelle → `docs/justifications/` local (`justifier-choix-techniques`)
- Aucun socle / store / API / design system **non utilisé** par cet incrément
- Projet avec une prod : l'incrément passe par le pipeline (`main` vert, déploiement rejouable, retour arrière connu), voir `references/devops.md`

Pas de DoD = pas fait.

## YAGNI (le piège n°1)

Le brief n'a pas demandé : **on ne fait pas**.

Store, design system, API, dossier `features/`, tokens, yup, captcha, 2FA, page admin « on s'en servira » : **supprimer**, pas garder.

« Hygiène » / « c'est un vrai produit » / « un camarade ferait le service » ≠ licence.

40 minutes déjà passées sur un socle inutile : **on jette**. Le coût est déjà perdu. Garder = gold plating.

## Changement de brief

Le brief **nouveau** gagne tout de suite.

Stopper l'ancien travail. Le retirer du livrable. Ne pas le finir « pour ne pas jeter ». Ne pas merger l'ancien et le nouveau « au cas où ».

## Taille du problème

| Contexte | Faire | Ne pas faire |
|----------|--------|----------------|
| Solo, 1-3 fichiers | Incrément + critères + démo | Sprint, story points, daily, burndown, Jira, SAFe |
| L'auteur demande une équipe / un sprint / un board **dans le livrable** | Produire l'artefact demandé, **travailler** quand même par incrément | Remplacer le logiciel qui marche par du théâtre |
| Flux continu | Limiter le WIP, avancer une carte | Inventer des sprints vides |

« Sois pro » / « le prof veut de l'agile » → incrément qui marche, pas un Playbook Scrum.

## Interdit

- Waterfall : architecture / design system / tous les modèles **avant** une page qui marche
- Intégrer à la fin, « on branchera demain matin »
- Cinq demi-features plutôt qu'une complète
- Scope hors brief glissé pendant que « on y est »
- Dire « fait » sans parcours visible et vérifié
- Déployer à la main, geler `main`, corriger en prod sans passer par le dépôt (`references/devops.md`)
- Défendre le plan contre un brief qui a changé

## Autres skills

Sur demande de l'auteur seulement : designer **le prochain incrément**, pas le produit entier (`brainstorming`), et planifier un incrément, pas un Gantt (`planning-and-task-breakdown`). Doc de **cet** incrément, pas une bible (`justifier-choix-techniques`).

## Désactivation

**Uniquement** si l'auteur dit : « arrête les pratiques agiles », « plus d'agile ». Une demande explicite du tour en cours prime (AGENTS.md) ; seules les formulations vagues ci-dessous ne désactivent pas.

« fais tout », « sois pro », « extra features », « le prof veut du scrum », « on a deux semaines » ≠ désactivation.

## Rationalisations à rejeter

| Excuse | Réalité |
|--------|---------|
| « On garde le store / le design system pour plus tard » | Socle non utilisé = gold plating. Jeter. |
| « 40 min déjà passées, jeter c'est du gâchis » | Le coût est perdu. Garder ajoute de la dette. |
| « Yup / captcha / admin, c'est de l'hygiène » | Hors brief = hors incrément. |
| « Plus y en a, mieux c'est pour le prof » | Plus de **valeur démontrable**, pas plus de fichiers. |
| « Socle d'abord, pages ensuite, on a le temps » | Waterfall. Une page qui marche dès le premier jour. |
| « Je finis X (20 min) puis je commence Y » | X est hors brief. Stop. Y tout de suite. |
| « Cinq modules en parallèle, on intègre à 8h » | Cinq demi-trucs. Une tranche bout en bout. |
| « Board Scrum / points / daily sur un projet solo » | Théâtre. Incrément + critères. |
| « Hybride : je garde X et j'ajoute Y au cas où » | Le brief a viré X. X sort du livrable. |
| « C'est fait, le code est écrit » | Pas de DoD, pas fait. |

## Drapeaux rouges - STOP

- Tu ajoutes un store, une API ou un design system que l'incrément n'utilise pas
- Tu as plus d'un incrément ouvert
- Pas de critères d'acceptation et tu codes déjà
- Tu vas dire « c'est fait » sans démo / vérif
- Tu inventes sprint / points / Jira pour 3 fichiers
- Tu termines une feature que le brief vient d'annuler
- Tu glisses yup, captcha, admin, 2FA « tant que tu y es »

→ Couper le hors-scope. Un incrément. Critères. DoD. Puis seulement livrer.
