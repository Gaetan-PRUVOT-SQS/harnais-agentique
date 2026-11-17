---
name: weight-space-surgery
description: >-
  Améliorer un modèle à poids ouverts sans réentraînement : boucles, refus,
  politique coincée, édition de poids ou d'activations, score hors
  échantillon. Use when improving an open-weight model without gradient
  training (weight-space surgery, weight-space programming, rank-one edit,
  activation steering, ablation). /weight-space-surgery
---

# Weight-space surgery (improve a model without retraining)

Use this when the goal is to change an open-weight model's behavior by reading and editing weights or activations, not by launching a training job. Typical targets: thinking loops, stuck policies, a single unwanted direction, or a circuit that already exists but is blocked.

Do not use this when the model lacks the underlying skill. Editing cannot invent knowledge the network never learned. Prefer fine-tuning or continued pretraining in that case.

## Core idea

A frontier model (or a careful human with the same harness) inspects another network's weights, runs a limited budget of forward passes on practice data, names the failure in plain language, then writes a small patch to the tensors. No optimizer, no loss, no gradient. The MIT CSAIL post "Sparks of Weight-Space Programming" (Takehi, Teoh, Zhang, Khattab, Nov 2026) calls this Weight-Space Programming. The headline case: Qwen3.5-0.8B MATH-500 7.9% to 48.1% by subtracting one repetition direction from `down_proj` in layers 15 and 19 (131,072 weights, 0.016% of the model). Hugging Face rebuilt the checkpoint from the logs and re-scored MATH-500 at 51.0%.

Related families that also avoid full retraining (pick the lightest that fits):

- **Direct weight edit**: rank-one subtraction (or addition) along a measured direction in MLP `down_proj` / `up_proj` / attention `out_proj` columns (Experiment 8 pattern).
- **Activation steering / representation engineering**: add a fixed vector to residual stream activations at inference; no weight change. Good for quick A/B before committing a weight patch.
- **Ablation / zeroing**: set a head, neuron group, or direction to zero to confirm causality before editing.
- **Task vectors / weight arithmetic**: `theta_task = theta_finetuned - theta_base`, then add or negate on another base. Needs a prior fine-tune somewhere; you still avoid training the target.
- **Locate-then-edit (ROME / MEMIT style)**: locate a fact in mid-layer MLP, rewrite a key-value association. Narrow; for factual associations, not general reasoning loops.

Default order: measure failure -> build contrastive pairs -> extract direction -> ablate to prove cause -> commit the smallest weight patch -> evaluate held-out.

## Preconditions

1. Open weights you can load on CPU or GPU (Hugging Face `safetensors` / PyTorch state dict).
2. A clear behavioral failure you can reproduce with fixed sampling settings (temperature, top-p, top-k, presence penalty, max tokens, thinking on/off).
3. Practice prompts that are **not** the final test set. Hold out the real benchmarks.
4. A Python harness over the tensors: read/write named parameters, run batched forward passes, log generations and token-limit hits.
5. Bit-exact logging of every edit (which tensor, which columns/rows, the vector, the scale) so the patch can be rebuilt and hash-verified.

If you only have an API with no weight access, stop. Steering via logits bias or system prompt is not weight-space surgery; say so and offer that lighter path separately.

## Recipe (language model, math/reasoning loops)

### 1. Freeze the evaluation protocol

Write down sampling, max new tokens, thinking mode, grader (e.g. last `\boxed{}` with a fixed math verifier), and seeds. Reuse the same protocol for base and edited. Never tune sampling after seeing test scores.

### 2. Quantify the failure on practice data

Run a batch of practice problems (hundreds if the budget allows). Record:

- accuracy if an answer appears
- share of generations that hit the token limit
- whether the model already had the correct intermediate answer before looping
- share of duplicated sentences in truncated tails

If most failures are ordinary wrong steps (bad arithmetic, invalid algebra) with no shared pattern, surgical edit is unlikely to help. Say so and stop or switch to training. The Gemma 3 270M counter-example in the MIT post stayed near 7% MATH-500 after the same procedure: no single direction to remove.

### 3. Localize with contrastive pairs

Build paired texts: same problem, same reasoning prefix, then either a productive continuation (check and conclude) or a looping continuation (the same doubt sentence repeated). Under teacher forcing, read residual states for both. Per layer, average (loop - productive), normalize: that unit vector is the repetition direction.

