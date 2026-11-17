---
name: pratiques-dev-senior
description: >-
  Pratiques de dev senior, permanentes dans tous les projets de l'auteur. Use when writing, reviewing, refactoring or delivering code, or when tempted to skip tests or error handling.
---

# Pratiques de dev senior

## Invariant

**PERMANENT.** Tous les projets, sans mode ni question sur le mode. Un brief ou un sujet (OpenClassrooms) fixe le périmètre et les contraintes imposées, jamais le niveau du code.

Livraison : français, zéro trace d'outil, une tranche à la fois. Après la feature : tests d'intégration et régressions dans le projet, correction si KO, validation si OK, commit, automatisation maximale, check sécu OK.

## Conception

- Proportionnée au besoin : la solution la plus simple qui tient, pas de couche « pour plus tard » (YAGNI)
- Barre ligne à ligne avant d'écrire et en relecture : `revue-minutieuse`
- Une responsabilité par fonction, module ou composant ; découper dès que ça clarifie
- Noms précis qui rendent les commentaires inutiles
- Données et effets séparés : logique pure testable, I/O aux bords
- Refactor quand le code touché le demande, dans la même tranche et sous tests

## Robustesse

- Erreurs gérées explicitement : pas de `catch` vide, message utile, état cohérent après échec
- Entrées validées aux frontières (formulaire, API, fichier, argv)
- Typage strict quand le langage le permet ; TypeScript sur un nouveau projet JS sauf brief contraire
- Pas de valeur magique ni de duplication qui dérive
- C : le code C se compile avec gcc -Wall -Wextra -Werror. Retours vérifiés, mémoire libérée, fuites contrôlées (valgrind ou `-fsanitize=address,undefined`). Le style est celui d'AGENTS.md : le code C respecte la norme 42, seul le bandeau 42 est exclu.

## Tests

- Tests du stack présents (Vitest, Jest, Playwright, pytest, Django, `make test`), sinon le plus léger possible
- Tests conçus par technique selon le risque (`iso-29119`) : partitions, valeurs limites, tables de décision, transitions d'états ; MC/DC pour le code à risque élevé (droits, sécurité, noyau) ; couverture mesurée comme critère de fin, au moins 90 % sur chaque couverture rapportée
- Régression ajoutée pour chaque bug corrigé, écrite avant la correction
- `tests-locaux` et `tests-regression-auto`, sortie réelle de la session
- Après la feature : tests d'intégration du comportement touché et suite de régression. KO : correction, puis on relance. OK : `revue-validation`, puis le commit, puis l'automatisation maximale (`tests-regression-auto`)
- Une relecture demandée comme telle : `revue-validation`, sans élargir le changement
- Build, jobs, QEMU ou émulateur sur ce poste : `poste-dev`

## Front

- React : composants découpés, props typées ou destructurées selon le repo, hooks personnalisés quand une logique se répète, état au plus près de son usage
- Accessibilité réelle : HTML sémantique, clavier, focus visible, labels, contrastes
- CSS selon la convention du projet ; pas de design system si le projet n'en a pas besoin

## Contraintes imposées

- OpenClassrooms et autres briefs : techno imposée respectée, mais code et tests au niveau senior
- Conventions, formateur et linter du dépôt priment sur les goûts. En C, le formateur est norminette, pas clang-format. Conventional Commits seulement si le dépôt les suit.

## Toujours

- Français et zéro mention d'assistant : règles permanentes d'AGENTS.md, déjà en contexte, rien à recharger ; `ecriture-naturelle` pour le ton
- `norme-cybersecurite` : baseline partout, OWASP du flux touché, audit complet si auth, données ou paiement
- `justifier-choix-techniques` pour une feature nouvelle
- `revue-minutieuse` : chaque ligne du changement comprise, nécessaire, vivante
- Commentaires rares et courts, en français ; jamais de code commenté. En C, norminette refuse un commentaire qu'elle ne place pas.

## Jugement

- Cadrer avant de coder : reformuler le problème et le pourquoi, fixer les critères de succès et le hors périmètre ; la bonne réponse est parfois plus petite, ou pas de code
- Comprendre avant de changer : lire le code, `git log`, les tests et les tickets pour savoir pourquoi une chose existe avant de la retirer ; refactorer par étapes sous tests, jamais de réécriture complète sans preuve
- Arbitrer explicitement : recommander une option, dire ce qu'elle coûte et ce qu'on abandonne, en coût total (exploitation, maintenance), pas seulement en temps de dev
- Trier par réversibilité : décision interne ou outillage, décider vite et mesurer ; schéma exposé, API publique, langage ou fournisseur, justification écrite (`justifier-choix-techniques`) avec pré-mortem
- Technologie connue et maintenue par défaut ; une seule nouveauté par projet, justifiée
- Déboguer en scientifique : reproduire par un test qui échoue, lire l'erreur et la pile en entier, une hypothèse, une expérience, `git bisect` si la régression est datée ; corriger la cause, nommer un contournement comme tel
- Faire marcher, puis propre, puis vite : mesurer avant d'optimiser, garder la version simple sans gain démontré
- Penser exploitation dès la conception : déploiement, diagnostic, migration et retour arrière ; ce qui ne s'observe pas ou ne s'annule pas n'est pas prêt
- Dire non ou « pas comme ça » avec les faits, une alternative et le coût de chaque voie, puis appliquer la décision prise
- Après un bug ou une régression : deux lignes de rétro (cause racine, garde-fou ajouté)

## Drapeaux rouges. STOP

- Code « simple pour un débutant » qui sacrifie la gestion d'erreurs ou les tests
- Sur-ingénierie : abstraction, store ou API sans besoin actuel
- Une ligne du changement qu'on ne peut pas expliquer, ou du code mort dans le diff (`revue-minutieuse`)
- Livrer une UI sans parcours clavier
- Annoncer vert sans sortie de tests de cette session
