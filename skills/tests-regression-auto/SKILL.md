---
name: tests-regression-auto
description: >-
  Après une feature : intégration et régressions, correction si KO, validation si OK, commit, automatisation. Use after a new feature or behavior change, before calling the work done.
---

# Régression automatique

## Invariant

**PERMANENT jusqu'à nouvel ordre explicite de l'auteur.**

Après chaque feature : lancer les tests d'intégration du comportement touché et la suite de régression, lire la sortie fraîche. Rouge : corriger et relancer les deux. La validation ne commence que si les deux sont verts et le check sécu est OK. Après le commit : automatisation maximale, une passe.

Violer la lettre, c'est violer l'esprit.

**REQUIRED:** lancement → `tests-locaux` (tout dans le projet, ni sandbox ni fichier temporaire). Sécu → `norme-cybersecurite`.

## Quoi lancer

| Contexte | Suite |
|----------|--------|
| Projet avec une suite | les cas d'intégration du comportement touché, puis la suite de régression, dans le projet. Une seule commande compte pour les deux quand elle lance ces cas et la suite déjà là |
| Pas de suite, et le brief n'en demande pas | le check manuel du comportement branché sur ses voisins, dit comme tel, puis le check de ce qui existait déjà |

Un test d'intégration fait passer la feature par ses vrais voisins (appelant, fichier, API, binaire, parcours). Le comportement jugé n'est pas mocké. La régression, c'est la suite déjà là, relancée entière. Les cas d'intégration du comportement nouveau sont dans le projet avant le lancement. S'ils manquent, on les écrit, puis on lance.

Le Stop ne lance que la première commande reconnue : npm test, manage.py test, composer test, pytest, cargo test, go test, ctest, puis make test-rapide, test ou check. L'intégration portée par une autre commande reste à lancer. Une collecte pytest vide est un KO, pas une absence de lanceur.

Pas de test qui parcourt le vrai home. Pas de perf, sauf ordre explicite.

## Boucle

1. Feature écrite, critères de fin écrits (`iso-29119`).
2. Tests d'intégration et régressions, dans le projet. Le rapport d'un
   sous-agent se revérifie ici : la sortie de cette commande est la preuve.
   Détail : `iso-29119`.
3. KO : c'est un incident. Noter attendu, obtenu, étapes et gravité.
   Confirmation : le test du défaut s'écrit avant le correctif, il échoue,
   puis il passe. On relance intégration et régressions. Un défaut amène
   un cas voisin. Un cas intermittent est un incident, pas une relance
   jusqu'au vert. Détail : `iso-29119`.
4. `cyber-scan.sh` sur les fichiers touchés.
5. OK (intégration verte, régressions vertes, sécu OK, critères de fin
   tenus, au moins 90 % sur chaque couverture rapportée) : validation (`revue-validation`,
   diff lu, parcours exécuté). Un KO pendant la validation revient à
   l'étape 3. Là seulement, dire que c'est bon.
6. Commit local de la feature, sans attendre de demande (règle immuable
   d'AGENTS.md), une fois la validation sans bloquant : fichiers stagés
   un par un, tests de régression inclus, message court qui note
   « régressions ok ». Push et PR restent sur ordre.
7. Automatisation maximale, après le commit. Une passe. Les contrôles
   de cette feature encore faits à la main, et qui peuvent devenir un
   cas stable, entrent dans la suite du projet. Le risque élevé d'abord.
   On les lance avec la commande déjà là. Pas de nouveau harnais, pas
   de hook, pas de pipeline, pas de push. Ce qui ne peut pas s'automatiser
   est nommé. Cette passe n'ouvre pas de tâche de fond ni de worktree.
   Un contrôle qui revient entre dans la suite, et ce cas se relance
   sans question. S'il n'y a rien à ajouter, on le dit en une ligne.
   Une horloge, un gateway ou une livraison vers un chat attend une
   demande explicite : rien ne s'arme en silence, et un cas de suite
   n'en crée pas un autre.
   Si la passe change des fichiers : retour à l'étape 2, puis
   validation, puis un commit, et on s'arrête.

Une sortie ancienne ne compte pas.

## Désactivation

Uniquement si l'auteur dit « arrête les tests de régression », « plus de régression auto », « excepte ce projet des régressions », ou si `~/.agents/hooks/disable-tests-regression-auto` existe.

## Rationalisations à rejeter

| Excuse | Réalité |
|--------|---------|
| « La feature est petite » | La suite part quand même |
| « Un test était déjà rouge » | On corrige le code jusqu'au vert |
| « La sécu, au prochain tour » | Livraison bloquée tant que le scan est rouge |
| « Le contrôle à la main a suffi » | Après le commit, il entre dans la suite s'il peut être un cas stable |
| « Le nouveau test est vert » | Écrit ou assoupli avec le code, il doit encore tomber sur une version fausse |
| « Ça ne plante pas, donc c'est bon » | L'absence de plantage laisse le critère ouvert |

## Drapeaux rouges. STOP

- Dire « les tests passent » sans sortie de cette session
- Prendre pour preuve le vert annoncé par un sous-agent
- Laisser un test rouge pour livrer plus vite
- Passer à la validation ou au commit tant qu'un test d'intégration ou de régression est rouge
- Dire la feature validée sans avoir exécuté le parcours
- Livrer un test qui reste vert quand le comportement est faux
- Prendre un Stop vert pour la validation, le commit ou l'automatisation
- Committer une feature sans suite verte de cette session, ou finir une feature validée sans la committer
- Finir au commit en laissant à la main un contrôle que la suite du projet peut lancer
- Lancer la suite sur le home réel
