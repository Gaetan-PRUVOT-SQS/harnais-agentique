# DevOps agile (référence)

Charger ce fichier quand un projet a un pipeline, un déploiement, une prod ou
une exploitation à gérer, ou quand l'auteur demande du DevOps, du CI/CD, des
métriques DORA, un post-mortem ou de l'infra as code.

Le `SKILL.md` reste la règle du quotidien (un incrément, critères, DoD). Ici :
ce que la recherche DORA, Google SRE, Microsoft et AWS retiennent comme
pratiques qui marchent, ramené à l'échelle d'un étudiant ou d'un petit projet.

Sources lues le 2026-10-02 : dora.dev (catalogue des capacités, guides CI,
CD, trunk-based, small batches, pervasive security, test automation, four
keys), Martin Fowler (deployment pipeline, test pyramid), rapports
State of DevOps 2024 et 2025, Google SRE Book (post-mortems), Microsoft Learn
« What is DevOps », « Shift left » et « Safe deployment practices », AWS
« What is DevOps », Builders' Library « Automating safe, hands-off
deployments », Well-Architected DevOps Guidance (continuous delivery,
dynamic environment provisioning), guide de test AWS Lambda, IT Revolution
(Three Ways).

## Ce que DevOps ajoute à l'agile

L'agile découpe le travail en incréments ; DevOps fait en sorte que chaque
incrément arrive en prod sans douleur et qu'on apprenne de la prod. Les deux
se renforcent : un incrément qui ne se déploie pas n'est pas fini.

Les trois voies (Gene Kim, The DevOps Handbook) :

| Voie | Idée | Action agent |
|------|------|----------------|
| Flux | Optimiser le système entier, de l'idée au client, pas un silo | Pas de défaut poussé en aval : un test rouge ne passe pas « pour voir » |
| Feedback | Raccourcir et amplifier les boucles de retour | Pipeline qui répond en minutes, prod qui remonte ses erreurs |
| Apprentissage | Expérimenter, échouer sans blâme, répéter jusqu'à maîtrise | Post-mortem écrit après un incident, action concrète |

CALMS (Jez Humble) : Culture, Automatisation, Lean, Mesure, Partage. Les
outils seuls ne font pas de DevOps ; sans culture (responsabilité partagée,
pas de blâme) le pipeline devient du théâtre.

## Les cinq métriques DORA

Quatre clés historiques plus une ajoutée en 2025. Elles mesurent le débit et
la stabilité, qui montent ensemble chez les bonnes équipes (ce n'est pas un
compromis).

| Métrique | Définition | Élite | Haut | Moyen | Bas |
|----------|------------|-------|------|-------|-----|
| Fréquence de déploiement | Combien de fois on déploie en prod | À la demande, plusieurs par jour | Entre 1/jour et 1/semaine | Entre 1/semaine et 1/mois | Moins d'1/mois |
| Délai de changement | Du commit au déploiement en prod | Moins d'un jour | Entre 1 jour et 1 semaine | Entre 1 semaine et 1 mois | Plus d'un mois |
| Taux d'échec | Part des déploiements qui exigent une intervention immédiate (rollback, hotfix) | 5 % | 10 % | 15 % | 64 % |
| Temps de rétablissement | D'un déploiement raté au service rétabli | Moins d'une heure | Moins d'un jour | Entre 1 jour et 1 semaine | Plus d'une semaine |
| Taux de retravail (2025) | Part des déploiements non planifiés causés par un incident en prod | Le plus bas possible | | | |

Plus la fiabilité (le service tient ses objectifs) comme quasi-métrique.

Pour un projet solo, on ne monte pas un tableau de bord. On se pose les
questions : combien de temps entre « ça marche chez moi » et « c'est en
ligne » ? Que se passe-t-il si je déploie une erreur ? En combien de temps je
reviens en arrière ?

