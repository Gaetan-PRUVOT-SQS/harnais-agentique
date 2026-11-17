---
name: justifier-choix-techniques
description: >-
  Use when shipping a new feature (docs/justifications/<slug>.md, kept local). Triggers: justification, choix technique, ADR, soutenance.
---

# Justifier les choix techniques (PERMANENT)

## Invariant

**PERMANENT jusqu'à nouvel ordre explicite de l'auteur.**

Toute feature ou tout code livré doit pouvoir justifier **chaque ligne**,
**chaque choix**, et **l'impact métier**.

Violer la lettre, c'est violer l'esprit.

Même force que la règle du français d'AGENTS.md.

## Objectif

Un lecteur (jury, l'auteur, agent futur) ouvre `docs/justifications/` et sait :
pourquoi ce code existe, ce qu'on a fait, quel choix, quelle alternative
rejetée, quel impact métier.

Chaque ligne se rattache à un choix documenté. Sinon : documenter, ou
supprimer la ligne. La lecture comprise, nécessaire et vivante est
`revue-minutieuse`. Un commentaire par ligne ne remplace ni le mapping
ni cette lecture.

## Gate

| Travail | Doc |
|---------|-----|
| Feature / composant / comportement nouveau | Fichier **avant** le code. Pas « fait » tant que le fichier + le mapping ne sont pas à jour |
| Choix non trivial (lib, structure, algo, CSS, state) | Bloc Choix dans le fichier de la feature |
| Typo, indent, rename mécanique, fix 1 caractère | Pas de fichier |
| Refactor qui change un choix | Mettre à jour le fichier **dans le même tour** |

Ordre : **doc → code → mapping**. Pas l'inverse.

## Où

Projet : `docs/justifications/<slug-feature>.md`

**REQUIRED:** copier `references/modele.md` du skill.

Pas dans le code : pas de commentaires, ou très minimalistes (règle permanente d'AGENTS.md).
Pas dans le chat. Pas un stub TODO.

## Minimum dans le fichier

1. **Métier** : besoin, qui, impact si absent
2. **Ce qu'on fait** : comportement, fichiers
3. **Choix** : choix / pourquoi / alternative rejetée / impact métier
4. **Traçabilité** : fichier + symbole → section du doc
5. **Tests** : risques, modèles de test reliés aux cas, techniques,
   couverture visée (au moins 90 % sur chaque couverture rapportée), critères de fin, puis résultat (`iso-29119`,
   `modeles/section-tests.md`). Proportionné au risque : trois lignes
   pour un risque faible.

## Interdit

- Dire « c'est fait » / committer une feature sans le fichier
- Céder à « on documente après » ou « je l'explique à la soutenance » sans demande claire de l'auteur
- Commenter chaque ligne à la place du markdown
- Spec SOLID / scalable / design system sans besoin actuel (YAGNI)
- Mention d'assistant ou d'IA dans les fichiers du repo (règle d'AGENTS.md)

## Désactivation

**Uniquement** si l'auteur dit : « arrête de documenter les choix », « plus de justifications », « excepte ce projet des justifications ». Une demande explicite du tour en cours prime (AGENTS.md) ; seules les formulations vagues ci-dessous ne désactivent pas.

« on documente après » (report vague) ≠ désactivation. « pas de doc pour cette feature » est une demande explicite : la respecter et le signaler une fois.

## Rationalisations à rejeter

| Excuse | Réalité |
|--------|---------|
| « On documente après / vite juste le code » | Feature pas faite. Doc avant « c'est fait » |
| « L'utilisateur a dit skip the docs » | Respecté pour cette feature, le signaler une fois |
| « Paperasse, un lecteur compétent voit le code » | Le but est métier + alternatives, pas relire le JS |
| « Trois commentaires suffisent » | Un commentaire ne porte ni alternative ni impact métier |
| « Résumé dans le chat » | Le chat disparaît. Le repo garde le markdown |
| « Stub TODO, on remplira demain » | Un TODO n'est pas une justification |
| « Démo / dîner / fenêtre de deploy » | Code sans trace = pas livrable |
| « Commenter chaque ligne = justifier chaque ligne » | Bruit. Mapping fichier → doc |
| « Typo donc gros document » | Typo = pas de fichier |
| « Le code existe déjà, trop tard pour la doc » | N'autorise pas le ship. Écrire le fichier maintenant, mapper, ou supprimer |

## Drapeaux rouges : STOP

- Tu vas dire « c'est fait » sans `docs/justifications/<slug>.md` pour une feature
- Une ligne ajoutée ne se rattache à aucun choix du doc
- Tu as commenté chaque ligne au lieu d'écrire le markdown
- Tu as sauté la doc sans demande explicite de l'auteur

→ Écrire ou mettre à jour le fichier, ou retirer le code injustifié. Puis seulement livrer.
