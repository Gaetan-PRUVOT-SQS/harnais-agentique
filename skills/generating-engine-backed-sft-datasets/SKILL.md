---
name: generating-engine-backed-sft-datasets
description: >-
  Use when building an SFT dataset where the assistant delegates exact computation to a tool or engine through a structured JSON call. Triggers: tool-call datasets, engine block.
---

# Generating engine-backed SFT datasets

## Overview

Build the dataset **programmatically**, then gate it with an audit that **executes every training target** and a separate report that **scores continuous quality**. Hand-written tool-call data has typos, label noise, and silent contract drift; generated data with an executing audit cannot ship a target that doesn't run.

**Core principle:** the model should learn to *route and extract the user's values* into the call — not to memorize one canonical parameterization per function. So sample varied params and put the exact numbers **verbatim** in the user prompt.

## When to use

- Training a copilot/agent to emit a structured call (JSON tool-call, ```engine``` block, function call) that a deterministic backend executes.
- You want the model to **never state the number itself** — it delegates exact arithmetic.
- You need reproducible regeneration + a hard quality bar (CI gate).

**Not for:** free-form prose datasets, RLHF preference pairs, or when there is no executable backend to validate against (then you have no ground-truth gate — most of the value is gone).

## Architecture (six pieces)

| Piece | Role | Rule |
|---|---|---|
| **Registry** | `module → allowed functions` whitelist | Single source of truth. Generator AND audit import the *same* file. |
| **Samplers** `mk_*(rng)` | one per function: `(rng) → (user_prompt, params)` | Draw realistic varied params; inject the numbers **verbatim** into the prompt. |
| **Renderers** | wrap the call in varied natural prose | Multiple templates + rng for lexical diversity; never leak the answer. |
| **Generator** | assemble records, fixed `SEED` | Deterministic → byte-identical regen. Balance by category. |
| **Audit** | hard pass/fail gate | **Executes every call through the real backend.** Exit 1 on any failure. |
| **Quality report** | continuous score | Diversity, balance, leakage, param-variety — the "is it good" beyond "does it run". |

## The quality loop

```bash
python3 generate_dataset.py   # 1. regenerate (deterministic; same seed → same bytes)
python3 audit_dataset.py      # 2. HARD GATE — must print PASS / exit 0
python3 quality_report.py     # 3. SCORE — aim for an A; fix anything flagged
```

Never ship unless the audit is PASS **and** the score is acceptable. Audit = binary correctness; report = continuous quality. You need both.

## What the audit MUST check (hard gates)

1. **Execute every call** through the real dispatcher/backend; fail if it raises or returns empty. (This is the strongest gate — it proves targets are runnable, not just well-formed.)
2. JSON parses; required keys present; `(module, function)` ∈ registry.
3. Structure: roles alternate, ends on assistant, no empty content.
4. **Anti-leak of the answer**: regex the prose for a stated number (`vaut/equals/price is …\d`) — the assistant must delegate, not compute. Fail if found.
5. Per-record contract: exactly N call-blocks for call-kinds, **0** for chat/route/identity kinds.
6. Prose/call agreement: if prose says "module 04", the block's module must be 04.
7. Coverage: every registry function used ≥ 1×.

## What the quality report MUST score (continuous)

- **Param variety per function**: distinct param-sets / occurrences. A function with **1 param-set is a red flag** — the model memorizes instead of extracting.
- **Train/val leakage**: build val from *independent* draws, **dedupe against train**; target 0%.
- **Prompt & answer uniqueness** (% distinct), vocab size.
- **Balance**: pick category (module) uniformly *first*, then function within it — otherwise a category with more functions gets over-weighted. Score = `100·(1 − CV)` of shares.
- **Conversation depth**: share of multi-turn records.

## Common mistakes

- **Hand-writing records** → typos, drift, label noise. Generate everything.
- **Audit that only checks JSON shape** → ships calls that crash the backend. Always *execute*.
- **One fixed param-set per function** → model emits frozen params, ignores the user's numbers. Sample + inject verbatim.
- **Val drawn from the same pool without dedup** → leakage; metrics lie. Independent draws + `prompt not in train_prompts`.
- **Balancing per function** when categories have unequal function counts → skew. Balance per category first.
- **Letting prose state the answer** → defeats the whole "delegate to engine" objective. Regex-gate it.
- **Non-deterministic generation** → can't reproduce or diff. Fix `SEED`; avoid wall-clock/`random()` without the seeded `rng`.

## Adapting to a new domain

1. Define the **registry** (your output contract / allowed calls).
2. Write one **sampler per call** that draws realistic params and puts them verbatim in the prompt.
3. Add **multiple phrasing templates** + rng variation.
4. **Balance** by top-level category.
5. Generate **val** by independent draws, **deduped** against train.
6. Write the **executing audit** (binary gate) and the **metrics report** (continuous score).
