# Stratégies de branches (référence)

Charger ce fichier quand l'auteur demande Git flow, GitHub flow, trunk-based,
une branche de release ou de hotfix, ou quand un projet a déjà une stratégie
de branches à respecter.

Le `SKILL.md` reste la règle du quotidien : un commit par feature validée, push et PR sur ordre, messages courts,
pas de Git flow inventé sur un dépôt qui travaille sur `main`.

Sources lues le 2026-10-02 : Vincent Driessen « A successful Git branching
model » (nvie.com, avec sa note de 2020), GitHub Docs « GitHub flow »,
trunkbaseddevelopment.com, Martin Fowler « Patterns for Managing Source Code
Branches », DORA (trunk-based development).

## Les trois modèles

| Modèle | Branches permanentes | Durée d'une branche de travail | Fait pour |
|--------|----------------------|--------------------------------|-----------|
| Trunk-based | `main` seule | Heures, un jour au plus, ou commit direct sur `main` en solo | Livraison continue, web, projet solo ou petite équipe avec CI |
| GitHub flow | `main` seule | Quelques jours, fermée par une PR | Petite équipe, revue par PR, déploiement depuis `main` |
| Git flow | `main` et `develop` | Semaines, plus `release-*` et `hotfix-*` | Logiciel versionné, plusieurs versions maintenues en parallèle, releases planifiées |

Driessen lui-même, en 2020 : Git flow est « inutilement complexe » pour une
application web livrée en continu ; il renvoie vers GitHub flow. DORA mesure
que des branches courtes et une fusion quotidienne sur `main` prédisent la
performance de livraison. Fowler : « si ça fait mal, fais-le plus souvent » ;
intégrer petit et souvent coûte moins que fusionner gros et rarement.

## Règle ici

- Par défaut : **trunk-based**. `main` toujours vert, branche courte si une
  revue ou une CI en a besoin, fusion le jour même, branche supprimée après.
- Projet avec PR et relecteur (binôme, équipe, école) : **GitHub flow**, une
  branche par incrément, nommée par ce qu'elle fait, une PR, fusion, suppression.
- **Git flow seulement si** le dépôt l'utilise déjà (présence de `develop`,
  de tags de release, d'un `release-*` dans l'historique) ou si le brief
  demande un logiciel versionné avec maintenance de plusieurs versions. Ne
  jamais l'installer sur un dépôt qui travaille sur `main`.
- Dans tous les cas : jamais de gel de code, jamais de branche d'environnement
  (`staging`, `prod`) : la configuration par environnement se gère par la
  config, pas par des branches (Fowler, pattern déconseillé).
- Un seul incrément ouvert à la fois (`pratiques-agiles`), donc une seule
  branche de travail à la fois.

## Trunk-based en pratique

- Solo : commit directement sur `main` quand les tests passent ; sinon
  branche de quelques heures.
- Équipe : branche courte, PR, revue rapide (synchrone si possible), fusion
  quotidienne. Trois branches actives au plus dans le dépôt.
- Fonctionnalité qui dure plus d'un jour : découper, ou fusionner derrière un
  feature flag, ou passer par branch by abstraction (la nouvelle
  implémentation grandit à côté de l'ancienne derrière une interface, puis on
  bascule).
- Release : tag sur `main` (`v1.2.0`). Branche de release seulement si une
  version doit être stabilisée pendant que `main` continue ; elle ne reçoit
  que des correctifs, cherry-pick depuis `main`, et meurt après la release.
- Correctif urgent : fix forward sur `main`, tag, déploiement. Hotfix branch
  seulement si une branche de release vit encore.

## GitHub flow en pratique

1. Branche depuis `main`, nom descriptif (`connexion-par-email`, pas
   `feature/JIRA-123` sauf convention du projet).
2. Commits petits, une idée chacun, messages selon `SKILL.md`.
3. PR sur ordre, titre et corps en français, résumé et comment tester.
4. Les retours de revue se traitent par de nouveaux commits sur la branche.
5. Fusion quand la CI est verte et la revue faite ; déploiement depuis `main`.
6. Branche supprimée après fusion.

## Git flow en pratique (si, et seulement si, il s'applique)

- `main` : chaque commit est une version livrée, taguée.
- `develop` : intégration de la prochaine version.
- `feature/*` : part de `develop`, revient dans `develop` par `merge --no-ff`
  (on garde la trace de la branche).
- `release-x.y.z` : part de `develop` quand le périmètre est figé ; seulement
  numéro de version et correctifs ; fusion dans `main` (tag `vx.y.z`) puis
  retour dans `develop`.
- `hotfix-x.y.z` : part de `main`, corrige, fusion dans `main` (tag) puis dans
  `develop` ou dans la release en cours.
- Versions : semver (`MAJEUR.MINEUR.CORRECTIF`), tag annoté avec un message
  court.
- Interdit même en Git flow : branche de feature qui vit des semaines sans
  rebase ni fusion de `develop`, gel de `develop` avant une release, release
  branch qui reçoit des fonctionnalités.

## Choisir (Fowler)

Avant de choisir, répondre à : combien de versions on maintient en parallèle ?
à quelle fréquence on déploie ? la CI est-elle fiable en moins de dix minutes ?
Plus on déploie souvent et moins on maintient de versions, plus on va vers
trunk-based. Le modèle se choisit pour le projet, pas pour « faire pro ».

## Rationalisations à rejeter

| Excuse | Réalité |
|--------|---------|
| « Git flow, c'est la best practice » | Son auteur dit le contraire pour le web. Trunk-based ou GitHub flow par défaut. |
| « Une branche `develop` pour être propre » | Deux branches permanentes doublent les fusions sans rien livrer de plus. `main` vert suffit. |
| « Je garde ma branche jusqu'à ce que tout soit fini » | Au-delà d'un jour, les conflits grossissent. Découper ou flag. |
| « Une branche `staging` et une branche `prod` » | Branche d'environnement : config dérive, fusions à sens unique. Configuration par environnement, un seul code. |
| « Un hotfix direct en prod, on reportera sur `main` » | Le correctif disparaît à la prochaine release. Fix sur `main` ou hotfix fusionné partout, tout de suite. |

## Drapeaux rouges - STOP

- Tu crées `develop` ou `release-*` sur un dépôt qui ne les a pas
- Une branche de travail a plus d'un jour et grossit encore
- Plus de trois branches actives, ou plus d'une par personne
- Une branche porte un nom d'environnement
- Un tag de version posé à la main sans passer par `main`

→ Revenir à `main`, découper, fusionner, taguer depuis `main`. Puis seulement
livrer.
