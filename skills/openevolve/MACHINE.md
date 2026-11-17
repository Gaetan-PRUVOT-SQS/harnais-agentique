# Harnais local

Ce fichier prime sur le reste du skill. `~/.agents/AGENTS.md` prime sur ce fichier.

## Source

https://github.com/algorithmicsuperintelligence/openevolve

Commit `8c65f74aa906abc0b0e9cae948ddf4c4c6570bdc`, version `0.4.0`, licence Apache-2.0 (`LICENSE`). Le dépôt n'est pas copié ici.

## Place

Dossier canonique : `~/.agents/skills/openevolve`. Grok lit `~/.agents/skills` directement.

## Paquet

Ne pas lancer `pip install`, `pip install -e`, Docker, ni un clone. Le Python du système est 3.14.4. Le paquet demande `>=3.10`. Ne pas installer un autre Python.

Si `openevolve-run` manque, le dire et rester sur le plan écrit.

## Quand lancer

Une exécution demande, dans le même message : le programme graine, le fichier qui définit `evaluate`, le dossier de sortie, et un budget (`--iterations` ou `--target-score`). Sinon, écrire le plan et s'arrêter.

Ne pas lancer sur le défaut `max_iterations: 10000`. Le nombre vient de la demande. Une grosse boucle attend un chiffre écrit dans cette demande.

La boucle appelle un LLM payant. L'évaluateur exécute le programme produit. Ne pas lancer pour essayer le skill.

## Clé et fournisseurs

La clé reste dans l'environnement. Ne pas la lire, l'afficher, ni la copier dans un fichier, un YAML, un commit ou un journal.

Clé absente : le dire, ne pas inventer de valeur, ne pas lancer.

Ne pas activer `provider: claude_code`, `provider: copilot_cli`, `allow_all_tools`, ni `manual_mode`.

## Sortie

Passer `--output`. Refuser `/tmp`, `/tmp/*`, `/var/tmp`, `/var/tmp/*`.

Dans un dépôt git, seulement un dossier nommé et ignoré. Ne pas recopier le meilleur programme par-dessus la graine, sauf si la demande le dit.

Si la graine a des marqueurs `EVOLVE-BLOCK` et que le YAML laisse `enforce_evolve_blocks` à faux, le dire dans le plan avant de lancer.

## Écriture

Un seul écrivain. Pas de workers agents en parallèle, pas de worktree, pas de copie du dépôt. Le skill ne commit pas. Pendant une exécution autorisée, la bibliothèque peut lancer ses propres processus. On n'en ajoute pas.

## Délégation

Lecture d'un rapport ou d'un checkpoint déjà écrit : `explorateur` ou `chercheur`, un seul niveau. Le parent garde les conclusions et les fichiers. Un sous-agent ne lance pas `openevolve-run`.
