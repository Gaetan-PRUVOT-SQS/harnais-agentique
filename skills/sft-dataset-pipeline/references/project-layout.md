# Structure projet (générée par scaffold)

Produit par `scripts/scaffold.py` à partir de `templates/` embarqués dans le skill.

```
<projet>/
├── config.json              # source de vérité (persona, modèle, taxonomie, volume)
├── train.jsonl              # 95% (split_ratio)
├── val.jsonl                # 5%
├── stats.json               # auto (build.py)
├── qa_report.json           # auto (audit.py)
├── quarantine.jsonl         # exemples non récupérables
├── benchmark_report.json
├── tokenizer_report.json
│
├── shards/shard_NNN.jsonl   # génération multi-agents
│
├── build.py                 # orchestrateur
├── audit.py                 # QA + auto-fix (lit config.json)
├── test_qa.py               # unit tests + gates
├── qa_fix.py                # fixtures (__CANONICAL__ → config)
├── benchmark.py
├── tokenizer_check.py
│
└── qa_dataset/
    ├── fixtures.json        # 15 cas régression
    ├── corrected.jsonl      # sorties auto-fix
    └── report.json
```

## Format JSONL

```json
{"messages": [
  {"role": "system", "content": "..."},
  {"role": "user", "content": "..."},
  {"role": "assistant", "content": "..."}
]}
```

Compatible TRL `SFTTrainer`, Unsloth, `load_dataset("json")`.

## Config-driven

`audit.py` charge `canonical_system` depuis `config.json` au démarrage.
`build.py` lit `shuffle_seed`, `split_ratio`.
`tokenizer_check.py` lit `target_model`, `tokenizer_limits`.
`test_qa.py` lit `target_examples` pour les gates de taille minimale.

## Scaffold

```bash
python3 <skill>/scripts/scaffold.py \
  --name <nom> --output <chemin> \
  [--system "..."] [--model hf/id] [--examples 1000]
```