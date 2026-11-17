---
name: revue-validation
description: >-
  Revue du diff, reçu de preuve et validation du parcours. Use when reviewing code, or before calling a feature done.
---

# Revue et validation

Deux questions, les deux exigées avant de dire une feature finie.

La vérification demande une preuve que les exigences spécifiées sont tenues. La validation demande une preuve que l'usage prévu l'est aussi. Les deux phrases viennent du glossaire ISTQB (verification v1, validation v1, glossary.istqb.org), lui-même aligné sur l'ISO 9000. Lire le diff ne valide pas. Une suite verte qui n'exerce pas le parcours non plus.

Ordre du pipeline : on crée la feature, on lance les tests d'intégration et les régressions, un KO part en correction, et la validation ne commence qu'une fois ces tests verts et le contrôle de sécurité OK. Un bloquant trouvé à la validation retourne à la correction, puis les tests repartent. Après la validation : le commit, puis l'automatisation maximale.

Voisins, à ne pas recopier : `code-review` (moteur de défauts), `revue-minutieuse` (ligne à ligne, code mort), `iso-29119` (techniques, oracles, incidents), `tests-regression-auto` (lancer la suite), `tests-locaux` (où lancer), `norme-cybersecurite` (baseline et flux), `pratiques-agiles` (une tranche, critères).

## Ce qu'on fait ici

Revue technique du diff, pas une inspection avec rôles, réunion et métriques. L'ISO/IEC 20246:2017 décrit ce cadre (le texte est payant, on n'en cite pas les clauses). On en garde cinq activités : cadrer, lire chaque ligne, rapporter les écarts avec une preuve, corriger les bloquants, dire ce qui reste.

Le lecteur par défaut est le fil principal. Risque élevé (sécu, auth, mémoire C, noyau) : un sous-agent qui ne fait que lire, brief d'AGENTS.md, puis le fil revérifie les lignes citées. Pas de fan-out, pas de second modèle. `code-review` en parle : on ne le fait pas.

Une revue demandée comme telle s'arrête au rapport. Pendant la livraison d'une feature, un bloquant se corrige dans la même tranche, puis on relit le correctif.

## Cadrage

Avant de lire le code, écrire trois lignes :

- Périmètre : les fichiers du changement, plus les appelants et les tests de ce comportement.
- Base : critères d'acceptation, brief, spec. À défaut, le comportement observable déjà là (`git log`, tests existants).
- Usage prévu : le parcours que quelqu'un va vraiment faire.

Hors de ce périmètre : on le signale, on n'y touche pas dans le même commit.

## Revue

Ordre : le critère et le cœur du changement, puis le reste, chaque fichier du diff, tests compris. Le formateur possède le style. Un écart de goût ne se commente pas.

Chaque ligne du diff est lue : comprise, nécessaire, vivante (`revue-minutieuse`). Le code mort dans le changement est un bloquant.

On cherche, dans cet ordre :