Les bandes du tableau ne sont pas un objectif. Le guide DORA
(https://dora.dev/guides/dora-metrics/, lu le 2026-10-30) range « fixer la
métrique comme but » parmi les pièges : exiger plusieurs déploiements par
jour pousse à truquer le chiffre. On s'en sert pour voir où ça coince, sur
une appli qui a une prod.

## Pratiques techniques (catalogue DORA)

### Petits lots

- Un changement dure des heures à deux jours, jamais plus d'une semaine.
- INVEST sur chaque tranche, comme dans `cadre.md`.
- Plusieurs petits changements livrables sur `main` par jour.
- Piège n° 1 : regrouper les lots avant de tester ou de déployer, ce qui
  retarde le retour.
- Piège n° 2 : un assistant IA qui génère une PR énorme. Découper quand même.

### Trunk-based development

- Branches de quelques heures, trois branches actives au plus, fusion sur
  `main` au moins une fois par jour.
- Zéro gel de code : un gel est incompatible avec l'intégration continue.
- Revue courte et proche du moment du code ; une revue asynchrone qui traîne
  pousse à grossir les lots.
- Tests automatisés lancés avant chaque commit sur `main`.
- Feature flags pour fusionner une fonctionnalité incomplète sans l'exposer ;
  retirer le flag une fois la fonctionnalité stable.
- Choix entre trunk-based, GitHub flow et Git flow : `pratiques-git-github`,
  `references/branches.md`.

### Intégration continue

- Build automatisé, numéroté, reproductible, qui produit un artefact
  déployable partout.
- Suite de tests fiable qui tourne en moins de dix minutes ; sinon on sépare
  rapide et lent (`test-rapide` dans le Makefile, comme le hook Stop le fait).
- Chaque commit déclenche build et tests ; le résultat est visible sans
  effort.
- Build cassé : on le répare avant tout autre travail.
- Tout ce qui sert à construire est dans le dépôt (scripts, config, lock).

### Livraison continue

- Le logiciel est déployable à tout moment ; c'est une priorité d'équipe.
- Déploiement automatisé, identique en test et en prod, sans étape manuelle
  qui dépend d'une personne.
- Courbe en J : accélérer un vieux process sans l'automatiser crée d'abord
  plus de tests manuels et de dette. Automatiser et simplifier ensemble.
- Déploiement sûr : rollout progressif, canary ou bleu-vert quand le service
  le justifie, et toujours un retour arrière connu et testé.

### Version control et infra as code

- Tout en version control : code, config, scripts de déploiement, schéma de
  base, définition de l'infra.
- Infra as code : déclaratif, revu, versionné, rejouable (Docker Compose,
  Terraform, Ansible selon le besoin). Pas de serveur configuré à la main
  « juste cette fois ».
- Dérive de configuration : la cible définie dans le dépôt fait foi ; on ne
  répare pas en prod sans reporter dans le code.
- Changements de base de données gérés comme du code : migrations
  versionnées, compatibles avec la version précédente le temps du déploiement.
- Le rapport DORA 2025 classe version control et petits lots parmi les sept
  capacités qui font que l'IA aide au lieu d'amplifier le désordre.

### Observabilité et alertes

- Logs, métriques, traces collectés avec un but : comprendre et déboguer la
  prod, pas accumuler.
- Alertes actionnables uniquement : chaque alerte a un seuil, un responsable,
  une action. Une alerte qu'on ignore se supprime.
- Notification proactive : on apprend l'incident par le système, pas par
  l'utilisateur.
- Les mesures de prod nourrissent les décisions produit (quelle feature est
  utilisée, laquelle plante).

### Sécurité intégrée

- La sécu entre à la conception, pas en revue finale (Deming : bâtir la
  qualité dedans plutôt que l'inspecter à la fin).
- Contrôles automatiques dans le pipeline : audit des dépendances, secrets
  scan, lint sécu. Ici : `norme-cybersecurite`, `sca-audit`,
  `secrets-scan`, `check-npm`.
- Bibliothèques et outils pré-approuvés plutôt que « chacun bricole ».
- Les équipes qui font ça passent beaucoup moins de temps à corriger des
  failles.

### Architecture et test

- Couplage faible : on peut tester et déployer un composant sans
  orchestrer tout le reste. Pas une licence pour des microservices sur un
  projet solo.
- Données de test gérées : jeux reproductibles, jamais des données
  personnelles de prod.
- Maintenabilité : code facile à trouver, réutiliser, changer ; documentation
  interne à jour. DORA 2024 : les équipes bien documentées sont plus fiables
  sur toutes les métriques.

## Tests automatisés avant déploiement

Sources : DORA (test automation), Martin Fowler (deployment pipeline, practical
test pyramid), Microsoft Learn (shift left, safe deployment practices).

Principe : un déploiement n'est jamais la première fois qu'on découvre un
problème. Le pipeline est une suite d'étapes qui vont du plus rapide au plus
lent ; chaque étape arrête tout si elle échoue, et l'artefact qui arrive en
prod est celui qui a passé toutes les étapes, construit une seule fois.

### Les étapes, du plus rapide au plus lent

| Étape | Quand | Contenu | Budget |
|-------|-------|---------|--------|
| Avant commit | Sur le poste | Formateur, linter, tests unitaires, hook pre-commit | Secondes |
| Commit stage | À chaque push, bloque la fusion | Build de l'artefact, lint, typage, tests unitaires et d'intégration étroite, analyse statique, scan des secrets et des dépendances | Moins de dix minutes |
| Acceptation | Sur l'artefact construit, après fusion | Déploiement dans un environnement jetable, smoke tests, tests d'acceptation (API, parcours), tests de contrat, migrations de base jouées | Dizaines de minutes |
| Pré-production | Même outil de déploiement que la prod | Smoke test de la config (bonne base, bonnes URL, secrets présents), santé du service, test de charge si le risque le justifie | Minutes à heures |
| Prod | Rollout progressif | Health check, smoke test post-déploiement, retour arrière automatique si le signal passe au rouge | Bake time avant d'élargir |

Règles :

- **Build once** : le même artefact (image, archive, binaire) traverse toutes
  les étapes. On ne reconstruit pas pour la prod.
- **Fail fast** : un échec arrête le pipeline ; personne ne pousse par-dessus
  un commit stage rouge.
- **Mêmes outils partout** : le script qui déploie en test déploie en prod.
  Une différence entre les deux est un bug caché.
- **Un seul signal de qualité** : quand le pipeline est vert, le logiciel est
  livrable. Un vert qui ne veut rien dire vaut moins qu'un rouge honnête.

### Pyramide et niveaux

- Beaucoup de tests unitaires (rapides, isolés), moins de tests
  d'intégration (un point d'intégration à la fois : base, API externe, fichier),
  très peu de tests bout en bout (lents, fragiles).
- Microsoft : L0 et L1 en mémoire (moins de 60 ms et 400 ms par test en
  moyenne, aucun au-delà de 2 s), L2 avec une dépendance réelle (SQL, fichier),
  L3 contre un service déployé, L4 en prod. L2 avant commit, L3 bloque la PR,
  L4 bloque le déploiement.
- Un test de haut niveau qui trouve un bug sans qu'un test de bas niveau
  échoue : écrire le test de bas niveau. Pousser chaque vérification au plus
  bas possible.
- Tests de contrat (consumer-driven) dès que deux services ou un front et un
  back évoluent séparément : c'est la première cause d'incident en prod sur
  des services découplés.
- Les tests unitaires sont écrits par les développeurs et vivent à côté du
  code (`tests-locaux`). Le code de test est du code produit : même revue,
  même qualité.

### Fiabilité

- Zéro test flaky toléré : un test qui échoue au hasard est réparé ou
  supprimé, jamais relancé « jusqu'à ce que ça passe ».
- Tests indépendants : état connu au départ, aucun ordre imposé, aucune
  dépendance à un service externe vivant (identité, horloge, réseau) sans
  doublure maîtrisée.
- Données de test reproductibles, jamais des données personnelles de prod.
- Chaque échec en pipeline est un incident au sens de `iso-29119` : attendu,
  obtenu, reproduction, test de régression avant correction.

### Ce qu'on vérifie avant de déployer, concrètement

1. L'artefact est celui que le commit stage a produit (hash, tag).
2. Les migrations de base passent sur une copie du schéma et restent
   compatibles avec la version précédente le temps du rollout.
3. Un smoke test lance le service et touche ses points d'entrée vitaux
   (santé, login, page principale) avec la config de la cible.
4. Les dépendances sont joignables depuis l'environnement cible (base,
   cache, API tierces) ; les secrets attendus sont présents sans être lus.
