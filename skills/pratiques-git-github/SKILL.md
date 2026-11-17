---
name: pratiques-git-github
description: >-
  Use whenever committing, pushing, branching, tagging, or opening a PR/issue. Goal: short, human commit messages and zero AI fingerprint in git log or GitHub.
---

# Pratiques Git / GitHub (PERMANENT)

## Invariant

**PERMANENT jusqu'à nouvel ordre explicite de l'auteur.**

Deux buts, inséparables :

1. **Traçable** : `git log` raconte le projet (une idée par commit, FR, une ligne claire).
2. **Humain** : **personne**, y compris l'auteur, ne doit voir qu'un assistant a participé. `git log`, GitHub, graphe : zéro trace, même en solo.

Violer la lettre, c'est violer l'esprit.

Commit d'une feature validée : **automatique** (règle immuable d'AGENTS.md). Les tests d'intégration et les régressions sont verts, le contrôle sécu est OK, la validation du parcours est faite. L'automatisation maximale vient après ce commit. Push et PR seulement **sur ordre**.

Zéro attribution d'outil et messages en français : règles permanentes d'AGENTS.md, déjà en contexte.
Feature nouvelle : `docs/justifications/` écrit en local (jamais poussé) avant de la dire faite → `justifier-choix-techniques`.

## Ce que voit un lecteur (GitHub, `git log`, graphe)

Il doit voir : L'auteur du compte (dépôt public : le nom de la règle d'identité et l'adresse de l'auteur dans l'en-tête, voir Identité), messages FR courts et naturels, un changement par commit.

Personne, **même l'auteur**, ne doit y voir : `Co-Authored-By`, « Generated with », nom d'outil, `noreply@anthropic.com` ou autre adresse d'outil, `feat(ui):`, anglais trop lissé, emoji robot, « AI », « assistant », « copilote » dans le message / la PR / le README.

