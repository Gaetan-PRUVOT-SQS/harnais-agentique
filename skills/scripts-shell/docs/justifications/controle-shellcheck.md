# Feature : shellcheck lancé à chaque écriture de script shell

Date : 2026-09-29

## Métier

- Besoin : les scripts shell (build, tests, outils, hooks de projets) sont
  écrits vite et relus peu. Une variable sans guillemets ou un shebang
  manquant passe inaperçu jusqu'au jour où il efface ou casse quelque chose.
- Qui est concerné : L'auteur et l'agent, dans tout projet qui contient du
  shell.
- Impact si on ne le fait pas : erreurs shell connues livrées alors qu'un
  outil les trouve en une seconde.

## Ce qu'on fait

- Comportement visible : après chaque écriture d'un `.sh`, d'un `.bash`
  ou d'un fichier sans extension à shebang sh, bash, dash ou ksh, le hook
  lance shellcheck et ajoute `SHELLCHECK KO. Corriger :` et la liste au
  contexte de l'agent. Rien si le script est propre.
- Fichiers touchés : `~/.agents/hooks/gate-shell-post.sh`,
  `~/.agents/hooks/dispatch.py` (`SHELL_FILES`, `SHEBANG_SHELL`,
  `script_shell`), `~/.agents/hooks/verify.py`
  (`test_shellcheck_apres_ecriture`), `~/.agents/hooks/ignores.sh`
  (shebang).

## Choix techniques

| Choix | Pourquoi | Alternative rejetée | Impact métier |
|-------|----------|---------------------|---------------|
| Niveau `-S info` | SC2086 (variable sans guillemets), l'erreur la plus fréquente, n'est qu'au niveau info | `-S warning` | l'erreur numéro un est signalée |
| `-e SC1091` | un `source "$VAR/x.sh"` ne peut pas être suivi statiquement : ce n'est pas un bug | tout garder | pas de bruit dans chaque projet |
| Détection par extension ou shebang | beaucoup d'outils shell n'ont pas d'extension | extension seule | les scripts d'outillage sont aussi vérifiés |
| PostToolUse, contexte seulement | l'agent corrige tout de suite, dans le même tour | bloquer au Stop | pas de boucle de blocage |
| Message si shellcheck absent | ne jamais laisser croire à un contrôle fait | silence | pas de fausse validation |

## Traçabilité

| Fichier | Fonction / bloc | Justifié par |
|---------|-----------------|--------------|
| `hooks/dispatch.py` | `script_shell`, `SHEBANG_SHELL` | détection par extension ou shebang |
| `hooks/gate-shell-post.sh` | appel `shellcheck -S info -x -e SC1091` | niveau info, SC1091 |
| `hooks/gate-shell-post.sh` | message shellcheck absent | pas de fausse validation |
| `hooks/verify.py` | `test_shellcheck_apres_ecriture` | tous les cas ci-dessus |