5. Le rollback est connu et a déjà été exécuté au moins une fois sur cet
   environnement.
6. Les scans sécurité du pipeline sont verts (`norme-cybersecurite`,
   `sca-audit`, `secrets-scan`).

Après déploiement : health check, smoke test post-déploiement, surveillance
des erreurs pendant le bake time (Microsoft : une journée complète incluant
un pic d'usage) avant d'élargir ; retour arrière automatique si le taux
d'erreur monte. Déployer en journée, tôt dans la semaine, quand on est là
pour réagir.

### Pipeline à la AWS (Builders' Library, Well-Architected DevOps Guidance)

Amazon pousse en prod sans intervention humaine après la revue de code.
Tout ce qui suit est automatisé, y compris la création et la destruction des
environnements de test.

| Étape | Ce qui s'y passe |
|-------|------------------|
| Source | Revue de code, dernier contrôle manuel : couverture de tests, instrumentation, mécanisme de rollback vérifiés par le relecteur |
| Build | Compilation, tests unitaires avec doublures, analyse statique, scans sécu, artefact signé ; on ne déploie que depuis un dépôt d'artefacts de confiance |
| Alpha, beta | Tests fonctionnels d'API et tests d'intégration bout en bout |
| Gamma | Environnement le plus proche possible de la prod : même config de déploiement, mêmes alarmes, mêmes canaris. C'est là qu'on vérifie que les alarmes sonnent juste, avant la prod |
| One-box | Le nouveau code sur une seule instance (ou un petit pourcentage d'invocations) à côté de l'ancien, 30 à 60 minutes, même load balancer ou même file : détecte un format de données que l'ancien code ne lit plus |
| Zeta | Tests d'intégration qui appellent les endpoints de prod des autres services : compatibilité arrière avec ce qui tourne vraiment |
| Prod | Vagues de taille croissante (régions calmes d'abord, une zone à la fois), bake time entre chaque vague, rollback automatique si l'alarme agrégée passe au rouge |

Règles qu'on en retient :

- **Fail-fast** : un test critique rouge arrête le pipeline à cette étape ;
  rien ne passe « en attendant ».
- **Environnements éphémères** : créés à la demande par le pipeline, détruits
  après les tests. Moins cher, toujours propre, pas de pollution d'une
  exécution à l'autre, parallélisable. Chaque pile a un nom unique (préfixe
  de branche ou de PR). Une alerte de coût est posée dès la création.
- **Compatibilité arrière** : le nouveau code doit coexister avec l'ancien
  le temps du rollout et du rollback. Tests one-box et zeta, migrations de
  base compatibles N-1, formats de données lisibles par les deux versions.
- **One-box d'abord** : jamais 100 % d'un coup. Une instance, puis on élargit
  si les métriques tiennent.
- **Observabilité dès la pré-prod** : alarmes, métriques et canaris identiques
  en gamma et en prod. Une alarme fausse en gamma est corrigée avant qu'elle
  bloque un déploiement de prod ; une alarme active bloque le déploiement.
- **Bake time avec assez de données** : on attend un nombre de points de
  mesure, pas seulement une durée.
- **Fenêtres** : pas de déploiement automatique pendant les périodes à risque.

### Serverless : trois techniques combinées (guide de test AWS Lambda)

- **Priorité au test dans le cloud** : seul moyen de vérifier les droits
  IAM, les quotas, la mémoire et le timeout de la fonction, les vraies
  signatures d'API. Chaque développeur a un environnement isolé (compte ou
  pile préfixée), déployé en infra as code, détruit ensuite.
- **Mocks** pour la logique métier isolée : rapides, bons pour simuler les
  pannes et les services tiers ; mais ce que les mocks couvrent doit aussi
  être couvert dans le cloud, et jamais de mock pour valider un appel de
  service.
- **Émulation locale** (SAM CLI, LocalStack) avec parcimonie : utile hors
  ligne, mais en retard sur les API, ne teste ni les droits ni les quotas.
- Structurer pour la testabilité : le handler est un adaptateur mince qui
  valide l'événement et appelle la logique métier testable sans Lambda.
- Les tests d'intégration priment : un appel HTTP synthétique sur l'API
  déployée vérifie le code, la config et les permissions entre services.

### Mesure (DORA)

- Part des tests écrits par les développeurs (cible : eux en premier).
- Bugs trouvés par étape dans le temps : de plus en plus tôt, de moins en
  moins cher.
- Part des échecs de pipeline qui correspondent à un vrai défaut (cible :
  tous).
- Temps passé à réparer des tests (doit baisser).
- Durée du commit stage (moins de dix minutes) et délai du vert à la prod.

### Version minimale solo

Un hook pre-commit (lint, tests rapides), un workflow CI à chaque push
(lint, typage, tests, build, scans), un `make test-rapide` sous dix minutes et
un `make test` complet, un script de déploiement qui finit par un smoke test
sur l'URL déployée et qui sait revenir au tag précédent. Pas de staging
dédié si une image Docker lancée dans le pipeline joue le même rôle.

## Pratiques de processus

- Visualiser le flux de l'idée à la prod et limiter le WIP (même règle que
  `SKILL.md` : un incrément ouvert).