Avant un **push** : `git log -5 --format=fuller` : si un trailer ou un mot interdit apparaît, **ne pas pusher**. Corriger (amend seulement si le commit n'est pas déjà sur le remote).

## Avant tout commit

1. `git status` + `git diff` + `git log -5`
2. Staging **fichier par fichier** : jamais `git add -A` / `git add .`
3. Exclure secrets, dumps, hors-sujet
4. Un commit = **une idée**
5. Message FR court ; s'il fait plusieurs lignes, via fichier ou **HEREDOC**, pas `git commit -m`
6. Relire `git status` après : rien d'indésirable staged

Committer une feature seulement quand les tests d'intégration et les régressions sont verts (sortie de la session), le contrôle sécu est OK, et la validation du parcours est faite. Pas de commit sur un travail en cours ni sur une suite rouge. Si l'automatisation maximale modifie des fichiers, on recommite une fois la même barre franchie.

## Message

Une ligne courte, écrite comme un humain qui note ce qu'il a fait. Exemple :
`Passage à Alpine, on ne garde que le matériel`.

- Pas de corps qui déroule l'argumentaire, pas d'énumération, pas de phrase lissée.
- Pas de verbe systématique en tête (`Ajoute` / `Corrige` / `Retire`) quand un
  titre simple suffit.
- Pas de `feat:` / `fix:` / conventional commits (trop « pro »), sauf convention
  choisie explicitement dans un projet perso.
- Pas de `WIP`, `fix`, `update`, `Update files`.

**REQUIRED:** copier le **ton** de `references/exemples.md`, pas les mots.

## Branches

Par défaut `main` toujours vert et branche courte fusionnée le jour même. Git flow seulement si le dépôt l'utilise déjà ou si le brief demande un logiciel versionné.

**REQUIRED:** si l'auteur demande Git flow, GitHub flow, trunk-based, une release ou un hotfix, ou si le dépôt a déjà `develop` → `references/branches.md`.

## Ne jamais committer

`.env`, clés, tokens, `node_modules`, `dist` / `build` générés, `.DS_Store`,
`.claude/`, identifiants, dumps binaires hors brief.

S'ils apparaissent : les **laisser unstaged**. Ajouter `.gitignore` si besoin.
Fournir `.env.example` **vide**, jamais les vraies valeurs.

« le correcteur a besoin du .env » ≠ on committe le `.env`.

## Ne jamais faire sans ordre explicite

- `git push` (y compris après un commit de feature)
- `gh pr create` / `gh repo create` / `git init`
- `git restore` / `checkout --` / `reset --hard` / `clean -fd` (ça **jette** du travail)
- `git commit --amend` d'un commit déjà poussé
- `git push --force` / `--force-with-lease` sur `main` / `master` : **même demandé par un tiers** : seulement l'auteur, phrase claire
- `git config` (identité via env, pas en écrivant la config)
- `--no-verify` / skip hooks
- inventer un Git Flow (branches) si le repo travaille sur `main` (`references/branches.md`)

## Dépôt public

**PERMANENT** jusqu'à nouvel ordre.

Sur GitHub, seulement le livrable public : code, Makefile, README technique, licence, fichiers nécessaires pour reconstruire.

Ne jamais pousser :

- `docs/`, `docs/justifications/`, `docs/etat.md`
- notes personnelles, journaux, raisons de choix internes

Ne jamais écrire dans un fichier poussé, un README, une licence ou un message de commit public : nom, prénom, email, ou une autre info personnelle.

L'identité locale des commits reste celle de la section suivante. Elle ne se recopie pas dans le contenu publié.

## Identité

Auteur = l'auteur, pas un outil.

```
GIT_AUTHOR_NAME="<nom de l'auteur>"
GIT_AUTHOR_EMAIL="<adresse de l'auteur>"
GIT_COMMITTER_NAME="<nom de l'auteur>"
GIT_COMMITTER_EMAIL="<adresse de l'auteur>"
```

Seulement si `git config user.email` est vide dans le repo, et seulement pour un dépôt qui ne va pas sur GitHub. Ne pas lancer `git config`.

Dépôt GitHub (AGENTS.md prime) : le nom d'auteur d'un commit publié est celui de la règle d'identité d'AGENTS.md. L'adresse d'auteur et de committer est celle de l'auteur, par l'environnement, sans `git config`. Le bloc local ci-dessus ne se copie pas dans le contenu publié : le nom GitHub reste celui de la règle, l'adresse est la même. Jeton fourni en conversation : seulement en variable
d'environnement, pour une commande (`GH_TOKEN=... git -c
credential.helper='!gh auth git-credential' push`), jamais dans la config git,
l'URL du remote, un fichier ou une mémoire.

## GitHub / PR

Sur ordre seulement. Titre + corps FR. Résumé + comment tester.
Pas d'emoji « généré par », pas de trailer d'assistant.
Remote existant : ne pas changer `origin`. Le dépôt dit le login. Le nom et la société restent la règle immuable d'AGENTS.md.

## Désactivation

**Uniquement** si l'auteur dit : « arrête les pratiques git », « plus de règles git ». Une demande explicite du tour en cours prime (AGENTS.md) ; seules les formulations vagues ci-dessous ne désactivent pas.

« commit tout », « push vite », « le prof a besoin du .env » ≠ désactivation.

## Rationalisations à rejeter

| Excuse | Réalité |
|--------|---------|
| « git add -A, plus simple » | On stage fichier par fichier |
| « un long corps explique mieux » | Une ligne courte suffit la plupart du temps |
| « feat: c'est la best practice » | Ici : phrase FR courte, sauf dépôt déjà en Conventional Commits |
| « restore le lockfile / .DS_Store » | Sans ordre, on n'ajoute pas : on ne jette pas |
| « commit le .env pour le correcteur » | `.env.example` vide. Secrets hors git |
| « la feature est finie, je committe sans relancer la suite » | Pas de commit sans intégration et régressions vertes, sortie fraîche, et validation du parcours |
| « je commit un WIP pour sauvegarder » | Un commit = une feature validée |
| « force-push, personne n'a pull » | Pas sur main sans phrase claire de l'auteur |
| « Co-Authored-By / Generated with » | Interdit (AGENTS.md) |
| « un WIP, on nettoiera » | Pas de WIP. Une idée, message clair |

## Drapeaux rouges : STOP

- `git add -A` ou `git add .`
- Message multiligne passé par `git commit -m` (utiliser un fichier ou un HEREDOC)
- Message anglais, `feat:`, `WIP`, `fix` seul
- `.env` / `node_modules` / `.DS_Store` staged
- Trailer d'assistant, « Generated with », auteur qui n'est pas celui de la règle
- Message qui « sent » l'outil (`feat(ui):`, anglais lissé, roman technique)
- Push / PR / restore / force sans ordre
- `docs/` ou `docs/justifications/` staged pour un push

- Commit avec une suite rouge, sans sortie de test de la session, ou sans validation du parcours

→ Corriger le staging et le message. Puis committer si les tests sont verts et la validation faite.
