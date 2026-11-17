#!/usr/bin/env python3
"""QA test suite for the SFT dataset pipeline.

Unit-tests audit rules and auto-fixes, plus integration gates on built JSONL.

Run:
    python -m unittest test_qa.py -v
    python test_qa.py              # same, verbose
"""
from __future__ import annotations

import json
import os
import shutil
import unittest

from audit import (
    CANONICAL_SYSTEM,
    SEVERITY_ERROR,
    audit_record,
    audit_shards,
    detect_lang,
    process_record,
)
from qa_fix import load_fixtures, run_all_fixtures, run_fixture

BASE = os.path.dirname(os.path.abspath(__file__))


def _record(
    user: str = "How do I use useState?",
    assistant: str | None = None,
    system: str | None = None,
    roles_order: list[str] | None = None,
) -> dict:
    assistant = assistant or (
        "Here is a minimal example.\n\n"
        "```tsx\n"
        "'use client';\n"
        "import { useState } from 'react';\n"
        "export function Counter() {\n"
        "  const [n, setN] = useState(0);\n"
        "  return <button onClick={() => setN(n + 1)}>{n}</button>;\n"
        "}\n"
        "```"
    )
    system = system if system is not None else CANONICAL_SYSTEM
    if roles_order:
        msgs = []
        content = {"system": system, "user": user, "assistant": assistant}
        for role in roles_order:
            msgs.append({"role": role, "content": content[role]})  # type: ignore[index]
        return {"messages": msgs}
    return {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
            {"role": "assistant", "content": assistant},
        ]
    }


def validate_jsonl(path: str) -> list[str]:
    """Return list of QA errors for a built JSONL file."""
    errors: list[str] = []
    if not os.path.exists(path):
        return [f"missing file: {path}"]

    with open(path, encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"{path}:{line_no} invalid json: {exc}")
                continue

            outcome = process_record(rec, fix=False)
            if outcome.quarantine:
                rules = [f.rule_id for f in outcome.findings if f.severity == SEVERITY_ERROR]
                errors.append(f"{path}:{line_no} quarantine rules={rules}")

            roles = [m.get("role") for m in rec.get("messages", [])]
            if roles[:3] != ["system", "user", "assistant"]:
                errors.append(f"{path}:{line_no} bad role order: {roles[:3]}")

            sys_content = next(
                (m.get("content") for m in rec.get("messages", []) if m.get("role") == "system"),
                None,
            )
            if sys_content != CANONICAL_SYSTEM:
                errors.append(f"{path}:{line_no} non-canonical system prompt")

    return errors


class TestLanguageDetection(unittest.TestCase):
    def test_french_high_confidence(self):
        lang, conf = detect_lang("Comment puis-je créer un composant réutilisable avec TypeScript ?")
        self.assertEqual(lang, "fr")
        self.assertIn(conf, ("high", "medium"))

    def test_english_high_confidence(self):
        lang, conf = detect_lang("How can I create a reusable component with TypeScript?")
        self.assertEqual(lang, "en")
        self.assertIn(conf, ("high", "medium"))


class TestAuditRules(unittest.TestCase):
    def test_valid_record_has_no_errors(self):
        findings = audit_record(_record())
        errors = [f for f in findings if f.severity == SEVERITY_ERROR]
        self.assertEqual(errors, [])

    def test_detects_broken_placeholder(self):
        rec = _record(assistant="Use this snippet:\n```tsx\n// ...rest of the component\n```")
        rules = [f.rule_id for f in audit_record(rec)]
        self.assertIn("content.broken_placeholder", rules)

    def test_detects_lang_mismatch_high_confidence(self):
        rec = _record(
            user="Comment puis-je créer un composant réutilisable avec mon équipe ?",
            assistant="Sure! Here is how you build a reusable component with TypeScript and React.",
        )
        rules = [f.rule_id for f in audit_record(rec)]
        self.assertIn("i18n.lang_mismatch", rules)

    def test_detects_unbalanced_fence(self):
        rec = _record(assistant="Example:\n```tsx\nconst x = 1;\n")
        rules = [f.rule_id for f in audit_record(rec)]
        self.assertIn("markdown.unbalanced_fence", rules)

    def test_detects_ellipsis_shorthand(self):
        rec = _record(
            assistant=(
                "Here is the pattern with a lazy ellipsis line that should be cleaned.\n\n"
                "```tsx\nconst x = 1;\n// ...\nconst y = 2;\n```\n\n"
                "Remove the ellipsis line so the snippet stays copy-pasteable."
            )
        )
        rules = [f.rule_id for f in audit_record(rec)]
        self.assertIn("content.ellipsis_shorthand", rules)


