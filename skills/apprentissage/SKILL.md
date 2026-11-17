---
name: apprentissage
description: Boucle d'auto-amélioration locale, sur le modèle Hermes. Use for Hermes self-improvement, a skill draft, bounded memory, or the curator.
---

# Apprentissage

Sur cette machine, lire [MACHINE.md](MACHINE.md) avant toute phase. S'il contredit ce fichier, MACHINE.md prime. `~/.agents/AGENTS.md` prime sur les deux.

Cette boucle reprend le geste d'Hermes Agent : après un workflow qui vaut d'être refait, une impasse dont le chemin a été trouvé, ou une correction de l'auteur, on garde la leçon. La mémoire garde un fait court. Une procédure va dans une skill. On ne réécrit pas les règles d'`AGENTS.md`.

## Mémoire

Un fait durable (préférence déjà confirmée, convention, correction) s'ajoute à `memory/global/apprentissage.md`. Le plafond est 2 200 caractères, celui de `MEMORY.md` chez Hermes. Au-dessus, on refuse et on consolide, on ne coupe pas en silence. Une entrée déjà présente ne se répète pas. Le profil de session reste `AGENTS.md` : on n'écrit pas un second profil.

## Skill

Sans accord, `deposer` écrit un brouillon dans `skills/apprentissage/journal/`. Ce dossier n'est pas versionné. Avec accord, la skill entre dans `~/.agents/skills/<nom>/SKILL.md` et une ligne `create` part dans le journal `ledger.jsonl`. Le nom est en minuscules et tirets. On ne pose pas de clé privée.

Le skill `learn` de Grok lit les sessions et propose des changements. Il reste la voie quand la demande est `/learn`. Ici, la leçon vient du travail en cours.

## Curateur

Il ne touche que les skills marquées `created_by: agent`. Une skill demandée par l'auteur, ou déjà dans le catalogue, reste en place (`conserve`). Une skill agent épinglée reste `active`. Sans usage, rien ne bouge avant 14 jours d'âge. Ensuite : `stale` à 14 jours sans usage, `archive` à 30. On n'efface pas. Pas de passage qui fusionne des skills par un modèle. Pas de démon, pas de `curl`, pas d'install d'Hermes.
