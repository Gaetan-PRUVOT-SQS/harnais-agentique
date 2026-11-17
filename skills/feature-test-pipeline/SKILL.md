---
name: feature-test-pipeline
description: Qualité des tests d'une feature ou d'un correctif, boucle d'échec jusqu'au vert, excuses refusées, critères de fin. Complète iso-29119 et tests-regression-auto.
---

# Pipeline de test d'une feature

Ce skill ne refait pas ce que d'autres disent déjà : stratégie, techniques, oracle et incidents sont dans `iso-29119`, le lancement et la boucle dans `tests-regression-auto`, le lieu d'exécution dans `tests-locaux`, la sécurité dans `security-gate`, la revue dans `revue-validation`. Ici : la qualité des tests eux-mêmes, la boucle d'échec, et ce qui compte comme fini.

Règle permanente : aucun échec toléré. La feature n'est finie que quand toute la suite est verte sur le dernier état du code.

## Règles dures

1. Jamais affaiblir un test pour passer au vert : pas de `.skip`, `xit`, `@Ignore`, `-x test`, pas d'assertion relâchée, pas de timeout allongé au hasard, pas de seuil abaissé, pas de retry ni de `sleep` en guise de correctif. Un test change seulement s'il est prouvé faux, et la raison est écrite dans la section Tests de la justification.
2. Le vert se juge sur la commande lancée dans cette session, sur l'état final : code de sortie, nombre de cas passés, échoués, sautés.
3. Un échec se corrige à la racine, puis on relance tout. Après 5 itérations sans progrès, on change d'approche : hypothèses déjà écartées écrites, relecture à contexte vierge par `explorateur` ou `relecteur`, puis on continue. On s'arrête seulement si le dernier remède est irréversible ou demande une décision de l'auteur.
4. Pas de secret, de rapport généré ni de sortie de build au dépôt. Les tests sont déterministes.

## Écrire de bons tests

- Tester le comportement par l'interface publique, là où les appelants s'en servent, pas les fonctions privées. Un test qui casse sur un refactor sans changement de comportement est lié à l'implémentation : on le réécrit.
- Valeurs attendues venues d'une source indépendante : calcul fait à la main, spec, exemple connu. Un test qui recalcule l'attendu comme le code (`expect(sum(a, b)).toBe(a + b)`) passe par construction et se refuse.
- Mocker seulement ce qu'on ne contrôle pas : API tierce, horloge, aléa, parfois réseau ou système de fichiers. Les modules du projet se testent en vrai ou avec un faux.
- Vérifier par l'interface (créer puis relire) plutôt que dans le stockage, sauf quand l'exigence porte sur le stockage : mot de passe haché, donnée chiffrée, enregistrement vraiment effacé.
- Voir chaque nouveau test échouer une fois, pour la bonne raison, avant de le faire passer.
- Snapshots, fichiers de référence et fixtures enregistrées sont des valeurs attendues. Les régénérer suit la règle 1 : chaque changement est lu dans le diff et justifié comme une assertion modifiée.
- Le TDD en tranches verticales (un test rouge, le code minimal, le suivant) se fait sur demande explicite de l'auteur, pas par défaut. Dans tous les cas, le test du défaut s'écrit et échoue avant le correctif.

Propriétés : quand le code a une règle vraie pour toute entrée (aller-retour `decode(encode(x)) == x`, inverse, comparaison avec une implémentation de référence simple, idempotence, invariant, vérificateur bon marché), ajouter un test de propriété (fast-check, Hypothesis, proptest, RapidCheck). Affirmer la propriété la plus forte possible, jamais « ne plante pas » seul. Construire des entrées valides dans le générateur au lieu de filtrer. Chaque contre-exemple trouvé reste comme test d'exemple. Ajouter une bibliothèque de propriétés est une décision de dépendance, à annoncer.

