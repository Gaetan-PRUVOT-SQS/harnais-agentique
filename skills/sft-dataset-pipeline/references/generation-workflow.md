# Workflow de génération

## Grille

```
shard_index = topic_index × num_difficulties + difficulty_index
volume      ≈ num_cells × examples_per_cell
```

Exemple : 30 topics × 3 niveaux × 12 ex ≈ 1080.

## Types de tâches (mixer par cellule)

- Génération de code
- Debug d'erreur / stack trace
- Explication de concept
- Review / refacto
- Migration (X → Y)

## Contraintes agent (qualité)

**Faire :**
- APIs actuelles du domaine cible
- Snippets complets et compilables au niveau de difficulté
- Variété de formulation, pas de quasi-doublons
- Langue assistant = langue utilisateur

**Ne pas faire :**
- Placeholders (`// ...`, `[insert]`, lorem)
- APIs dépréciées pour le sujet traité
- Gros payload dans le chat (écrire le fichier shard directement)
- Mélange de langues dans un même exemple

## Prompt agent

```
Génère ~{examples_per_cell} exemples SFT :
  Topic: {topic}
  Niveau: {beginner|intermediate|advanced}
  Domaine: {description}

Fichier: shards/shard_{index:03d}.jsonl
System (exact): {canonical_system}

Format: 1 JSON/ligne, messages system/user/assistant
Langues: {language_mix}
Retour: {"file": "shards/shard_XXX.jsonl", "count": N}
```

## Orchestration parallèle

```
parallel(cells[0..N-1]):
  agent(cell[i]) → shard_i.jsonl
  assert count >= 10
```

## Vérification post-génération

```python
topic_index = shard_index // len(difficulties)
level_index = shard_index % len(difficulties)
```

Comparer avec la taxonomie attendue. Régénérer les shards décalés.

## Scaling

| Stratégie | Volume |
|-----------|--------|
| Standard | cells × 12 |
| Plus/cellule | cells × 20 |
| Plus de topics | 40 × 3 = 120 cells |
| 2e passe variation | merge + dedup build |