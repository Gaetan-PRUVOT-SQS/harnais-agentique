# Checklist prod-ready

## Gates automatiques

```bash
python3 -m unittest test_qa.py -v
python3 qa_fix.py
python3 build.py
python3 benchmark.py
.venv/bin/python tokenizer_check.py
```

### Attendu

- `qa_report.json` → `health_score: 100`, `lines_quarantined: 0`
- `qa_dataset/report.json` → `failed: 0`
- `tokenizer_report.json` → 0% overflow @ `max_seq_length`
- `train.jsonl` / `val.jsonl` valides JSON, ratio ≈ split_ratio

## Ce que QA prouve / ne prouve pas

| Prouvé | Non prouvé |
|--------|------------|
| Structure JSON valide | Code compile |
| System prompt canonique | Code exécutable en prod |
| Ordre des rôles | Exactitude factuelle |
| Pas de placeholders | Pédagogie optimale |
| Cohérence langue | Absence d'hallucinations |

## Spot-check humain (5–10 ex)

- Question réaliste ?
- Code/APIs corrects pour le domaine ?
- Langue cohérente ?
- Bloc code complet ?
- Pas de duplication évidente ?

## Verdict

| Usage | Prêt ? |
|-------|--------|
| SFT v1 / expérimentation interne | Oui si gates OK + spot-check |
| Beta équipe | + eval modèle held-out |
| Prod client | + eval complète + review humaine |
| Code safety-critical | + vérification compile/run |

## Fine-tuning

```python
SFTConfig(
    max_seq_length=<config.max_seq_length>,
    dataset_text_field="messages",
)
```

Choisir `max_seq_length` depuis `tokenizer_report.json` (p99 ou max observé, 0% truncation).