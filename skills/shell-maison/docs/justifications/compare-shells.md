# Feature : compare-shells, test différentiel d'un shell maison

Date : 2026-09-29

## Métier

- Besoin : un shell maison doit se comporter comme un shell de référence
  sur le sous-ensemble choisi. Lire la spec ne suffit pas à prouver le
  comportement ; comparer à dash sur des cas précis, si.
- Qui est concerné : L'auteur quand il écrit son shell (VelumOS, projet
  perso), l'agent qui ajoute des cas.
- Impact si on ne le fait pas : écarts de quoting, d'expansion ou de code
  de retour découverts tard, un par un.

## Ce qu'on fait

- Comportement visible : `compare-shells SHELL_TESTE DOSSIER_CAS
  [REFERENCE]` lance chaque `DOSSIER_CAS/*.sh` avec les deux shells,
  compare sortie standard, code de retour et présence d'erreurs, affiche
  OK ou KO avec un extrait du diff, puis le total. Code 1 si un cas diffère
  ou s'il n'y a aucun cas, 2 pour un mauvais usage, 127 si la référence
  manque.
- Fichiers touchés : `scripts/compare-shells`, `scripts/cas/*.sh`,
  `scripts/tests/compare-shells.bats`, `scripts/tests/faux-shell`, lien
  `~/.local/bin/compare-shells`.

## Choix techniques

| Choix | Pourquoi | Alternative rejetée | Impact métier |
|-------|----------|---------------------|---------------|
| dash comme référence par défaut | petit, proche de POSIX, installé | bash | on vise POSIX, pas les extensions de bash |
| Comparer la présence d'erreurs, pas leur texte | chaque shell préfixe ses messages à sa façon | comparer stderr mot pour mot | pas de faux KO sur `dash: 1:` |
| Écrit en sh POSIX, vérifié par shellcheck, checkbashisms, shfmt -fn | il doit tourner partout, y compris sous le shell testé | bash | exemple vivant du skill scripts-shell |
| Sorties dans `build/compare-shells` | règle tests-locaux : rien hors du projet | fichiers temporaires | rien à nettoyer ailleurs |
| Aucun cas = échec | un dossier vide ne prouve rien | réussite | pas de faux vert |
| Tests bats avec un faux shell | prouve que le banc détecte un écart | tester seulement le cas vert | le banc ne peut pas passer à vide |

## Traçabilité

| Fichier | Fonction / bloc | Justifié par |
|---------|-----------------|--------------|
| `compare-shells` | `lancer` | présence d'erreurs, sorties dans build |
| `compare-shells` | `comparer` | comparaison et diff |
| `compare-shells` | fin (`[ "$total" -gt 0 ]`) | aucun cas = échec |
| `tests/compare-shells.bats` | 6 tests | faux shell, codes 2 et 127 |
