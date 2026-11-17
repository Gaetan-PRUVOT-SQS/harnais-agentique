#!/usr/bin/env python3
"""QA dataset runner and auto-correction API.

Loads regression cases from qa_dataset/fixtures.json, applies audit fixes,
and validates expected outcomes.

Usage:
    python qa_fix.py                  # run all fixture cases, write qa_dataset/report.json
    python qa_fix.py --case fix.system
"""
from __future__ import annotations

import argparse
import copy
import json
import os
from typing import Any

from audit import CANONICAL_SYSTEM, audit_record, process_record

BASE = os.path.dirname(os.path.abspath(__file__))
QA_DATASET = os.path.join(BASE, "qa_dataset")
FIXTURES_PATH = os.path.join(QA_DATASET, "fixtures.json")
REPORT_PATH = os.path.join(QA_DATASET, "report.json")
CORRECTED_PATH = os.path.join(QA_DATASET, "corrected.jsonl")


def _substitute_canonical(obj: Any) -> Any:
    if isinstance(obj, str):
        return obj.replace("__CANONICAL__", CANONICAL_SYSTEM)
    if isinstance(obj, list):
        return [_substitute_canonical(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _substitute_canonical(v) for k, v in obj.items()}
    return obj


def load_fixtures(path: str = FIXTURES_PATH) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError("fixtures.json must be a JSON array")
    return _substitute_canonical(data)


def _roles(rec: dict[str, Any]) -> list[str]:
    return [m.get("role") for m in rec.get("messages", []) if isinstance(m, dict)]


def _content(rec: dict[str, Any], role: str) -> str:
    for m in rec.get("messages", []):
        if m.get("role") == role:
            return m.get("content", "")
    return ""


def _check_assertions(rec: dict[str, Any], assertions: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if assertions.get("system_equals_canonical"):
        if _content(rec, "system") != CANONICAL_SYSTEM:
            errors.append("system prompt is not canonical")

    for role in ("user", "assistant"):
        text = _content(rec, role)
        for needle in assertions.get(f"{role}_contains", []):
            if needle not in text:
                errors.append(f"{role} missing substring: {needle!r}")
        for needle in assertions.get(f"{role}_not_contains", []):
            if needle in text:
                errors.append(f"{role} still contains forbidden substring: {needle!r}")

    expected_roles = assertions.get("roles_order")
    if expected_roles and _roles(rec)[: len(expected_roles)] != expected_roles:
        errors.append(f"role order {_roles(rec)} != {expected_roles}")

    for rule in assertions.get("finding_rules", []):
        found = {f.rule_id for f in audit_record(rec)}
        if rule not in found:
            errors.append(f"expected finding rule missing: {rule}")

    for rule in assertions.get("no_finding_rules", []):
        found = {f.rule_id for f in audit_record(rec)}
        if rule in found:
            errors.append(f"unexpected finding rule present: {rule}")

    return errors


def run_fixture(case: dict[str, Any], *, apply_fix: bool = True) -> dict[str, Any]:
    """Execute one QA dataset case and return pass/fail details."""
    case_id = case["id"]
    input_rec = copy.deepcopy(case["input"])
    expected_quarantine = case.get("quarantine", False)
    expected_fixes = set(case.get("expected_fixes", []))
    assertions = case.get("assertions", {})

    if apply_fix and not case.get("skip_fix", False):
        outcome = process_record(input_rec, fix=True)
        output_rec = outcome.record
        quarantine = outcome.quarantine
        fixes = set(outcome.fixes_applied)
    else:
        outcome = process_record(input_rec, fix=False)
        output_rec = input_rec
        quarantine = outcome.quarantine
        fixes = set()

    errors: list[str] = []
    if quarantine != expected_quarantine:
        errors.append(f"quarantine={quarantine}, expected={expected_quarantine}")

    if expected_fixes and not expected_fixes.issubset(fixes):
        missing = sorted(expected_fixes - fixes)
        errors.append(f"missing expected fixes: {missing}")

    if not expected_quarantine:
        errors.extend(_check_assertions(output_rec, assertions))

    return {
        "id": case_id,
        "rule": case.get("rule"),
        "passed": not errors,
        "errors": errors,
        "quarantine": quarantine,
        "fixes_applied": sorted(fixes),
        "output": output_rec if not expected_quarantine else None,
    }


def run_all_fixtures(
    path: str = FIXTURES_PATH,
    *,
    apply_fix: bool = True,
    report_path: str = REPORT_PATH,
    corrected_path: str = CORRECTED_PATH,
) -> dict[str, Any]:
    os.makedirs(QA_DATASET, exist_ok=True)
    cases = load_fixtures(path)
    results = [run_fixture(case, apply_fix=apply_fix) for case in cases]
    passed = sum(1 for r in results if r["passed"])
    failed = [r for r in results if not r["passed"]]

    with open(corrected_path, "w", encoding="utf-8") as fh:
        for r in results:
            if r.get("output"):
                fh.write(
                    json.dumps(
                        {"id": r["id"], "rule": r["rule"], "record": r["output"]},
                        ensure_ascii=False,
                    )
                    + "\n"
                )

    report = {
        "fixtures_path": path,
        "total": len(cases),
        "passed": passed,
        "failed": len(failed),
        "pass_rate": round(100 * passed / len(cases), 1) if cases else 100.0,
        "failures": failed,
        "corrected_path": corrected_path,
    }
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run QA dataset fixture suite")
    parser.add_argument("--case", help="Run a single fixture id")
    parser.add_argument("--no-fix", action="store_true", help="Audit only, do not apply fixes")
    parser.add_argument("--report", default=REPORT_PATH)
    args = parser.parse_args()

    if args.case:
        cases = [c for c in load_fixtures() if c["id"] == args.case]
        if not cases:
            raise SystemExit(f"Unknown case id: {args.case}")
        result = run_fixture(cases[0], apply_fix=not args.no_fix)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        raise SystemExit(0 if result["passed"] else 1)

    report = run_all_fixtures(apply_fix=not args.no_fix, report_path=args.report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["failed"] == 0 else 1)


if __name__ == "__main__":
    main()