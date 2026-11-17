#!/usr/bin/env python3
"""Benchmark the SFT dataset pipeline, QA suite, and dataset quality.

Usage:
    python benchmark.py
    python benchmark.py --json   # machine-readable only
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import time
from typing import Any

BASE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def _run(cmd: list[str], cwd: str = BASE) -> tuple[float, int, str]:
    t0 = time.perf_counter()
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    elapsed = time.perf_counter() - t0
    out = (proc.stdout or "") + (proc.stderr or "")
    return elapsed, proc.returncode, out.strip()


def _file_size(path: str) -> int:
    return os.path.getsize(path) if os.path.exists(path) else 0


def _load_jsonl(path: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _chars_words(rec: dict[str, Any]) -> tuple[int, int, dict[str, int]]:
    per_role: dict[str, int] = {}
    total_chars = 0
    total_words = 0
    for m in rec.get("messages", []):
        text = m.get("content", "") or ""
        c = len(text)
        w = len(text.split())
        per_role[m.get("role", "?")] = per_role.get(m.get("role", "?"), 0) + c
        total_chars += c
        total_words += w
    return total_chars, total_words, per_role


def _estimate_tokens(chars: int) -> int:
    # rough chars/4 heuristic for English+code mixed SFT data
    return max(1, round(chars / 4))


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    k = (len(ordered) - 1) * (p / 100)
    f = int(k)
    c = min(f + 1, len(ordered) - 1)
    if f == c:
        return ordered[f]
    return ordered[f] + (ordered[c] - ordered[f]) * (k - f)


def dataset_metrics() -> dict[str, Any]:
    train = _load_jsonl(os.path.join(BASE, "train.jsonl"))
    val = _load_jsonl(os.path.join(BASE, "val.jsonl"))
    all_rows = train + val

    chars, words, assistant_chars, user_chars = [], [], [], []
    code_blocks = 0
    langs = {"fr": 0, "en": 0}

    from build import detect_lang, first_user

    for rec in all_rows:
        tc, tw, per = _chars_words(rec)
        chars.append(tc)
        words.append(tw)
        assistant_chars.append(per.get("assistant", 0))
        user_chars.append(per.get("user", 0))
        asst = next((m["content"] for m in rec["messages"] if m["role"] == "assistant"), "")
        code_blocks += asst.count("```") // 2
        langs[detect_lang(first_user(rec))] += 1

    total_chars = sum(chars)
    total_words = sum(words)

    return {
        "examples": {"train": len(train), "val": len(val), "total": len(all_rows)},
        "bytes": {
            "train": _file_size(os.path.join(BASE, "train.jsonl")),
            "val": _file_size(os.path.join(BASE, "val.jsonl")),
            "shards_dir": sum(
                _file_size(os.path.join(BASE, "shards", f))
                for f in os.listdir(os.path.join(BASE, "shards"))
                if f.endswith(".jsonl")
            ),
        },
        "chars": {
            "total": total_chars,
            "mean": round(statistics.mean(chars), 1),
            "median": round(statistics.median(chars), 1),
            "p95": round(_percentile(chars, 95), 1),
            "max": max(chars) if chars else 0,
        },
        "words": {
            "total": total_words,
            "mean": round(statistics.mean(words), 1),
            "median": round(statistics.median(words), 1),
        },
        "assistant_chars": {
            "mean": round(statistics.mean(assistant_chars), 1),
            "median": round(statistics.median(assistant_chars), 1),
            "p95": round(_percentile(assistant_chars, 95), 1),
        },
        "user_chars": {
            "mean": round(statistics.mean(user_chars), 1),
            "median": round(statistics.median(user_chars), 1),
        },
        "tokens_estimated": {
            "total": _estimate_tokens(total_chars),
            "mean_per_example": round(_estimate_tokens(total_chars) / max(len(all_rows), 1), 1),
            "train": _estimate_tokens(sum(chars[: len(train)])) if train else 0,
            "val": _estimate_tokens(sum(chars[len(train) :])) if val else 0,
        },
        "code_blocks_total": code_blocks,
        "code_blocks_per_example": round(code_blocks / max(len(all_rows), 1), 2),
        "language_estimate": langs,
        "language_fr_pct": round(100 * langs["fr"] / max(len(all_rows), 1), 1),
    }


def qa_metrics() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name in ("stats.json", "qa_report.json"):
        path = os.path.join(BASE, name)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                out[name.replace(".json", "")] = json.load(fh)

    fixtures_report = os.path.join(BASE, "qa_dataset", "report.json")
    if os.path.exists(fixtures_report):
        with open(fixtures_report, encoding="utf-8") as fh:
            out["qa_fixtures"] = json.load(fh)

    quarantine = os.path.join(BASE, "quarantine.jsonl")
    q_count = 0
    if os.path.exists(quarantine):
        with open(quarantine, encoding="utf-8") as fh:
            q_count = sum(1 for line in fh if line.strip())
    out["quarantine_lines"] = q_count
    return out


def benchmark_pipeline() -> dict[str, Any]:
    stages: dict[str, Any] = {}

    cases = [
        ("qa_fix", [PY, "qa_fix.py"]),
        ("audit_check_only", [PY, "audit.py", "--check-only"]),
        ("unit_tests", [PY, "-m", "unittest", "test_qa.TestLanguageDetection", "test_qa.TestAuditRules", "test_qa.TestAutoFix", "test_qa.TestShardAuditIntegration", "test_qa.TestQADatasetFixtures"]),
        ("dataset_gates", [PY, "-m", "unittest", "test_qa.TestDatasetGates"]),
    ]

    for name, cmd in cases:
        elapsed, code, _ = _run(cmd)
        stages[name] = {"seconds": round(elapsed, 3), "ok": code == 0}

    # Full build is heavy (re-audits shards); time audit+concat path separately
    t0 = time.perf_counter()
    from audit import audit_shards

    audit_shards(
        os.path.join(BASE, "shards"),
        fix=False,
        report_path=os.path.join(BASE, ".bench_qa_report.json"),
        quarantine_path=os.path.join(BASE, ".bench_quarantine.jsonl"),
    )
    stages["audit_shards_scan"] = {"seconds": round(time.perf_counter() - t0, 3), "ok": True}

    for tmp in (".bench_qa_report.json", ".bench_quarantine.jsonl"):
        p = os.path.join(BASE, tmp)
        if os.path.exists(p):
            os.remove(p)

    total = sum(s["seconds"] for s in stages.values())
    stages["pipeline_total_estimated"] = {"seconds": round(total, 3)}

    return stages


def benchmark() -> dict[str, Any]:
    t0 = time.perf_counter()
    pipeline = benchmark_pipeline()
    dataset = dataset_metrics()
    qa = qa_metrics()
    elapsed = time.perf_counter() - t0

    return {
        "benchmark_version": 1,
        "elapsed_seconds": round(elapsed, 3),
        "pipeline": pipeline,
        "dataset": dataset,
        "qa": qa,
        "summary": {
            "health_score": qa.get("stats", {}).get("qa_health_score"),
            "examples_total": dataset["examples"]["total"],
            "tokens_estimated_total": dataset["tokens_estimated"]["total"],
            "fr_pct": dataset["language_fr_pct"],
            "fixture_pass_rate": qa.get("qa_fixtures", {}).get("pass_rate"),
            "pipeline_ok": all(s.get("ok", False) for s in pipeline.values() if isinstance(s, dict) and "ok" in s),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark SFT dataset pipeline")
    parser.add_argument("--json", action="store_true", help="Print JSON only")
    parser.add_argument("--out", default=os.path.join(BASE, "benchmark_report.json"))
    args = parser.parse_args()

    report = benchmark()
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    s = report["summary"]
    d = report["dataset"]
    p = report["pipeline"]
    qa = report["qa"]

    print("=" * 60)
    name = "SFT-DATASET"
    cfg_path = os.path.join(BASE, "config.json")
    if os.path.exists(cfg_path):
        with open(cfg_path, encoding="utf-8") as fh:
            name = json.load(fh).get("project_name", name).upper()
    print(f"{name} BENCHMARK")
    print("=" * 60)
    print()
    print("## Pipeline (seconds)")
    for name, data in p.items():
        if name == "pipeline_total_estimated":
            continue
        status = "OK" if data.get("ok") else "FAIL"
        print(f"  {name:<24} {data['seconds']:>7.3f}s  [{status}]")
    print(f"  {'TOTAL (est.)':<24} {p['pipeline_total_estimated']['seconds']:>7.3f}s")
    print()
    print("## Dataset")
    print(f"  Examples        train={d['examples']['train']}  val={d['examples']['val']}  total={d['examples']['total']}")
    print(f"  Size            train={d['bytes']['train']/1e6:.2f} MB  val={d['bytes']['val']/1e6:.2f} MB  shards={d['bytes']['shards_dir']/1e6:.2f} MB")
    print(f"  Chars/example   mean={d['chars']['mean']}  median={d['chars']['median']}  p95={d['chars']['p95']}  max={d['chars']['max']}")
    print(f"  Tokens (est.)   total={d['tokens_estimated']['total']:,}  mean/ex={d['tokens_estimated']['mean_per_example']}")
    print(f"  Code blocks     total={d['code_blocks_total']}  per_ex={d['code_blocks_per_example']}")
    print(f"  Language        FR={d['language_estimate']['fr']} ({d['language_fr_pct']}%)  EN={d['language_estimate']['en']}")
    print()
    print("## QA")
    print(f"  Health score    {s['health_score']}%")
    print(f"  Fixture pass    {s['fixture_pass_rate']}% ({qa.get('qa_fixtures', {}).get('passed', '?')}/{qa.get('qa_fixtures', {}).get('total', '?')})")
    print(f"  Quarantined     {qa.get('quarantine_lines', 0)}")
    print(f"  Pipeline OK     {s['pipeline_ok']}")
    print()
    print(f"Report → {args.out}  ({report['elapsed_seconds']}s)")


if __name__ == "__main__":
    main()