class TestAutoFix(unittest.TestCase):
    def test_fixes_non_canonical_system(self):
        rec = _record(system="You are a helpful assistant.")
        outcome = process_record(rec, fix=True)
        sys_msg = outcome.record["messages"][0]["content"]
        self.assertEqual(sys_msg, CANONICAL_SYSTEM)
        self.assertIn("prompt.canonical_system", outcome.fixes_applied)

    def test_fixes_html_entities(self):
        rec = _record(user="Why &amp; how?", assistant="Use &lt;div&gt; here.\n\n```tsx\n<div />\n```")
        outcome = process_record(rec, fix=True)
        self.assertNotIn("&amp;", outcome.record["messages"][1]["content"])
        self.assertNotIn("&lt;", outcome.record["messages"][2]["content"])

    def test_fixes_unbalanced_fence(self):
        rec = _record(
            assistant=(
                "Open fence without a close — the audit should append the missing fence.\n\n"
                "```tsx\nconst x = 1;\n"
            )
        )
        outcome = process_record(rec, fix=True)
        content = outcome.record["messages"][2]["content"]
        self.assertEqual(content.count("```") % 2, 0)
        self.assertFalse(outcome.quarantine)

    def test_fixes_ellipsis_in_code(self):
        rec = _record(
            assistant=(
                "The ellipsis line is only scaffolding; remove it from the fenced block.\n\n"
                "```tsx\nconst a = 1;\n// ...\nconst b = 2;\n```\n\n"
                "After cleanup the snippet should still compile."
            )
        )
        outcome = process_record(rec, fix=True)
        content = outcome.record["messages"][2]["content"]
        self.assertNotIn("// ...", content)
        self.assertIn("content.expand_ellipsis", outcome.fixes_applied)
        self.assertFalse(outcome.quarantine)

    def test_fixes_role_order(self):
        rec = _record(roles_order=["user", "assistant", "system"])
        outcome = process_record(rec, fix=True)
        roles = [m["role"] for m in outcome.record["messages"]]
        self.assertEqual(roles, ["system", "user", "assistant"])

    def test_quarantines_lang_mismatch(self):
        rec = _record(
            user="Comment puis-je créer un composant réutilisable avec mon équipe ?",
            assistant="Sure! Here is how you build a reusable component with TypeScript and React.",
        )
        outcome = process_record(rec, fix=True)
        self.assertTrue(outcome.quarantine)


class TestShardAuditIntegration(unittest.TestCase):
    def setUp(self):
        self.fixtures = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qa-fixtures")
        shutil.rmtree(self.fixtures, ignore_errors=True)
        os.makedirs(self.fixtures)
        self.shard = os.path.join(self.fixtures, "shard_000.jsonl")
        with open(self.shard, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(_record(), ensure_ascii=False) + "\n")
            bad = _record(
                assistant="```tsx\n// ...rest of the component\n```",
            )
            fh.write(json.dumps(bad, ensure_ascii=False) + "\n")

    def tearDown(self):
        shutil.rmtree(self.fixtures, ignore_errors=True)

    def test_audit_shards_fixes_and_quarantines(self):
        report = audit_shards(
            self.fixtures,
            fix=True,
            report_path=os.path.join(self.fixtures, "qa_report.json"),
            quarantine_path=os.path.join(self.fixtures, "quarantine.jsonl"),
        )
        self.assertEqual(report["lines_scanned"], 2)
        self.assertEqual(report["lines_kept"], 1)
        self.assertEqual(report["lines_quarantined"], 1)

        with open(self.shard, encoding="utf-8") as fh:
            kept = [json.loads(line) for line in fh if line.strip()]
        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0]["messages"][0]["content"], CANONICAL_SYSTEM)


