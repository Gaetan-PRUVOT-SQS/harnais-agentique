#!/usr/bin/env python3
"""Scaffold a new SFT dataset project from skill-embedded templates.

Self-contained: copies only from the skill's templates/ folder.

Usage:
    python3 scaffold.py --name my-ft-dataset --output ~/Bureau/my-ft-dataset
    python3 scaffold.py --name backend-ft --output ./backend-ft \
        --system "You are a senior backend engineer..."
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES = os.path.join(SKILL_ROOT, "templates")


def scaffold(
    name: str,
    output: str,
    *,
    system_prompt: str | None = None,
    target_model: str | None = None,
    target_examples: int | None = None,
) -> None:
    if not os.path.isdir(TEMPLATES):
        print(f"Templates not found: {TEMPLATES}", file=sys.stderr)
        sys.exit(1)

    output = os.path.expanduser(output)
    if os.path.exists(output) and os.listdir(output):
        print(f"Output directory not empty: {output}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(output, exist_ok=True)

    for entry in os.listdir(TEMPLATES):
        src = os.path.join(TEMPLATES, entry)
        dst = os.path.join(output, entry)
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

    os.makedirs(os.path.join(output, "shards"), exist_ok=True)

    cfg_path = os.path.join(output, "config.json")
    with open(cfg_path, encoding="utf-8") as fh:
        cfg = json.load(fh)

    cfg["project_name"] = name
    if system_prompt:
        cfg["canonical_system"] = system_prompt
    if target_model:
        cfg["target_model"] = target_model
    if target_examples:
        cfg["target_examples"] = target_examples

    with open(cfg_path, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    readme = f"""# {name}

SFT chat dataset — scaffolded via `sft-dataset-pipeline` skill.

## Workflow

1. Edit `config.json` (persona, taxonomy, target model, volume)
2. Define topics in `config.json` → `taxonomy.topics`
3. Generate `shards/shard_NNN.jsonl` (one shard per taxonomy cell)
4. `python3 build.py`
5. `python3 benchmark.py`
6. `.venv/bin/python tokenizer_check.py` (after `pip install transformers`)

## Config-driven

`canonical_system`, `target_model`, split ratio, and gates all read from `config.json`.
Fixtures use `__CANONICAL__` — resolved automatically at test time.
"""
    with open(os.path.join(output, "README.md"), "w", encoding="utf-8") as fh:
        fh.write(readme)

    print(json.dumps({"ok": True, "output": output, "templates": TEMPLATES}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Scaffold SFT dataset from skill templates")
    parser.add_argument("--name", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--system", default=None, help="canonical_system in config.json")
    parser.add_argument("--model", default=None, help="target_model in config.json")
    parser.add_argument("--examples", type=int, default=None, help="target_examples in config.json")
    args = parser.parse_args()
    scaffold(
        args.name,
        args.output,
        system_prompt=args.system,
        target_model=args.model,
        target_examples=args.examples,
    )


if __name__ == "__main__":
    main()