- Approbation allégée : revue par les pairs plutôt que comité de changement.
  Les comités externes ralentissent sans réduire les échecs.
- Retour client intégré tôt et souvent.
- L'équipe choisit ses outils et peut expérimenter sans permission externe.

## Culture

- Culture générative (Westrum) : haute coopération, messagers formés plutôt
  que punis, responsabilités partagées, échec traité par l'enquête.
- Post-mortem sans blâme (Google SRE) après tout incident visible, toute
  perte de données, tout rollback. Contenu : chronologie, impact, causes,
  actions de correction priorisées. On part du principe que chacun a agi de
  bonne foi avec l'information qu'il avait ; on corrige le système, pas les
  gens.
- Apprentissage continu, temps réservé à l'amélioration, rythme soutenable.
- DORA 2024 : sécurité psychologique, autonomie et responsabilités claires
  prédisent la performance autant que la technique.

## Déclinaison pour un projet étudiant ou solo

| Pratique | Version minimale qui compte |
|----------|------------------------------|
| Petits lots | Un incrément démontrable par session, commit dès qu'il marche |
| Trunk-based | `main` toujours vert, branche courte si besoin, fusion le jour même |
| CI | Un workflow qui lance lint, tests, build à chaque push (`ci-cd-and-automation`, `github-actions-docs`) |
| Tests avant déploiement | Commit stage sous dix minutes, smoke test sur l'artefact déployé, rollback déjà exercé |
| Environnement de test | Un compose ou une pile lancée par le pipeline, détruite à la fin ; une seule instance avec le nouveau code avant d'élargir |
| CD | Un script de déploiement rejouable, un rollback connu (tag précédent, image précédente) |
| IaC | Dockerfile et compose dans le dépôt, zéro config manuelle sur le serveur |
| Observabilité | Logs structurés, une page de santé, une alerte quand le service tombe |
| Sécurité | Scans dans le pipeline, secrets hors dépôt, dépendances à jour |
| Mesure | Savoir répondre : délai commit-prod, dernier incident, temps de retour |
| Post-mortem | Trois lignes dans `docs/justifications/` après un incident : ce qui s'est passé, pourquoi, ce qui change |

