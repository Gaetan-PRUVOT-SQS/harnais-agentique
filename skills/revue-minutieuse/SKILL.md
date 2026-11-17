---
name: revue-minutieuse
description: >-
  Revue ligne à ligne, aussi avant d'écrire : chaque ligne du changement est
  comprise, exigée par un critère ou un invariant, et atteinte. Aucun code mort.
  Use when writing, generating or reviewing code, hunting unused or speculative
  code, or running /revue-minutieuse. Triggers: revue minutieuse, code mort,
  justifier chaque ligne, avant de générer.
---

# Revue minutieuse

**PERMANENT.** Tout code écrit ou relu. Chaque ligne du **changement** est
comprise, nécessaire, et atteinte. Un code mort dans ce diff est un bloquant.

Voisins, à ne pas recopier :

| Sujet | Skill |
|---|---|
| Défauts par accords, réfutation | `code-review` |
| Porte de livraison, reçu, parcours | `revue-validation`, `validation-gate` |
| Mapping symbole → choix de feature | `justifier-choix-techniques` |
| Hors brief, socle inutilisé | `pratiques-agiles` |
| Tics d'un diff généré | `anti-slop` (section Code généré) |
| Inutilisé que **ce** changement a créé | `general-engineering` |

Taxonomie : `references/taxonomie.md`. Outils : `references/outils.md`.

## Les trois questions

Pour chaque instruction, déclaration, import, branche et symbole **ajoutés ou
modifiés** :

1. **Compris** : on dit ce que la ligne fait, sans deviner. Un nom opaque, un
   enchaînement qu'on ne peut pas paraphraser, ou un appel dont l'API n'est pas
   vérifiée à la version installée : on s'arrête. Google, *Every Line* : on
   lit chaque ligne humaine assignée, on ne balaie pas un bloc en supposant
   qu'il va.
2. **Nécessaire** : on nomme le critère d'acceptation, l'invariant (chemin
   d'erreur, frontière de confiance, contrat d'un appelant déjà là, exigence
   du langage ou du compilateur) qui l'exige. Une phrase orale suffit. Le
   mapping fichier → choix reste dans `docs/justifications/`
   (`justifier-choix-techniques`). Pas un commentaire par ligne.
3. **Vivant** : un chemin d'exécution réel l'atteint, et son résultat est lu,
   testé, ou produit un effet observable. Calculé puis jeté, jamais appelé,
   condition impossible, `#if 0`, code commenté : mort.

Une question sans réponse : on n'écrit pas la ligne. En revue, c'est un
bloquant. On la retire, ou on la rattache à un critère écrit, puis on relit.

Raisons qui tiennent : le critère nommé, l'invariant nommé, le contrat déjà
là, l'exigence du compilateur ou du protocole.

Raisons qui ne tiennent pas : « pour plus tard », « plus complet », « au cas
où », « le patron a souvent une fabrique », « ça compile », « ça fait
symétrique », « on a déjà écrit le helper ».

## Avant d'écrire

Ordre fixe. On ne commence pas le code avant 1 et 2.

1. Critères d'acceptation écrits (`pratiques-agiles`).
2. Inventaire : fichiers et symboles prévus, **une** raison chacun, rattachée
   à un critère ou à un invariant. Un symbole sans raison sort de la liste.
3. On n'écrit que cet inventaire. Un helper, une couche, une option, un type
   ou un fichier qui n'y figure pas n'entre pas.
4. Après le diff : les trois questions sur chaque hunk, puis les outils de
   `references/outils.md` (compilateur et linter du projet d'abord).

La bonne réponse peut être plus petite, ou pas de code.

## En revue

Cadrage et gravité : `revue-validation`. Ici, seulement la lecture ligne à
ligne. Une revue demandée comme telle s'arrête au rapport. Pendant une
livraison, un bloquant de ce skill se corrige dans la même tranche.

Ordre :

1. Lire le critère, puis chaque hunk, chaque instruction. Technique
   page-by-page (ISO/IEC 20246, résumés publics, pas de numéro de clause) :
   on paraphrase le bloc avant de passer au suivant. Fagan : le lecteur dit
   ce que le texte fait. Si on ne peut pas, on ne valide pas, on clarifie ou
   on simplifie.
2. Les trois questions. Taxonomie du code mort. Odeurs d'agent ci-dessous.
3. Ensuite seulement `code-review` (accords, sécu, perf).

Fichiers générés, tables de données, renommages mécaniques : on scanne la
structure, on ne pretend pas une lecture instruction par instruction. Un
fichier humain dans le même diff reste lu au complet. Google : le contexte
du fichier entier, pas seulement le hunk.

Code mort **déjà** dans l'arbre, hors du changement : on le signale, on ne
l'efface pas dans le même commit (`general-engineering`). Code que **ce**
changement rend inutilisé : on le retire dans ce diff.

Un changement trop large pour être lu ainsi se découpe. `validation-gate`
vise autour de 400 lignes modifiées.

## Odeurs d'agent

À chercher dans tout diff produit par un modèle, en plus de la taxonomie :

- Helper, validateur, retry, formateur de date déjà présents dans le dépôt.
- Nouvelle couche (fabrique, interface, module utilitaire) pour un seul
  appelant.
- Import, paquet ou API qui n'existe pas à la version installée.
- Branche, option, paramètre ou type « pour plus tard ».
- Test qui reste vert si on casse le comportement (`iso-29119`).
- Fichiers séparés qui ne font que se renvoyer l'appel (modularité de
  façade).

Volume : plus le diff gonfle, plus la structure se dégrade. On coupe avant
d'expliquer.

## Verdict

Bloquant : une ligne du changement incomprise, sans raison nommée, ou morte
(toute classe de `references/taxonomie.md`) ; un debug laissé ; un code
commenté ; une API inventée.

Note : style déjà couvert par le formateur ; code mort préexistant hors du
diff.

Le formateur possède le style. Un écart de goût ne se commente pas.

## Compte rendu

```
Périmètre :
Lu : N hunks, fichiers…
Outils : commande, sortie (inutilisé / inatteignable)
Bloquants :
  fichier:ligne, classe, phrase de la question qui échoue
Notes :
Limites : ce qui n'a pas été lu, outil absent
```

Zéro bloquant dans le périmètre lu, ce n'est pas « sans défaut ». Les
défauts d'accords restent `code-review`.

## On s'arrête

- Balayer un bloc humain sans le paraphraser.
- Écrire un symbole absent de l'inventaire.
- Commenter du code au lieu de le retirer.
- Garder un inutilisé « pour ne pas jeter ».
- Dire justifié parce que ça compile ou que les tests passent.
- Ajouter du code seulement pour faire monter une couverture.

## Références

- Google eng-practices, CC-BY 3.0 : Every Line, Complexity / over-engineering
  <https://google.github.io/eng-practices/review/reviewer/looking-for.html>
- CWE-561 Dead Code <https://cwe.mitre.org/data/definitions/561.html>
- CERT MSC07-C, MSC56-J (code mort, valeurs inutilisées)
- MISRA C Rule 2.2 (opération sans effet) ; exception `(void)` pour un
  retour volontairement ignoré, encore explicable
- ISO/IEC 20246:2017, technique page-by-page. Résumés publics. Pas de
  numéro de clause
- Fagan, inspections : le lecteur paraphrase. Résumés publics
- Apple `goto fail` (CVE-2014-1266) : de l'inatteignable a sauté une
  vérification
- Holzmann, Power of Ten : portée minimale, retours vérifiés, compilateur
  à tous les avertissements. On n'importe pas les dix règles (tas, récursion)
