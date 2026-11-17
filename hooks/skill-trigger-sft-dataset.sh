#!/usr/bin/env bash
# UserPromptSubmit hook: deterministically nudge the model to load the
# generating-engine-backed-sft-datasets skill when the prompt is about
# building tool-call / engine-backed fine-tuning datasets.
#
# Reads the hook payload (JSON) on stdin, matches the user prompt against a
# keyword set (FR + EN), and on a hit injects additionalContext telling the
# model to invoke the skill. No match → emit nothing (silent passthrough).
set -euo pipefail

payload="$(cat)"

# Extract the prompt; fall back to empty if jq/key missing.
prompt="$(printf '%s' "$payload" | jq -r '.prompt // empty' 2>/dev/null || true)"
[ -z "$prompt" ] && exit 0

# Case-insensitive keyword match. Distinctive multi-word triggers to avoid
# firing on unrelated "dataset" or "training" chatter.
if printf '%s' "$prompt" | grep -iqE \
  'tool[ -]?call dataset|function[ -]?call dataset|engine[ -]?backed|bloc engine|engine block|dataset.*tool[ -]?call|dataset.*moteur déterministe'; then
  ctx='Le prompt concerne la création d'\''un dataset SFT/fine-tuning à base d'\''appels structurés (tool-call / engine block). Skill utile : generating-engine-backed-sft-datasets (dataset où l'\''assistant appelle un outil). Pour un dataset chat JSONL classique : sft-dataset-pipeline.'
  jq -nc --arg ctx "$ctx" '{hookSpecificOutput:{hookEventName:"UserPromptSubmit",additionalContext:$ctx}}'
fi

exit 0
