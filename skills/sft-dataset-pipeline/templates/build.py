#!/usr/bin/env python3
"""Build an SFT chat dataset from generated shards.

QA audit + auto-fix shards -> concatenate -> validate JSON ->
dedup by normalized first user turn -> deterministic shuffle ->
train/val split -> write stats.json + qa_report.json.
"""
import json
import glob
import os
import re
import hashlib
import random

from audit import audit_shards, load_config
from qa_fix import run_all_fixtures
from test_qa import run_dataset_gates, run_unit_tests, validate_jsonl

BASE = os.path.dirname(os.path.abspath(__file__))
SHARDS = os.path.join(BASE, "shards")
_CFG = load_config()
SEED = _CFG.get("shuffle_seed", 1337)
SPLIT_RATIO = _CFG.get("split_ratio", 0.95)


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def first_user(rec):
    for m in rec.get("messages", []):
        if m.get("role") == "user":
            return m.get("content", "")
    return ""


def detect_lang(text: str) -> str:
    t = " " + norm(text) + " "
    fr_markers = [" le ", " la ", " les ", " un ", " une ", " des ", " je ", " mon ",
                  " comment ", " pourquoi ", " avec ", " pour ", " dans ", " est ",
                  " fonctionne ", " erreur ", " peux-tu ", " voici ", " quand ", " que "]
    score = sum(1 for mk in fr_markers if mk in t)
    return "fr" if score >= 2 else "en"


def main():
    if not run_unit_tests(verbosity=1):
        raise SystemExit(1)

    fixture_report = run_all_fixtures()
    if fixture_report["failed"]:
        print(json.dumps({"qa_fixture_failures": fixture_report["failures"]}, ensure_ascii=False, indent=2))
        raise SystemExit(1)

    qa = audit_shards(
        SHARDS,
        fix=True,
        report_path=os.path.join(BASE, "qa_report.json"),
        quarantine_path=os.path.join(BASE, "quarantine.jsonl"),
    )

    files = sorted(glob.glob(os.path.join(SHARDS, "shard_*.jsonl")))
    raw, invalid = [], 0
    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if not rec.get("messages"):
                        invalid += 1
                        continue
                    # require at least one user + one assistant turn
                    roles = [m.get("role") for m in rec["messages"]]
                    if "user" not in roles or "assistant" not in roles:
                        invalid += 1
                        continue
                    raw.append(rec)
                except json.JSONDecodeError:
                    invalid += 1

    # dedup by normalized first user turn
    seen, deduped = set(), []
    for rec in raw:
        h = hashlib.sha1(norm(first_user(rec)).encode("utf-8")).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        deduped.append(rec)

    rng = random.Random(SEED)
    rng.shuffle(deduped)

    n_val = max(1, round(len(deduped) * (1 - SPLIT_RATIO)))
    val, train = deduped[:n_val], deduped[n_val:]

    def write_jsonl(path, recs):
        with open(path, "w", encoding="utf-8") as fh:
            for r in recs:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    train_path = os.path.join(BASE, "train.jsonl")
    val_path = os.path.join(BASE, "val.jsonl")
    write_jsonl(train_path, train)
    write_jsonl(val_path, val)

    gate_errors = validate_jsonl(train_path) + validate_jsonl(val_path)
    if gate_errors:
        print(json.dumps({"qa_gate_errors": gate_errors[:20]}, ensure_ascii=False, indent=2))
        raise SystemExit(1)

    if not run_dataset_gates(verbosity=1):
        raise SystemExit(1)

    langs = {"fr": 0, "en": 0}
    for r in deduped:
        langs[detect_lang(first_user(r))] += 1

    stats = {
        "shards": len(files),
        "raw_lines": len(raw),
        "invalid_lines": invalid,
        "after_dedup": len(deduped),
        "duplicates_removed": len(raw) - len(deduped),
        "train": len(train),
        "val": len(val),
        "lang_estimate": langs,
        "format": "chat (messages: system/user/assistant)",
        "seed": SEED,
        "qa_health_score": qa.get("health_score"),
        "qa_quarantined": qa.get("lines_quarantined", 0),
        "qa_fixes_applied": sum(qa.get("fixes_applied", {}).values()),
        "qa_unit_tests_passed": True,
        "qa_fixture_cases_passed": fixture_report["passed"],
        "qa_fixture_total": fixture_report["total"],
        "qa_dataset_gates_passed": True,
    }
    with open(os.path.join(BASE, "stats.json"), "w", encoding="utf-8") as fh:
        json.dump(stats, fh, ensure_ascii=False, indent=2)

    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
