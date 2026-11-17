---
name: sft-dataset-pipeline
description: >-
  Construire des datasets SFT de chat (JSONL messages) : shards, audit QA avec correction, fixtures de régression, tokenizer, benchmark. Use when creating or auditing a chat SFT dataset.
---

# SFT Dataset Pipeline : Méthodologie

Template method autonome. Tout le code et les fixtures sont embarqués dans ce skill (`templates/`). Aucune dépendance à un projet externe.

## Quand l'utiliser

- Nouveau dataset SFT pour un assistant domaine/code
- Extension ou rebuild d'un dataset shard-based
- Gates QA avant fine-tuning
- Validation prod-readiness ou fit tokenizer

## Phases

```
Phase 1 : Cadrage     → config.json (persona, taxonomie, modèle, volume)
Phase 2 : Génération  → shards parallèles (1 cellule = 1 shard)
Phase 3 : QA          → audit auto-fix + quarantaine
Phase 4 : Build       → concat, dedup, shuffle, split train/val
Phase 5 : Validation  → tests, fixtures, gates, benchmark, tokenizer
Phase 6 : Décision    → prod-ready checklist
```

## Phase 1 : Cadrage (`config.json`)

```json
{
  "project_name": "my-domain-ft-dataset",
  "canonical_system": "You are a senior …",
  "target_model": "google/gemma-4-E4B-it",
  "max_seq_length": 2048,
  "tokenizer_limits": [2048, 4096, 8192],
  "split_ratio": 0.95,
  "shuffle_seed": 1337,
  "target_examples": 1000,
  "language_mix": {"fr": 0.33, "en": 0.67},
  "examples_per_cell": 12,
  "taxonomy": {
    "topics": ["topic-a", "topic-b"],
    "difficulties": ["beginner", "intermediate", "advanced"],
    "cells": 90
  }
}
```

Tout le pipeline lit `config.json` : persona, modèle cible, split, gates de taille.

## Phase 2 : Génération multi-agents

### Grille taxonomique

```
cells = len(topics) × len(difficulties)
shard_index = topic_index × len(difficulties) + difficulty_index
fichier     = shards/shard_{index:03d}.jsonl
```

Volume typique : **30 topics × 3 niveaux × ~12 ex = ~1080 exemples**.

### Format JSONL (une ligne = un exemple)

```json
{
  "messages": [
    {"role": "system", "content": "<canonical_system>"},
    {"role": "user", "content": "<question>"},
    {"role": "assistant", "content": "<réponse + ```code```>"}
  ]
}
```

### Prompt agent (template)

```
Génère ~{examples_per_cell} exemples SFT pour :
- Topic : {topic}
- Niveau : {difficulty}
- Domaine : {stack ou métier}

Fichier : shards/shard_{index:03d}.jsonl
System prompt (exact) : {canonical_system}

Contraintes :
- Questions réalistes, réponses idiomatiques
- Assistant dans la MÊME langue que l'utilisateur
- Code complet dans des blocs ``` avec tag langage
- PAS de placeholders (// ..., [insert code], lorem ipsum)
- Mix : génération, debug, explication, review, migration
- Retourne uniquement : {"file": "...", "count": N}
```

### Piège critique

Vérifier `shard_index ↔ topic` après génération. Un décalage d'index corrompt la couverture thématique.

Détails : [references/generation-workflow.md](references/generation-workflow.md)

## Phase 3 : QA (audit déterministe)

### Auto-fix

| Rule ID | Action |
|---------|--------|
| `prompt.canonical_system` | Remplace par `config.canonical_system` |
| `content.unescape_*` | `html.unescape` |
| `content.trim_*` | Strip whitespace |
| `structure.role_order` | system → user → assistant |
| `markdown.unbalanced_fence` | Ajoute ` ``` ` fermant |
| `content.expand_ellipsis` | Supprime `// ...`, `{/* ... */}`, `/* ... */` |

### Quarantaine (non récupérable)

- Placeholders cassés, mismatch langue haute confiance, assistant < 80 chars, JSON invalide

Règles complètes : [references/qa-rules.md](references/qa-rules.md)

### Fixtures de régression

15 cas minimum embarqués dans `templates/qa_dataset/fixtures.json`. Le token `__CANONICAL__` est résolu depuis `config.json` à l'exécution.

Catégories : pass (EN/FR), fix (system, entities, order, fence, ellipsis), quarantine (placeholder, lang, too-short).

## Phase 4 : Build (`build.py`)

Ordre strict :

```
unit_tests → fixtures → audit_shards(fix=True)
→ concat → dedup (hash 1er user normalisé) → shuffle(seed)
→ train.jsonl + val.jsonl → validate_jsonl → dataset_gates
```

Sorties auto : `stats.json`, `qa_report.json`, `quarantine.jsonl`. README manuel.

## Phase 5 : Validation

```bash
python3 -m unittest test_qa.py -v
python3 qa_fix.py          # failed == 0
python3 build.py
python3 benchmark.py
.venv/bin/python tokenizer_check.py
```

Critères : `health_score == 100`, `quarantine_count == 0`, 0% troncature @ `max_seq_length`.

## Phase 6 : Prod-ready

| Gate | SFT v1 |
|------|--------|
| health_score 100% | Oui |
| quarantine 0 | Oui |
| tests + fixtures verts | Oui |
| tokenizer 0% truncation | Oui |
| spot-check humain 5–10 ex | Recommandé |
| eval modèle | Requis pour prod critique |

QA valide la **forme**, pas la compilation du code.

Checklist : [references/prod-ready.md](references/prod-ready.md)

## Scaffolding d'un nouveau projet

Le skill embarque tout dans `templates/`. Aucun fichier externe requis.

```bash
python3 ~/.agents/skills/sft-dataset-pipeline/scripts/scaffold.py \
  --name my-ft-dataset \
  --output ~/Bureau/my-ft-dataset \
  --system "You are a senior …" \
  --model google/gemma-4-E4B-it
```

Structure produite : [references/project-layout.md](references/project-layout.md)

## Arborescence du skill (self-contained)

```
sft-dataset-pipeline/
├── SKILL.md                    ← cette méthodologie
├── scripts/scaffold.py         ← copie templates/ → projet cible
├── templates/                  ← code + fixtures embarqués
│   ├── config.json
│   ├── audit.py, build.py, test_qa.py, qa_fix.py
│   ├── benchmark.py, tokenizer_check.py
│   └── qa_dataset/fixtures.json
└── references/                 ← docs méthodo (pas de deps externes)
```

## Adapter à un nouveau domaine

1. Scaffold le projet
2. Remplir `taxonomy.topics` dans `config.json`
3. Personnaliser `canonical_system`
4. Ajuster les exemples dans `fixtures.json` si le domaine n'est pas code/FR-EN
5. Générer les shards en parallèle
6. `build.py` → `benchmark.py` → `tokenizer_check.py`

## Pièges connus

- Index shard ≠ index taxonomie → régénérer les shards concernés
- Ellipsis `// ...` → auto-fix, pas quarantaine
- `role_order` doit écrire le shard même sans autre fix
- `loadTestsFromTestCase` (pas `loadTestsFromClass`)
- Modèles nested config (Gemma4) : `text_config.max_position_embeddings`
- `transformers>=5.5` pour architectures récentes

## Commandes

```bash
python3 build.py
python3 audit.py --check-only
python3 -m unittest test_qa.py -v
python3 qa_fix.py
python3 benchmark.py
.venv/bin/python tokenizer_check.py
wc -l train.jsonl val.jsonl
```