class TestQADatasetFixtures(unittest.TestCase):
    """Regression suite driven by qa_dataset/fixtures.json."""

    @classmethod
    def setUpClass(cls):
        cls.fixtures = load_fixtures()

    def test_fixtures_file_not_empty(self):
        self.assertGreaterEqual(len(self.fixtures), 10)

    def test_all_fixture_cases_pass(self):
        report = run_all_fixtures()
        self.assertEqual(
            report["failed"],
            0,
            "\n".join(
                f"{f['id']}: {', '.join(f['errors'])}"
                for f in report.get("failures", [])
            ),
        )

    def test_each_fixture_individually(self):
        for case in self.fixtures:
            with self.subTest(case_id=case["id"]):
                result = run_fixture(case)
                self.assertTrue(result["passed"], result["errors"])


class TestDatasetGates(unittest.TestCase):
    """Post-build gates on train.jsonl / val.jsonl (skipped if not built yet)."""

    @classmethod
    def setUpClass(cls):
        cls.train = os.path.join(BASE, "train.jsonl")
        cls.val = os.path.join(BASE, "val.jsonl")
        cls.built = os.path.exists(cls.train) and os.path.exists(cls.val)

    def test_train_jsonl_passes_qa_gate(self):
        if not self.built:
            self.skipTest("train.jsonl not built yet")
        errors = validate_jsonl(self.train)
        self.assertEqual(errors, [], "\n".join(errors[:10]))

    def test_val_jsonl_passes_qa_gate(self):
        if not self.built:
            self.skipTest("val.jsonl not built yet")
        errors = validate_jsonl(self.val)
        self.assertEqual(errors, [], "\n".join(errors[:10]))

    def test_minimum_dataset_size(self):
        if not self.built:
            self.skipTest("dataset not built yet")
        with open(os.path.join(BASE, "config.json"), encoding="utf-8") as fh:
            cfg = json.load(fh)
        target = cfg.get("target_examples", 1000)
        split = cfg.get("split_ratio", 0.95)
        min_train = int(target * split * 0.85)
        min_val = max(1, int(target * (1 - split) * 0.5))
        with open(self.train, encoding="utf-8") as fh:
            n_train = sum(1 for line in fh if line.strip())
        with open(self.val, encoding="utf-8") as fh:
            n_val = sum(1 for line in fh if line.strip())
        self.assertGreaterEqual(n_train, min_train)
        self.assertGreaterEqual(n_val, min_val)


def _run_classes(classes: list[type], verbosity: int = 2) -> bool:
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for cls in classes:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    result = unittest.TextTestRunner(verbosity=verbosity).run(suite)
    return result.wasSuccessful()


def run_unit_tests(verbosity: int = 1) -> bool:
    """Rules, auto-fixes, and shard audit integration (no built dataset required)."""
    return _run_classes(
        [
            TestLanguageDetection,
            TestAuditRules,
            TestAutoFix,
            TestShardAuditIntegration,
            TestQADatasetFixtures,
        ],
        verbosity=verbosity,
    )


def run_dataset_gates(verbosity: int = 1) -> bool:
    """Post-build gates on train.jsonl / val.jsonl."""
    return _run_classes([TestDatasetGates], verbosity=verbosity)


def run_tests(verbosity: int = 2) -> bool:
    return run_unit_tests(verbosity=verbosity) and run_dataset_gates(verbosity=verbosity)


if __name__ == "__main__":
    raise SystemExit(0 if run_tests() else 1)