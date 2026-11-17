---
name: openevolve
description: 'Évolution de code par LLM si le paquet est déjà là. Graine, évaluateur, budget nommés. Use for OpenEvolve, evolve a program, or MAP-Elites.'
---

# OpenEvolve

Sur cette machine, lire [MACHINE.md](MACHINE.md) avant toute phase. S'il contredit ce fichier, MACHINE.md prime. `~/.agents/AGENTS.md` prime sur les deux.

Bibliothèque d'évolution de programmes, commit `8c65f74aa906abc0b0e9cae948ddf4c4c6570bdc`, version `0.4.0`, licence Apache-2.0 (`LICENSE`). Le code du dépôt n'est pas dans ce dossier.

## Sélection

On garde le programme que `evaluate` mesure le meilleur. Un score moins bon, ou pas mesuré, ne remplace pas ce parent. Pas de population lancée d'ici. `AGENTS.md` porte la même règle.

## Commande

Point d'entrée installé : `openevolve-run` (`openevolve.cli:main`).

```
openevolve-run PROGRAMME EVALUATEUR [options]
```

`EVALUATEUR` est un fichier Python qui définit `evaluate`.

Options :

- `--config` / `-c` : YAML
- `--output` / `-o` : dossier de résultats
- `--iterations` / `-i` : nombre d'itérations
- `--target-score` / `-t` : score d'arrêt
- `--checkpoint` : reprise d'un dossier `checkpoint_N`
- `--api-base` : URL de l'API
- `--primary-model`, `--secondary-model`
- `--evaluator-args` : objet JSON transmis à `evaluate` si sa signature l'accepte
- `--logger-prefix`, `--log-level`

Sans `--output`, la bibliothèque crée `openevolve_output` à côté du programme. Les checkpoints sont sous `<sortie>/checkpoints/`.

## Réglages par défaut

`diff_based_evolution` vaut vrai : l'évolution propose des blocs `<<<<<<< SEARCH`, `=======`, `>>>>>>> REPLACE`. Une réécriture complète du fichier demande `diff_based_evolution: false` dans le YAML.

`enforce_evolve_blocks` vaut faux. Les marqueurs `EVOLVE-BLOCK-START` et `EVOLVE-BLOCK-END` (commentaire du langage, ou une ligne qui contient `# EVOLVE-BLOCK-START`) ne bornent les modifications que si le YAML met ce réglage à vrai.

`max_iterations` vaut 10000. Sans fichier YAML, la clé vient de `OPENAI_API_KEY` et la base de `OPENAI_API_BASE` (défaut `https://api.openai.com/v1`). Un YAML peut citer `${OPENAI_API_KEY}`.
