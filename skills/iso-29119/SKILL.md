---
name: iso-29119
description: >-
  Tests ISO/IEC/IEEE 29119 et ISTQB CTFL : risques, partitions, limites, tables, MC/DC, confirmation, régression, oracle après sous-agent. Use when designing, running or reporting tests.
---

# Tests à la ISO/IEC/IEEE 29119

La série 29119 est la norme internationale du test logiciel ; elle a
remplacé IEEE 829 et BS 7925. On en reprend ce qui rend les tests
meilleurs : un vocabulaire commun, une stratégie fondée sur les risques,
une chaîne traçable de la base de test jusqu'aux cas, des techniques avec
leur couverture mesurée, des critères de fin et des incidents
exploitables. On laisse la paperasse : conformité adaptée (« tailored
conformance », clause 4 de chaque partie normative), dont chaque
adaptation est justifiée ici, avec une documentation qui vit dans la
justification et dans le code des tests. Références : éditions 2021 et
suivantes, qui ont remplacé les conditions de test par les modèles de
test.

Voisins : tests-locaux (où et comment lancer), tests-regression-auto
(boucle et blocage), pratiques-agiles (critères d'acceptation),
justifier-choix-techniques (section Tests), pratiques-dev-senior,
norme-cybersecurite (tests de sécurité), code-review (test statique),
wcag, web-perf, os-efficience, integration-systeme (niveaux sur un OS),
shell-maison (`compare-shells`), playwright-automation, api-testing,
vitest ; unit-testing et tdd sur demande.

## La série

| Partie | Sujet | Ce qu'on en tire |
|--------|-------|------------------|
| 29119-1:2022 | Concepts généraux (informative) | le vocabulaire, les pratiques |
| 29119-2:2021 | Processus de test | la chaîne de chaque feature, la stratégie par les risques |
| 29119-3:2021 | Documentation de test | où vit chaque information, en léger |
| 29119-4:2021 | Techniques de test | conception des cas et mesure de couverture |
| 29119-5:2024 | Tests pilotés par mots-clés | tests système et E2E lisibles |
| ISO/IEC TR 29119-6:2021 | 29119 en projet agile | correspondance avec critères d'acceptation, DoD, TDD, BDD |
| ISO/IEC TR 29119-11:2020 | Systèmes à base d'IA | non-déterminisme, données, oracles |
| ISO/IEC TR 29119-13:2022 | Systèmes biométriques | hors de nos besoins |

- 29119-8 (tests à base de modèles) est approuvée par l'IEEE en septembre
  2026 mais pas encore publiée par l'ISO : ne pas la citer comme publiée.
- Les textes sont payants : on s'appuie sur les sommaires et extraits
  publics (iso.org, OBP, aperçus), les résumés IEEE et
  softwaretestingstandard.org.
- Test statique : le concept est dans 29119-1 (4.1.5), les revues dans
  ISO/IEC 20246:2017 ; aucune norme publiée pour l'analyse statique.

## Vocabulaire (29119-1)

- Base de test : ce qui dit le comportement attendu (critères
  d'acceptation, sujet ou brief, spec POSIX ou RFC, page de manuel).
- Élément de test : ce qu'on teste (fonction, module, binaire, image).
- Modèle de test : la représentation de ce qu'on teste, propre à une
  technique (partitions d'un domaine, table de décision, diagramme
  d'états, grammaire, flot de contrôle). Depuis 2021, il remplace la
  « condition de test » des éditions 2013.
- Élément de couverture : ce qu'une technique demande de couvrir dans son
  modèle (une partition, une limite, une règle de table, une transition,
  une issue de condition).
- Cas de test : préconditions, entrées, résultat attendu.
- Procédure de test : les actions qui exécutent des cas ; chez nous, le
  code de test ou le scénario `qemu-test`.
- Oracle : ce qui dit si le résultat est juste (valeur attendue, outil de
  l'hôte, propriété).
- Niveaux : unitaire ou composant, intégration, système, intégration de
  systèmes, acceptation. Type : test centré sur une caractéristique de
  qualité (fonctionnel, sécurité, performance, accessibilité...).
- Pratiques décrites par 29119-1 (4.4) : tests à base de modèles, tests
  scriptés et exploratoires, tests fondés sur l'expérience, manuels et
  automatisés, en continu, dos à dos (« back-to-back » : notre OS comparé
  à l'hôte, `compare-shells`), A/B, mathématiques et fuzz.

## Stratégie par les risques (29119-2)

- Lister les risques produit de la feature : ce qui peut mal tourner et
  pour qui. Impact et probabilité de 1 à 3 chacun.
- Le risque décide des techniques, de la profondeur de couverture, des
  niveaux et des types :

| Risque | Exemples | Réponse de test |
|--------|----------|-----------------|
| Élevé | auth, droits, paiement, données perso, noyau, parseur d'entrée hostile, perte de données | table de décision ou transitions, limites, MC/DC à 100 %, tests négatifs, fuzz à graine, revue |
| Moyen | règle métier, formulaire, API interne | partitions, limites, branches à 100 % |
| Faible | affichage, texte, outil interne | cas nominal et un cas d'erreur |

Le plancher est immuable (`AGENTS.md`) : au moins 90 % sur chaque couverture rapportée. La table peut exiger plus (branches à 100 %, MC/DC à 100 %). Elle ne descend pas sous 90. On n'exclut pas du code pour faire le chiffre. Une mesure absente se dit dans la section Tests et laisse le critère ouvert.

- Types choisis d'après les caractéristiques d'ISO/IEC 25010:2023 que la
  feature touche : aptitude fonctionnelle, efficacité de performance,
  compatibilité, capacité d'interaction (accessibilité : wcag),
  fiabilité, sécurité (norme-cybersecurite), maintenabilité (analyse
  statique), flexibilité (multi-arch : `make test-all`), sûreté. 29119-4
  cite encore l'édition 2011 à huit caractéristiques.
- Critères de fin (« completion criteria ») écrits avant d'exécuter :
  tous les cas verts, au moins 90 % sur chaque couverture rapportée,
  aucun incident grave ouvert, check sécu OK.
- On n'exécute un niveau que si l'élément se construit et si l'oracle est
  écrit. Un outil absent ou un temps coupé se dit dans le résultat. Ça ne
  retire pas un risque élevé en silence.
- Le risque produit (ce que l'utilisateur subit) fixe la profondeur. Le
  risque projet (délai, outil, compétence) se rapporte, il ne réécrit pas
  le plan.

## ISTQB CTFL 4.0.1

Syllabus Foundation Level v4.0.1 (2024-09-15). Même socle que la 29119 :
test fondé sur le risque, modèles, traçabilité. Stuart Reid porte les
deux. Les techniques du chapitre 4 (partitions, limites, tables, états,
instructions, branches, supposition d'erreur, exploratoire) sont déjà
dans le tableau 29119-4. On ne les recopie pas.

Les sept principes deviennent des gestes :

| Principe | Geste |
|----------|--------|
| Le test montre des défauts | Une suite verte baisse la probabilité d'un défaut restant. Elle ne prouve pas qu'il n'y en a plus. Le rapport dit le risque résiduel. |
| L'exhaustif est impossible | Le risque et la technique choisissent l'échantillon. |
| Tester tôt | Les critères et les cas naissent avec le changement. Le statique passe avant l'exécution. |
| Les défauts se groupent | Un défaut trouvé amène un cas voisin sur le même module, en plus du cas qui le reproduit. |
| Les tests s'usent | Le même jeu de données finit par ne plus rien trouver. Quand le code ou le risque change, on ajoute ou on varie un cas. Le cas de régression déjà là reste. |
| Le test dépend du contexte | Un noyau et un formulaire n'ont pas la même profondeur. La table de risque tranche. |
| Zéro défaut sur la mauvaise cible | L'oracle vient de la base de test (brief, spec, page de manuel). Pas du code qu'on vient d'écrire. |

Gestes en plus, pour un dev seul :

- Confirmation, puis régression. Le cas du défaut échoue avant le
  correctif et passe après. La suite déjà là repasse. Les deux se disent.
- Pas de second testeur. L'indépendance tient parce que l'oracle est la
  base de test, et parce que la revue (`code-review`) relit sans réécrire
  le cas pour qu'il colle à l'implémentation.
- Pyramide : beaucoup de cas au niveau composant, moins en intégration,
  peu au niveau système. Un parcours de bout en bout ne remplace pas la
  table d'un risque élevé.
- On automatise ce qui est stable et ce qui porte un risque élevé. La
  passe après le commit est dans `tests-regression-auto`. Un cas
  intermittent est un incident. On ne le relance pas jusqu'à ce qu'il
  passe.
- Avant une modification, nommer ce qu'elle peut casser. La suite de
  cette zone repasse.

On ne reprend pas de l'ISTQB : les rôles d'examen, un test manager, les
quadrants comme cérémonie, un plan de test séparé, ni le texte du
syllabus.

## Chaîne de conception (29119-2)

Processus de conception et d'implémentation de 29119-2:2021 (8.2), en
quatre activités :

1. TD1, créer le modèle de test : pour chaque partie de la base de test,
   la technique choisie selon le risque donne un modèle identifié (`M1`,
   `M2`...) : domaine partitionné, table de décision, diagramme d'états.
2. TD2, identifier les éléments de couverture dans ce modèle.
3. TD3, dériver les cas de test : valeurs concrètes et résultat attendu,
   oracle explicite, jusqu'à couvrir les éléments visés.
4. TD4, créer les procédures : le code de test, automatisé, dans le
   projet, regroupé par niveau et par environnement (hôte, QEMU,
   navigateur).

- Les autres processus dynamiques : gestion de l'environnement et des
  données de test, exécution, rapport d'incident. Côté gestion : stratégie
  et planification, suivi et contrôle, fin de test.
- Traçabilité : le nom d'un cas dit sa technique et ce qu'il couvre
  (« limite mode 01000 invalide ») ; la section Tests de la justification
  relie base de test, modèle, éléments de couverture et cas.
- Exemple vérifié : `exemples/` (règle d'accès de type Unix,
  18 cas pilotés par une table, `make verifier`) et sa section Tests
  remplie dans `modeles/section-tests.md`.

## Techniques (29119-4)

| Technique | Éléments de couverture | Où ça paie |
|-----------|------------------------|------------|
| Partitions d'équivalence | une valeur par partition valide et invalide | formulaires, argv, arguments d'appel système |
| Valeurs limites (2 ou 3 valeurs) | chaque limite et ses voisines | tailles, index, `n - 1`, `PATH_MAX`, `INT_MIN`, dates |
| Arbre de classification | combinaisons de classes | options d'un outil, réglages |
| Test syntaxique | chaque règle de grammaire et ses mutations | parseurs : shell, cpio, ELF, JSON, HTTP |
| Combinatoire (toutes, par paires, chaque choix, choix de base) | paires ou valeurs à couvrir | options croisées, navigateurs et tailles d'écran |
| Table de décision | chaque règle | droits, règles métier, tarifs |
| Graphe cause-effet | combinaisons de causes | règles à contraintes entre entrées |
| Transitions d'états | états, transitions simples (0-switch), paires de transitions (1-switch) ; chez nous aussi les transitions invalides, refusées | TCP, processus, discipline de ligne, composant React, tunnel de commande |
| Scénarios | parcours principal et alternatifs | E2E Playwright, cas d'usage |
| Aléatoire | profil d'entrées, graine affichée | fuzz d'appels système et de parseurs |
| Métamorphique | relations entre exécutions | sans oracle : tri (permutation), aller-retour compression, filtre inclus dans la liste complète, OS comparé à l'hôte |
| Fondée sur les exigences | chaque exigence | critères d'acceptation, sujet |
| Instructions, branches, décisions | instructions, branches | tout code, plancher 90 % |
| Conditions de branche, combinaisons, MC/DC (« MCDC testing ») | issues de conditions | décisions à plusieurs conditions dans du code à risque élevé |
| Flot de données | paires définition et usage | code à états mutables (allocateur, cache) |
| Supposition d'erreur | liste d'erreurs typiques | partout, après les autres techniques |

Chaque technique définit ses éléments de couverture (29119-4, clause 5)
et sa mesure de couverture en pourcentage (clause 6).

## Ordre de l'oracle

L'oracle dit si le résultat est juste. On prend la source la plus forte
qui existe, et on écrit ce qu'elle ne couvre pas.

1. La base de test prime quand elle donne le résultat : brief, spec,
   page de manuel, critères. Valeur, état, code de sortie.
2. Référence indépendante, si la base ne donne pas la valeur, ou en
   plus : ancien système, version simple, opération inverse. Deux
   enveloppes du même code ne sont pas indépendantes.
3. Propriété ou relation, dans le même cas. Elle complète les exemples.
   Elle ne remplace pas une valeur que la base donne déjà.
4. Implicite, toujours : plantage, sanitizer, fuite, blocage, sortie
   mal formée. L'absence de plantage ne prouve pas le comportement.
   Un test qui ne fait qu'appeler, ou qui vérifie seulement qu'un
   objet existe, laisse le critère ouvert.

On affirme le contrat observable. L'ordre instable, l'heure, l'adresse
et le libellé restent dehors, sauf si la base les exige.

Un instantané écrit dans le même changement reprend la sortie du code.
Il ne devient un oracle que si la base, déjà écrite, donne cette sortie.
Le savoir du modèle sans ancre externe ne donne pas le résultat attendu.

## Propriété et différentiel

Une fonction pure (parseur, format, calcul) se tient par une propriété
écrite avant le code : aller-retour, invariant, idempotence, ou le même
résultat que la version simple. L'outil du langage tire les entrées et
réduit l'échec (Hypothesis, fast-check, proptest). Le cas minimisé reste
dans la suite. Les exemples choisis pendant l'écriture ne remplacent pas
cette propriété quand elle existe. La propriété s'ajoute à la base. Elle
prend sa place seulement si la base ne donne pas la valeur.

Un remplacement se compare à l'ancien système sur des entrées tirées.
On écarte l'ordre instable et l'horodatage avant de comparer. Un écart
voulu est noté, avec la raison. Le reçu de la feature est dans
`revue-validation`.

Erreurs typiques à essayer :

- C : off-by-one, `NULL`, taille 0, débordement d'entier, chaîne non
  terminée, retour ignoré, descripteur non fermé, fuite sur chemin
  d'erreur.
- TS et React : `undefined`, course entre requêtes, état périmé dans une
  closure, clé de liste, double soumission, fuseau horaire, Unicode.
- PHP, Django, MongoDB : injection, accès à l'objet d'un autre (IDOR),
  pagination aux bornes, transaction à moitié faite, N+1.
- Noyau : interruption au milieu d'une section, pid réutilisé, page
  retirée pendant une copie user, allocation qui échoue.

## Mesurer la couverture

- C avec gcc (vérifié ici avec gcc 16.2.1) : compiler l'élément de test
  avec `--coverage -fprofile-abs-path -fcondition-coverage`, lancer les
  tests, puis `LC_ALL=C gcov -b -g -o DOSSIER_OBJETS fichier.o` : lignes,
  branches et issues de conditions (MC/DC). `LC_ALL=C` parce que gcov
  traduit ses messages. `exemples/verifier-couverture RESUME [SEUIL]`
  échoue sous le seuil (sh POSIX, 6 tests bats).
- clang : `-fprofile-instr-generate -fcoverage-mapping -fcoverage-mcdc`,
  puis `llvm-profdata merge` et `llvm-cov report`, avec les outils de la
  même version de LLVM que le compilateur.
- Vitest : `vitest run --coverage`, seuils dans `coverage.thresholds`
  (lignes, branches, fonctions, instructions) ; pytest : `coverage run
  --branch -m pytest` puis `coverage report --fail-under=N` ; PHPUnit :
  PCOV ou Xdebug, `--coverage-text`.
- Noyau : la logique pure se teste et se mesure sur l'hôte ; dans QEMU,
  la preuve passe par les programmes de test (integration-systeme).
- Plancher immuable : au moins 90 % sur chaque couverture rapportée
  (lignes ou instructions, branches prises au moins une fois, issues de
  conditions quand l'outil les donne). Le seuil passé à l'outil ne
  descend pas sous 90. `verifier-couverture` reste à 100 par défaut. Son
  second argument accepte n'importe quel entier : le test qui lui passe
  80 montre le paramètre, il n'autorise pas une suite livrée sous 90.
- La couverture est un critère de sortie, pas un but : 100 % de lignes
  avec de mauvais oracles ne prouve rien. Le test de mutation (Stryker,
  mutmut, skill unit-testing) mesure la force des oracles.

## Exécution, incidents, fin

- Environnement et données de test : fixtures dans le projet, graine
  affichée, versions épinglées (tests-locaux, integration-systeme).
- Exécution : sortie fraîche, nombre de cas passés et échoués
  (tests-regression-auto).
- Incident (rubriques de 29119-3, 8.11) : date, auteur, contexte (élément
  et version, environnement), description (étapes, attendu, obtenu),
  gravité, priorité, risque, statut. Le test qui le reproduit s'écrit
  avant la correction et reste comme test de régression.
- Suivi : on compare au plan (cas verts, couverture, incidents ouverts) et
  on ajoute des cas là où le risque le demande.
- Fin (rubriques de 29119-3, 7.4) : ce qui a été testé, écarts au plan,
  évaluation face aux critères de fin, blocages, mesures, risques
  résiduels, ce qui se réutilise, leçons ; en quelques lignes dans la
  justification et dans le compte rendu final.

## Documentation légère (29119-3 adaptée)

| Information de 29119-3 | Où elle vit chez nous |
|------------------------|------------------------|
| Politique de test | AGENTS.md |
| Pratiques de test de l'organisation | skills tests-locaux, tests-regression-auto, iso-29119 |
| Plan de test | section Tests de `docs/justifications/<slug>.md` (risques, techniques, couverture visée, critères de fin) |
| Spécifications du modèle, des cas et des procédures | le code des tests : noms de cas, tables de cas ; le modèle dans la section Tests |
| Besoins et état de préparation des données et de l'environnement | fixtures, Makefile, versions épinglées |
| Résultats obtenus et verdicts, journal d'exécution | sortie du lanceur dans `build/`, jamais poussée |
| Rapport d'incident | test de régression et ligne dans la section Tests |
| Rapports d'avancement et de fin | section Tests (Résultat) et compte rendu final |

- 29119-3 accepte le papier comme l'électronique (outils, tableurs,
  photos de tableau blanc) et laisse adapter noms et contenus ; TR 29119-6
  parle de documents bien moins détaillés en agile.
- Modèle à copier : `modeles/section-tests.md`, proportionné au risque
  (un risque faible tient en trois lignes).

## Test statique

- Revues et analyse statique trouvent des défauts sans exécuter :
  code-review, shellcheck, `tsc --strict`, eslint, clang-tidy. Elles
  comptent dans la stratégie, surtout pour le risque élevé.
- Le déroulement de la revue et la validation par exécution du parcours
  sont dans `revue-validation`. Les techniques de test restent ici.

## Mots-clés (29119-5)

- Tests système et E2E écrits avec des actions métier (`seConnecter`,
  `ajouterAuPanier`) bâties sur des mots-clés de bas niveau (cliquer,
  saisir) : Page Objects de Playwright, étapes de `qemu-test`. Chaque
  mot-clé est testé une fois, puis réutilisé.

## IA (TR 29119-11)

- Fonction à base de LLM ou dataset SFT : sortie non déterministe, donc
  propriétés et relations métamorphiques plutôt que valeur exacte, jeu de
  test séparé des données d'entraînement, graine et température fixées
  quand c'est possible, seuils statistiques écrits. L'oracle déterministe
  passe devant : code de sortie, contenu de fichier, outil de l'hôte,
  invariant, réponse connue. Un juge qui est lui-même un modèle s'emploie
  seulement en l'absence d'oracle déterministe, et le fil principal
  revérifie encore un fait décisif. Le contrôle lit l'état. Il ne le
  réécrit pas avant la note.

## Multi-agents

Qui écrit, le brief et le plafond d'une vague sont déjà fixés : section
Multi-agents d'AGENTS.md, puce OS de `~/.agents/regles/bas-niveau.md`,
sources dans `~/.agents/docs/justifications/multi-agents.md`. Ici, ce que
ça change pour les tests.

- L'oracle est l'état final lu par une commande fraîche du fil principal :
  code de sortie, fichier, invariant. Le rapport d'un sous-agent se
  revérifie par cette commande, y compris s'il annonce que les tests
  passent.
- La suite et les critères d'acceptation se tiennent tous les deux. La
  suite couvre les assertions. Les critères couvrent le risque produit
  (geste ISTQB sur la mauvaise cible, plus haut).
- La base de test est le brief ou la spec écrits avant le départ des
  agents. Les cas en sortent. La suite du fil principal tient ce contrat,
  même pour un sous-agent qui n'a pas chargé les règles.
- Un seul écrivain par défaut. Quand l'auteur ordonne plusieurs écrivains,
  la suite se lance sur l'arbre une fois la vague intégrée. Ce qu'un
  écrivain peut modifier dans les tests est écrit dans
  `~/.agents/regles/bas-niveau.md`.
- La relecture à contexte vierge, réservée au risque élevé, compte comme
  test statique. La suite reste à lancer.
- La prose d'un agent se juge par des propriétés et des relations (section
  IA). Un passage intermittent est un incident.
- On n'ajoute ni harnais d'évaluation à cas dorés, ni annotateur de
  traces, ni hook, ni second skill.

## Ce qu'on ne reprend pas

- Documents séparés, signatures, rôles de test manager, processus
  organisationnel lourd : pour un dev seul, conformité adaptée.
- La couverture comme objectif en soi. Le plancher (au moins 90 % sur
  chaque couverture rapportée) est un critère de fin. Le dépasser en
  vidant les oracles ou en excluant du code ne compte pas.
- La norme a été contestée : pétition « Stop 29119 » lancée en août 2014
  par l'ISST après l'exposé de James Christie à CAST 2014 (absence de
  consensus, documentation lourde, test exploratoire mis de côté). Elle
  ne remplace pas le jugement. Sur une feature à risque, une courte session
  exploratoire (but, durée, notes) complète les cas écrits, et chaque bug
  trouvé devient un test.

## Références

- ISO/IEC/IEEE 29119-1 à -5, ISO/IEC TR 29119-6, -11 et -13 : sommaires
  et aperçus sur iso.org et l'Online Browsing Platform ;
  softwaretestingstandard.org ; Stuart Reid, « Test Design using Test
  Models » (janvier 2026) et « Risk-Based Testing for AI » (novembre 2024).
- ISTQB, Certified Tester Foundation Level Syllabus v4.0.1 (2024-09-15),
  istqb.org. On s'en sert pour les principes et les gestes, pas pour en
  copier le texte.
- ISO/IEC 25010 (modèle de qualité), ISO/IEC 20246 (revues).
- GCC, « Instrumentation Options » (`-fcondition-coverage`) et `gcov -g` ;
  Clang, « Source-based Code Coverage » (MC/DC).
- Cemri et al., « Why Do Multi-Agent LLM Systems Fail? »,
  arXiv:2503.13657, NeurIPS 2025. On en tire la vérification à deux
  niveaux. Les chiffres sont dans
  `~/.agents/docs/justifications/multi-agents.md`.
- Chen, « When Agent Evaluation Becomes Unreliable », arXiv:2610.16067,
  déposé le 2026-10-12, pas relu par des pairs. Un oracle qui réécrit
  l'état avant la note fausse le score. D'où la lecture seule du contrôle.
- Propriété et différentiel : sources et rejets dans
  `~/.agents/docs/justifications/verification-par-la-preuve.md`.
- Ordre de l'oracle : Barr et al., IEEE TSE 2015, et la suite dans
  `~/.agents/docs/justifications/ordre-oracle.md`.
