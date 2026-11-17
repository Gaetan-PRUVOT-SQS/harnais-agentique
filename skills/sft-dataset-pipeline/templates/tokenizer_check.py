#!/usr/bin/env python3
"""Token-length analysis for SFT datasets using the target model tokenizer.

Reads target model from config.json (default: google/gemma-4-E4B-it).

Usage:
    python tokenizer_check.py
    python tokenizer_check.py --model LiquidAI/LFM2.5-8B-A1B
    python tokenizer_check.py --limits 2048,4096,8192
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
from typing import Any

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE, "config.json")


def _default_model() -> str:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, encoding="utf-8") as fh:
            return json.load(fh).get("target_model", "google/gemma-4-E4B-it")
    return "google/gemma-4-E4B-it"


def _default_limits() -> list[int]:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, encoding="utf-8") as fh:
            return json.load(fh).get("tokenizer_limits", [2048, 4096, 8192, 32768])
    return [2048, 4096, 8192, 32768]


def _percentile(values: list[int], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    k = (len(ordered) - 1) * (p / 100)
    f = int(k)
    c = min(f + 1, len(ordered) - 1)
    if f == c:
        return ordered[f]
    return ordered[f] + (ordered[c] - ordered[f]) * (k - f)


def _load_rows() -> list[tuple[str, int, dict[str, Any]]]:
    rows: list[tuple[str, int, dict[str, Any]]] = []
    for split in ("train", "val"):
        path = os.path.join(BASE, f"{split}.jsonl")
        with open(path, encoding="utf-8") as fh:
            for line_no, line in enumerate(fh, 1):
                line = line.strip()
                if line:
                    rows.append((split, line_no, json.loads(line)))
    return rows


def _chat_text(tokenizer, messages: list[dict[str, str]]) -> str:
    if hasattr(tokenizer, "apply_chat_template"):
        try:
            return tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=False,
            )
        except Exception:
            pass
    parts = []
    for m in messages:
        parts.append(f"{m['role'].upper()}: {m['content']}")
    return "\n\n".join(parts)


def analyze(model_id: str, limits: list[int]) -> dict[str, Any]:
    from transformers import AutoConfig, AutoTokenizer

    config = AutoConfig.from_pretrained(model_id, trust_remote_code=True)
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)

    rows = _load_rows()
    per_example: list[dict[str, Any]] = []
    total_tokens: list[int] = []
    assistant_tokens: list[int] = []
    user_tokens: list[int] = []

    for split, line_no, rec in rows:
        messages = rec.get("messages", [])
        text = _chat_text(tokenizer, messages)
        ids = tokenizer.encode(text, add_special_tokens=True)
        n = len(ids)

        asst = next((m["content"] for m in messages if m.get("role") == "assistant"), "")
        usr = next((m["content"] for m in messages if m.get("role") == "user"), "")
        n_asst = len(tokenizer.encode(asst, add_special_tokens=False))
        n_usr = len(tokenizer.encode(usr, add_special_tokens=False))

        total_tokens.append(n)
        assistant_tokens.append(n_asst)
        user_tokens.append(n_usr)
        per_example.append(
            {
                "split": split,
                "line": line_no,
                "tokens_total": n,
                "tokens_user": n_usr,
                "tokens_assistant": n_asst,
            }
        )

    overflow: dict[str, Any] = {}
    for limit in limits:
        over = [x for x in total_tokens if x > limit]
        worst = sorted(per_example, key=lambda x: x["tokens_total"], reverse=True)[:5]
        overflow[str(limit)] = {
            "count": len(over),
            "pct": round(100 * len(over) / max(len(total_tokens), 1), 2),
            "worst_examples": [x for x in worst if x["tokens_total"] > limit][:3],
        }

    max_ctx = getattr(config, "max_position_embeddings", None)
    if max_ctx is None and hasattr(config, "text_config"):
        max_ctx = getattr(config.text_config, "max_position_embeddings", None)

    return {
        "model_id": model_id,
        "max_position_embeddings": max_ctx,
        "examples": len(rows),
        "tokens": {
            "total_sum": sum(total_tokens),
            "mean": round(statistics.mean(total_tokens), 1),
            "median": round(statistics.median(total_tokens), 1),
            "p95": round(_percentile(total_tokens, 95), 1),
            "p99": round(_percentile(total_tokens, 99), 1),
            "max": max(total_tokens) if total_tokens else 0,
            "min": min(total_tokens) if total_tokens else 0,
        },
        "assistant_tokens": {
            "mean": round(statistics.mean(assistant_tokens), 1),
            "median": round(statistics.median(assistant_tokens), 1),
            "p95": round(_percentile(assistant_tokens, 95), 1),
            "max": max(assistant_tokens) if assistant_tokens else 0,
        },
        "user_tokens": {
            "mean": round(statistics.mean(user_tokens), 1),
            "median": round(statistics.median(user_tokens), 1),
            "max": max(user_tokens) if user_tokens else 0,
        },
        "overflow_by_limit": overflow,
        "recommendation": _recommendation(total_tokens, limits, max_ctx),
    }


def _recommendation(tokens: list[int], limits: list[int], max_ctx: int | None) -> dict[str, Any]:
    p99 = _percentile(tokens, 99)
    safe_limits = [l for l in limits if _percentile(tokens, 99) <= l * 0.95]
    suggested = min(safe_limits) if safe_limits else max(limits)
    return {
        "p99_tokens": round(p99, 1),
        "suggested_max_seq_length": suggested,
        "fits_default_2048": round(100 * sum(1 for t in tokens if t <= 2048) / max(len(tokens), 1), 1),
        "fits_default_4096": round(100 * sum(1 for t in tokens if t <= 4096) / max(len(tokens), 1), 1),
        "model_max_context": max_ctx,
        "headroom_at_2048": round(2048 - statistics.mean(tokens), 1),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Tokenizer length check for SFT dataset")
    parser.add_argument("--model", default=_default_model())
    parser.add_argument("--limits", default=",".join(str(x) for x in _default_limits()))
    parser.add_argument("--out", default=os.path.join(BASE, "tokenizer_report.json"))
    args = parser.parse_args()
    limits = [int(x) for x in args.limits.split(",") if x.strip()]

    report = analyze(args.model, limits)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)

    t = report["tokens"]
    r = report["recommendation"]
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print()
    print("--- Summary ---")
    ctx = report["max_position_embeddings"]
    ctx_s = f"{ctx:,}" if ctx is not None else "n/a"
    print(f"Model: {report['model_id']} (max ctx {ctx_s})")
    print(f"Examples: {report['examples']}")
    print(f"Tokens/ex: mean={t['mean']} median={t['median']} p95={t['p95']} p99={t['p99']} max={t['max']}")
    print(f"Fits 2048: {r['fits_default_2048']}%  |  4096: {r['fits_default_4096']}%")
    print(f"Suggested max_seq_length: {r['suggested_max_seq_length']}")


if __name__ == "__main__":
    main()