Mutation : sur le code modifié à risque élevé, StrykerJS, PIT ou Mull montrent que les tests échouent quand le code est faux. Chaque mutant survivant est un test manquant (on l'ajoute) ou un mutant équivalent (prouvé par écrit). Un mutant en dépassement de temps ne prouve rien. Score et survivants vont dans la section Tests.

Outils par pile (le linter et le formateur du projet font foi) :

| Pile | Tests | Analyse |
|---|---|---|
| React, TS | Vitest + Testing Library, requêtes par rôle ou label | ESLint, `tsc --noEmit` |
| Android | JUnit, MockK, Robolectric, Compose UI test | Android Lint, ktlint, detekt |
| C | CMocka, Unity ou Check, CTest | `-Wall -Wextra -Werror`, sanitizers, valgrind, cppcheck, clang-tidy |
| Python | pytest + pytest-cov | ruff, mypy |

E2E : `qa-e2e`, avec le lanceur déjà présent dans le dépôt (Playwright ou Cypress). Serveurs de test sur `127.0.0.1`, jamais `0.0.0.0`. Pas d'attente fixe, on attend l'état.

## Boucle d'échec

1. Reproduire le test en isolation, garder logs et trace.
2. Classer : défaut du produit, défaut du test, environnement, intermittent (passe au rejeu, c'est un incident).
3. Noter l'incident : attendu, obtenu, étapes, gravité, cause (`iso-29119`).
4. Corriger la cause. Pour un test instable on retire le non-déterminisme (horloge figée, graine, fichiers isolés), on ne rejoue pas.
5. Confirmation : le test du défaut échoue avant le correctif, passe après.
6. Régression : toute la suite, sortie fraîche.

Défaut dont la cause n'est pas évidente :

- Avant de lire le code pour théoriser, obtenir une commande qui passe au rouge sur ce symptôme exact : test au plus près, script avec fixture, requête rejouée, `git bisect run`. Rapide et déterministe. Pour un défaut intermittent, monter le taux de reproduction (boucles, charge, parallélisme), sans jamais le masquer.
- Réduire la reproduction jusqu'à ce que chaque entrée restante serve.
- Écrire 3 à 5 hypothèses classées, chacune avec une prédiction qui peut la démentir, et les tester une variable à la fois.
- Les logs de debug temporaires portent un préfixe unique (`[DEBUG-a4f2]`) et se cherchent jusqu'à zéro avant le commit. Aucun secret dans un log, écrire `<REDACTED>`.
- Si on a forcé un rouge en changeant du code ou une fixture, vérifier par un `git diff` que le changement s'est bien appliqué.

## Excuses qui ne justifient jamais un rouge

| Pensée | Action |
|---|---|
| « Cet échec n'a rien à voir avec mon changement » | Le prouver sur l'état d'avant. Si c'est déjà rouge, le dire comme bloquant : la feature n'est pas finie. |
| « C'est instable, un rejeu passera » | Un passage au rejeu est un incident intermittent. Chercher le non-déterminisme. |
| « Un timeout plus long règle ça » | Trouver ce que le test attend vraiment et attendre cet état. |
| « L'assertion est trop stricte » | La changer seulement avec la preuve que l'attendu est faux. |
| « La couverture est presque suffisante » | Sous 90 %, ou sous un critère de fin écrit plus haut, ce n'est pas fini. |
| « Ça passait tout à l'heure » | Seul le lancement complet sur l'état actuel compte. |
| « Le sous-agent dit que ça passe » | Relancer et lire la sortie soi-même. |
| « Le test contredit la spec » | S'arrêter, rapporter le test, son attendu et la ligne de spec. Ne jamais plier le code autour du test (cas spécial sur son entrée, valeur en dur, état gardé entre appels), ni modifier le test pour coller au code. |

## Critères de fin

- [ ] Suite complète verte : 0 échec, 0 sauté, 0 mis de côté, aucun test instable.
- [ ] Couverture mesurée, au moins 90 % sur chaque couverture rapportée (`iso-29119`), sur le code livré. Le seuil écrit avant la campagne ne descend pas sous ce plancher. Branches rapportées quand l'outil le peut. Non mesurable : dit dans la section Tests, le critère reste ouvert. On n'abaisse pas le seuil après coup et on n'exclut pas du code pour faire le chiffre.
- [ ] Contrôle de sécurité OK (`security-gate`, `norme-cybersecurite`).
- [ ] Aucun réglage de test, seuil ou lanceur affaibli sans raison écrite.
- [ ] Lint, types et analyse statique propres pour la pile.
- [ ] Chaque critère d'acceptation relié à au moins un test qui passe, par le nom du test.
- [ ] Chaque correction a son test de régression, vu échouer avant et passer après.
- [ ] Chaque « fini », « vert », « corrigé » s'appuie sur une commande de cette session avec code de sortie et comptes.

## Commit

Un commit local par feature validée, tests de régression inclus, fichiers ajoutés un par un, message en français, court, naturel (`Scénario FAT32, régressions ok`). Les détails des tests vont dans la section Tests de `docs/justifications/<slug>.md`, pas dans le message. Pas de push sans demande.

## Rapport de fin

Section Tests de la justification (modèle : `iso-29119/modeles/section-tests.md`), puis quelques lignes dans le compte rendu : périmètre, techniques, cas passés ou échoués, couverture, évaluation des critères de fin, incidents, écarts, risque résiduel.