Ne pas faire : Kubernetes pour un site statique, microservices pour un
binôme, tableau de bord DORA pour trois fichiers, SRE on-call imaginaire.
Même règle que l'agile : proportionné au problème, pas de théâtre.

## Rationalisations à rejeter

| Excuse | Réalité |
|--------|---------|
| « On automatisera le déploiement quand ce sera stable » | Le déploiement manuel est ce qui rend instable. Automatiser dès la première mise en ligne. |
| « Je gèle `main` avant la démo » | Un gel casse l'intégration continue. `main` reste vert en permanence, la démo se fait depuis un tag. |
| « La PR est grosse mais tout est lié » | Découper quand même : API d'abord, flag si l'UI n'est pas prête. |
| « Je corrige directement sur le serveur, c'est plus vite » | Dérive de configuration. Corriger dans le dépôt, redéployer. |
| « Pas besoin de rollback, ça marchera » | Le taux d'échec élite est 5 %, pas 0. Rollback testé avant le premier déploiement. |
| « La sécu, on verra en fin de projet » | Dix fois plus cher à la fin. Scans dans le pipeline dès le premier commit. |
| « Le test est flaky, je relance » | Un test au hasard ne prouve rien. Réparer ou supprimer, jamais relancer pour avoir le vert. |
| « Un environnement de test permanent, c'est plus simple » | Il dérive et se pollue. Créé par le pipeline, détruit après, nom unique par branche. |
| « Ça passe en local, je déploie direct » | Le pipeline existe pour ça. Pas de déploiement sans commit stage vert sur l'artefact construit. |
| « L'incident est réglé, pas besoin d'écrire » | Sans post-mortem, le même incident revient. Trois lignes suffisent. |
| « L'IA génère le code, ça va plus vite » | DORA 2025 : plus vite seulement si petits lots et version control tiennent, sinon plus d'incidents. |

## Drapeaux rouges - STOP

- Un déploiement qui dépend d'une suite de commandes tapées à la main
- `main` rouge depuis plus d'une heure et on continue autre chose
- Une branche qui a plus d'une journée
- Un secret, un mot de passe ou une config de prod dans le dépôt
- Aucun moyen connu de revenir à la version précédente
- Une alerte ignorée « parce qu'elle sonne tout le temps »
- Un test relancé jusqu'au vert, ou un déploiement lancé depuis un poste sans passer par le pipeline
- Un incident clos sans une ligne écrite

→ Automatiser, réparer `main`, découper, sortir le secret, écrire le rollback.
Puis seulement livrer.