1. Le changement fait ce que le critère dit, et rien d'autre.
2. Les chemins d'échec, les limites, l'état laissé si ça casse au milieu.
3. Les tests échoueraient si le comportement revenait en arrière. L'oracle vient de la base, pas du code qu'on vient d'écrire (`iso-29119`).
4. Un accord entre deux bouts (appelant et appelé, écriture puis lecture, deux effets qui doivent rester d'accord). Le détail des accords, de la réfutation et du rapport long est dans `code-review`. On ne le recopie pas. Une suspicion sans exécution atteignable n'est pas un défaut.
5. Le flux touché, côté confiance : `norme-cybersecurite`. La grille source, frontière, puits est dans `code-review/references/security-review.md`.
6. La perf seulement sur un chemin chaud, ou sur demande. Il faut une charge atteignable et une conséquence. `code-review/references/performance-review.md`.

Les commandes `/security-audit-static`, `/performance-audit-static`, `/ship-check` et `/pm-ai-shipping` ne sont pas installées. On ne les lance pas.

Un défaut se garde seulement s'il a : l'attendu et d'où il sort, une exécution possible, l'endroit (`fichier:ligne`, les deux bouts si la frontière est en cause), une conséquence observable, et le mécanisme qui aurait pu l'empêcher déjà vérifié.

Gravité :

- Bloquant : mauvais comportement, trou de sécu, donnée perdue ou corrompue, test qui ne peut pas échouer sur le critère.
- Note : le reste. Ça ne retient pas la livraison. On ne corrige pas une note dans la foulée.

Le changement peut partir s'il améliore le code et qu'aucun bloquant n'est ouvert. On ne le retient pas pour le polir. Les faits l'emportent sur une préférence. Le style, c'est le guide du dépôt.

Dire aussi ce qui tient. Un rapport qui n'accuse pas tout est lisible.

## Validation

Chaque critère a un nom : un cas de test, ou un contrôle exécuté à la main et dit comme tel. Un critère sans les deux n'est pas validé.

Vérification, preuves à avoir :

- diff lu, y compris les tests ;
- analyse statique du langage (le skill du langage dit l'outil) ;
- tests d'intégration du comportement et suite de régression verts, sortie de cette session (`tests-regression-auto`) ;
- `cyber-scan.sh` vert sur les fichiers touchés ;
- aucun bloquant ouvert.

Validation, en plus : exécuter le parcours d'usage et comparer à l'oracle. Un test qui mock le comportement jugé ne compte pas pour ce parcours. Une UI se valide dans le navigateur, geste par geste. Un noyau ou un shell se valide par le harnais du projet, pas par une lecture du C.

Dire dans le compte rendu ce qui a été exécuté et ce qui a seulement été lu. Ce qui n'a pas tourné n'est pas validé. Le risque résiduel se dit (`iso-29119`).

## Reçu

Avant de dire la feature finie, le compte rendu tient un reçu par critère.

- Critère : état de départ, action, résultat observable.
- Oracle : la base de test d'abord, quand elle donne le résultat. Propriété ou ancien système en plus, ou à la place si la base ne donne pas la valeur. La sortie du code nouveau, recopiée dans le test, ne compte pas. Un instantané écrit dans le même changement non plus.
- Source : commande fraîche, état observé, ou `fichier:ligne`, relue par le fil qui décide.

Le récit d'un agent ne prouve rien. Une lecture, un plan ou un résumé n'est pas une vérification. Seul l'état du système tranche. Pas de second agent pour ce reçu : le fil principal le tient. Le sous-agent du risque élevé reste celui d'AGENTS.md. Un contrôle déterministe tranche avant un juge qui est un modèle.

Un test ajouté ou assoupli dans le même changement est un bloquant s'il reste vert sur une implémentation fausse. Le cas du défaut avant le correctif, ou une mutation minimale, sert de preuve. L'ordre des sources est dans `iso-29119`. Un test qui se contente de l'absence de plantage laisse le critère ouvert : on le dit.

## On s'arrête

- « C'est bon » sans avoir lu le diff.
- « Les tests passent » comme seule validation.
- Annoncer fini à partir d'un récit, même le sien.
- Garder un test qui reste vert quand le comportement est faux.
- Corriger une note, ou un fichier hors du changement, dans le même commit.
- Prendre le « c'est bon » d'un sous-agent sans relire les lignes qu'il cite.
- Annoncer le code sans défaut. Zéro bloquant dans le périmètre lu, c'est tout.

## Références

- Google, eng-practices, CC-BY 3.0 : <https://google.github.io/eng-practices/review/reviewer/standard.html>, <https://google.github.io/eng-practices/review/reviewer/looking-for.html>, <https://google.github.io/eng-practices/review/reviewer/navigate.html>. On en garde : améliorer le code plutôt que viser le parfait, les faits plutôt que le goût, le cœur du changement d'abord, les tests dans le même changement.
- ISO/IEC 20246:2017, revues de produits de travail. Résumés publics seulement. Pas de numéro de clause.
- ISTQB Glossary, verification v1 et validation v1 : <https://glossary.istqb.org/>.
- Reçu : Sanayei et al., arXiv:2610.17724, déposé le 2026-10-13, pas relu par des pairs. On garde le reçu et le refus du récit. On n'installe pas Sauron. Le reste des sources est dans `~/.agents/docs/justifications/verification-par-la-preuve.md`.
