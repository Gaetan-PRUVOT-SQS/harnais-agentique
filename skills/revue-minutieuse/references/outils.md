# Outils du code mort

Référence de `revue-minutieuse`. L'oracle reste les trois questions. Un
outil produit des **candidats**. On confirme sur le source.

Ordre : compilateur et linter **du projet**, déjà en `-Werror` ou équivalent,
puis un graphe si le linter ne voit qu'un fichier. On n'installe un outil
que s'il sert cette mission (`AGENTS.md`). Sorties dans un dossier de build
ignoré par git. `tests-locaux`.

## Par langage

| Langage | D'abord (projet) | Graphe, si besoin |
|---|---|---|
| C | `gcc -Wall -Wextra -Werror` (`-Wunused*`). clang `-Wunreachable-code` en analyse. cppcheck, clang-tidy | cppcheck `unusedFunction`. Un `.c` jamais listé dans le Makefile |
| Rust | `rustc` / clippy : `dead_code`, `unused_*`. `cargo clippy` du projet | |
| JS / TS | ESLint `no-unused-vars`, TypeScript `noUnusedLocals` / `noUnusedParameters` | `knip` si le dépôt l'a, sinon `npx knip` pour cette passe. Fichiers et exports |
| Python | ruff `F401` `F841`, pyflakes | `vulture` (confiance 80+). Relancer après un retrait, il en découvre d'autres |
| PHP | PHPStan / Psalm, règles unused du projet | |
| Go | `staticcheck` U1000, compilateur | `deadcode` pour les fonctions inatteignables |
| Java | inspection unused de l'IDE du projet, PMD Unused* | |
| Shell | shellcheck (déjà le hook). Une fonction jamais appelée, un script hors Makefile | |

C : gcc ne promet pas `-Wunreachable-code` (avertissement historiquement
faible). La lecture page-by-page reste obligatoire. clang et cppcheck
complètent.

Un avertissement `unused` sur une ligne du changement est un bloquant
candidat. On ne le muselle pas (`# unused`, `@ts-ignore`, `(void)` posé
pour taire) sans la raison MISRA : retour qu'on doit ignorer, dite.

## Graphe contre fichier

ESLint, ruff, `-Wunused` voient **un** fichier. Un export jamais importé,
un fichier orphelin, une dépendance du manifeste : il faut le graphe
(knip, vulture, `go mod tidy` / `npm ls` selon le manifeste).

Les tests et les points d'entrée du framework se déclarent à l'outil
(sinon faux positif). On ne « corrige » pas un faux positif en élargissant
l'ignore : on nomme l'entrée.

## Couverture

`gcov`, `coverage`, c8, lcov : piste, pas verdict. Une ligne jamais
exécutée par la suite peut être un cas manquant. Une ligne inatteignable
est morte même si un test l'importe. `iso-29119` possède le plan de
couverture.

## Commande type

Dans le projet, après le diff :

1. Build et linter du dépôt, lire `unused` / `dead_code` / `F401`.
2. Si JS/TS et graphe utile : knip sur les fichiers touchés.
3. Si Python et doute sur des fonctions : vulture à confiance haute.
4. Relire chaque candidat avec les trois questions.
5. Retirer, relancer : un mort en cache souvent un autre.

On n'invente pas un vert. La sortie de cette session se cite dans le
compte rendu du skill.