Project each MLP's write (via `down_proj`) onto the next layer's direction. Keep the layers that dominate (in Experiment 8: 15 and 19). Rank neurons by how aligned their `down_proj` column is with that direction, weighted by activation change during the loop. Take a small top set (64 per layer concentrated 91 to 98% of the contrast in Experiment 8).

Confirm with ablation and a random orthogonal control of equal norm. If the random direction barely moves the metric, the measured direction is doing the work.

Budget forward passes deliberately (e.g. 10 / 25 / 50 packs of up to 512 sequences). Prefer fewer, decisive probes over exhaustive search. In Experiment 8 only the 50-pass budget unlocked the big gain.

### 4. Patch (rank-one subtraction on selected columns)

Experiment 8's frozen edit, from the authors' final report:

```text
W = W0 - scale * outer(u, mask * (u @ W0))
```

Equivalently, for each selected column `i`: `W_i' = W_i - scale * (u · W_i) * u`, with `u` the unit repetition direction and `mask` selecting the top columns (64 per layer there). Scale was swept (1, 2, 3, 4, 6); 6 was kept after a dose-response on repeated-segment log-prob without harming productive segments. Orthogonal content of those columns is preserved; aligned write is inverted and amplified.

Touch on the order of 0.01% to 0.1% of parameters when possible. Edit the concrete tensor indices you measured. Save a diff (old bytes hash, new bytes hash) for every touched tensor.

### 5. Verify on held-out tests

Evaluate base vs edited on the held-out suite the editor never saw. Report at least:

- primary task score (e.g. MATH-500)
- a near transfer set (e.g. GSM8K)
- a non-math control (e.g. instruction following)
- token-limit hit rate
- regressions on answers that already finished before the edit

Independent rebuild: re-apply the logged patch to a clean base checkpoint, hash-check tensors, re-run the suite. Only then claim the result.

### 6. Interpret honestly

If accuracy rises mainly because loops stop, say the edit **unblocked** existing skill. If a non-looping model does not move, say the method **cannot add** missing skill. Never describe the gain as "N times smarter" without stating what was measured. Do not treat viral video numbers (e.g. "192 rechecks") as fact unless they appear in primary logs.

## Recipe (small policies / control nets)

For tiny MLPs that fit in context or a notebook:

1. Give the editor the full weight list (or a sandbox over tensors), the observation/action layout, and one failure episode.
2. Ask for a diagnosis in plain language, then a minimal edit that fixes only the named cause.
3. Score on a large frozen episode set the editor did not cherry-pick during editing.
4. Prefer one-shot or few-shot edits that change a few percent of weights over rewriting the whole net, unless the task is "write weights from scratch".

## Safety and scope

- Never edit a deployed model without a rollback checkpoint and a side-by-side eval.
- Never claim validation from practice-set scores alone.
- Do not hide sampling changes inside an "edit" story.
- Keep secrets and user data out of practice prompts sent to an external editor model.
- If the only available editor is a closed API, treat logs as sensitive; store diffs locally.
- Novelty caveat: the linear-direction removal itself is close to known abliteration / steering work; what Experiment 8 stresses is an end-to-end general LLM driving the procedure without a human-written recipe.

## Deliverables when you run this skill

1. Short failure report (what breaks, how often, sampling fixed).
2. Localization note (layers, tensors, direction, contrastive pairs, ablation and orthogonal control).
3. Patch file or script (`apply_edit.py` style) with scale, mask, and sha256 of touched tensors.
4. Held-out table: base vs edited, including token-limit rate and at least one control benchmark.
5. One-paragraph limit statement: unblocked vs newly taught.

## Sources to cite when explaining the method

- Takehi, Teoh, Zhang, Khattab. "Sparks of Weight-Space Programming". Nov 2026. https://rikiyat.github.io/blog/weight-space-programming/
- Edited demo checkpoint: https://huggingface.co/RikiyaT/Qwen3.5-0.8B-weight-space-programming
- Experiment logs (formula in `exp8_math/runs/p50c/work_notes/final_report.md`): https://github.com/RikiyaT/lm_understand-logs

When writing user-facing docs from this skill, strip tool names that the owner forbids in published text, keep facts and URLs, and avoid em dashes.
