#!/usr/bin/env python3
"""QA audit and automatic correction for SFT chat datasets.

Scans shards (or JSONL records), applies deterministic fixes in place, and
quarantines examples that still fail critical checks.

Integrated into build.py; can also run standalone:

    python audit.py              # audit + fix shards, write qa_report.json
    python audit.py --check-only # audit without writing fixed shards
"""
from __future__ import annotations

import argparse
import glob
import html
import json
import os
import re
from dataclasses import dataclass, field
from typing import Any

BASE = os.path.dirname(os.path.abspath(__file__))
SHARDS = os.path.join(BASE, "shards")
CONFIG_PATH = os.path.join(BASE, "config.json")


def load_config() -> dict[str, Any]:
    with open(CONFIG_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def get_canonical_system() -> str:
    return load_config().get("canonical_system", "You are a helpful assistant.")


CANONICAL_SYSTEM = get_canonical_system()

SEVERITY_ERROR = "error"
SEVERITY_WARN = "warning"
SEVERITY_INFO = "info"

BROKEN_PLACEHOLDER_RE = re.compile(
    r"(?:"
    r"\.\.\.\s*(?:rest of|omitted|truncated|your code)|"
    r"\[insert(?:\s+code)?\]|<insert|<your[\s_-]?code[\s_-]?here>|"
    r"lorem ipsum|TODO:\s*implement|FIXME:\s*implement"
    r")",
    re.IGNORECASE,
)

ELLIPSIS_LINE_RE = re.compile(r"^\s*//\s*\.\.\.\s*$", re.MULTILINE)
ELLIPSIS_JSX_RE = re.compile(r"^\s*\{/\*\s*\.\.\.\s*\*/\}\s*$", re.MULTILINE)
INLINE_ELLIPSIS_RE = re.compile(r"/\*\s*\.\.\.\s*\*/")

CODE_REQUEST_RE = re.compile(
    r"\b(show me|write|create|implement|give me|can you|peux-tu|écris|crée|montre|exemple|example|snippet|code)\b",
    re.IGNORECASE,
)

FR_MARKERS = [
    r"\bje\b", r"\bmon\b", r"\bma\b", r"\bmes\b", r"\bcomment\b", r"\bpourquoi\b",
    r"\bpeux-tu\b", r"\bvoici\b", r"\bc'est\b", r"\bqu'", r"\bdébut", r"\bavec\b",
    r"\bpour\b", r"\bdans\b", r"\berreur\b", r"\bcomposant\b", r"\bnotre\b",
    r"\bjeu\b", r"\bchez\b", r"\btrès\b", r"\bça\b", r"\bêtre\b", r"\bavoir\b",
]
EN_MARKERS = [
    r"\bthe\b", r"\bmy\b", r"\bhow\b", r"\bwhy\b", r"\bcan you\b", r"\bhere's\b",
    r"\bwhat's\b", r"\bcomponent\b", r"\berror\b", r"\bwith\b", r"\bfor\b",
    r"\bour\b", r"\bthis\b", r"\bwhen\b", r"\bshould\b", r"\bplease\b",
]
ACCENT_RE = re.compile(r"[àâäéèêëïîôùûüç]", re.IGNORECASE)


@dataclass
class Finding:
    rule_id: str
    severity: str
    message: str
    auto_fixable: bool = False


@dataclass
class AuditOutcome:
    record: dict[str, Any]
    findings: list[Finding] = field(default_factory=list)
    fixes_applied: list[str] = field(default_factory=list)
    quarantine: bool = False

    @property
    def has_error(self) -> bool:
        return any(f.severity == SEVERITY_ERROR for f in self.findings)


def _lang_scores(text: str) -> tuple[int, int]:
    t = " " + re.sub(r"\s+", " ", (text or "").lower()) + " "
    fr = sum(1 for m in FR_MARKERS if re.search(m, t))
    en = sum(1 for m in EN_MARKERS if re.search(m, t))
    if ACCENT_RE.search(text or ""):
        fr += 2
    return fr, en


def detect_lang(text: str) -> tuple[str, str]:
    """Return (lang, confidence) where confidence is high|medium|low."""
    fr, en = _lang_scores(text)
    if fr >= 3 and en <= 1:
        return "fr", "high"
    if en >= 3 and fr <= 1:
        return "en", "high"
    if fr >= 2 and fr > en + 1:
        return "fr", "medium"
    if en >= 2 and en > fr + 1:
        return "en", "medium"
    if fr > en:
        return "fr", "low"
    if en > fr:
        return "en", "low"
    return "mixed", "low"


def _get_roles(rec: dict[str, Any]) -> dict[str, str | None]:
    msgs = rec.get("messages") or []
    out: dict[str, str | None] = {"system": None, "user": None, "assistant": None}
    for m in msgs:
        role = m.get("role")
        if role in out and out[role] is None:
            out[role] = m.get("content", "")
    return out


def audit_record(rec: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    msgs = rec.get("messages")

    if not isinstance(msgs, list) or not msgs:
        findings.append(Finding("structure.empty_messages", SEVERITY_ERROR, "Missing messages array"))
        return findings

    roles = [m.get("role") for m in msgs if isinstance(m, dict)]
    for required in ("system", "user", "assistant"):
        if required not in roles:
            findings.append(
                Finding("structure.missing_role", SEVERITY_ERROR, f"Missing role: {required}", True)
            )

    content = _get_roles(rec)
    for role, text in content.items():
        if text is None:
            continue
        if not str(text).strip():
            findings.append(
                Finding(f"content.empty_{role}", SEVERITY_ERROR, f"Empty {role} content")
            )

    if content["system"] and content["system"].strip() != CANONICAL_SYSTEM:
        findings.append(
            Finding("prompt.non_canonical_system", SEVERITY_WARN, "System prompt differs from canonical", True)
        )

    if roles[:3] != ["system", "user", "assistant"] and all(r in roles for r in ("system", "user", "assistant")):
        findings.append(
            Finding("structure.role_order", SEVERITY_WARN, "Messages not in system→user→assistant order", True)
        )

    for role, text in content.items():
        if not text:
            continue
        if re.search(r"&(?:amp|lt|gt|quot|#39);", text):
            findings.append(
                Finding("content.html_entities", SEVERITY_WARN, f"HTML entities in {role} content", True)
            )
        if text != text.strip():
            findings.append(
                Finding("content.trim_whitespace", SEVERITY_INFO, f"Leading/trailing whitespace in {role}", True)
            )

    user, assistant = content.get("user") or "", content.get("assistant") or ""

    if assistant:
        fences = assistant.count("```")
        if fences % 2 != 0:
            findings.append(
                Finding("markdown.unbalanced_fence", SEVERITY_ERROR, "Unbalanced code fences in assistant", True)
            )
        if len(assistant) < 80:
            findings.append(
                Finding("content.assistant_too_short", SEVERITY_ERROR, "Assistant response too short (<80 chars)")
            )
        elif len(assistant) < 180:
            findings.append(
                Finding("content.assistant_short", SEVERITY_WARN, "Assistant response short (<180 chars)")
            )
        if BROKEN_PLACEHOLDER_RE.search(assistant):
            findings.append(
                Finding("content.broken_placeholder", SEVERITY_ERROR, "Broken placeholder in assistant response")
            )
        if (
            ELLIPSIS_LINE_RE.search(assistant)
            or ELLIPSIS_JSX_RE.search(assistant)
            or INLINE_ELLIPSIS_RE.search(assistant)
        ):
            findings.append(
                Finding(
                    "content.ellipsis_shorthand",
                    SEVERITY_WARN,
                    "Ellipsis shorthand in code block",
                    True,
                )
            )

    if user and assistant and CODE_REQUEST_RE.search(user) and "```" not in assistant:
        findings.append(
            Finding("content.missing_code_block", SEVERITY_WARN, "User asks for code but assistant has no fenced block")
        )

    if user and assistant:
        ul, uc = detect_lang(user)
        al, ac = detect_lang(assistant)
        if uc == "high" and ac == "high" and ul != al:
            findings.append(
                Finding(
                    "i18n.lang_mismatch",
                    SEVERITY_ERROR,
                    f"High-confidence language mismatch: user={ul}, assistant={al}",
                )
            )
        elif ul != "mixed" and al != "mixed" and ul != al and uc in ("high", "medium") and ac in ("high", "medium"):
            findings.append(
                Finding(
                    "i18n.lang_mismatch_soft",
                    SEVERITY_WARN,
                    f"Possible language mismatch: user={ul}, assistant={al}",
                )
            )

    return findings


def _fix_html_entities(text: str) -> str:
    return html.unescape(text)


def _fix_unbalanced_fences(text: str) -> str:
    if text.count("```") % 2 == 0:
        return text
    return text.rstrip() + "\n```"


def _fix_ellipsis_shorthand(text: str) -> tuple[str, bool]:
    """Remove/replace lazy ellipsis placeholders inside fenced code blocks."""
    parts = text.split("```")
    if len(parts) < 3:
        return text, False

    changed = False
    for i in range(1, len(parts), 2):
        block = parts[i]
        # language tag is on the first line of odd segments
        block_lines = block.split("\n")
        if not block_lines:
            continue
        code_lines = block_lines[1:] if len(block_lines) > 1 else []
        lang_line = block_lines[0]

        cleaned: list[str] = []
        for line in code_lines:
            if ELLIPSIS_LINE_RE.match(line) or ELLIPSIS_JSX_RE.match(line):
                changed = True
                continue
            if INLINE_ELLIPSIS_RE.search(line):
                new_line = INLINE_ELLIPSIS_RE.sub("{}", line)
                if new_line != line:
                    changed = True
                line = new_line
            cleaned.append(line)

        parts[i] = lang_line + ("\n" + "\n".join(cleaned) if cleaned else "")

    return "```".join(parts), changed


def _normalize_record(rec: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    fixes: list[str] = []
    msgs = rec.get("messages")
    if not isinstance(msgs, list):
        return rec, fixes

    by_role: dict[str, dict[str, Any]] = {}
    extras: list[dict[str, Any]] = []
    for m in msgs:
        if not isinstance(m, dict):
            continue
        role = m.get("role")
        if role in ("system", "user", "assistant") and role not in by_role:
            by_role[role] = m
        else:
            extras.append(m)

    ordered: list[dict[str, Any]] = []
    for role in ("system", "user", "assistant"):
        if role in by_role:
            ordered.append(by_role[role])
        elif role == "system":
            ordered.append({"role": "system", "content": CANONICAL_SYSTEM})
            fixes.append("structure.insert_system")

    role_order_wrong = bool(msgs) and [m.get("role") for m in msgs if isinstance(m, dict)][:3] != [
        "system",
        "user",
        "assistant",
    ]
    if not ordered:
        return rec, fixes
    if ordered[0].get("role") != "system":
        fixes.append("structure.role_order")

    new_msgs: list[dict[str, Any]] = []
    for m in ordered:
        role = m.get("role", "")
        content = m.get("content", "")
        if isinstance(content, str):
            if role == "system" and content.strip() != CANONICAL_SYSTEM:
                content = CANONICAL_SYSTEM
                fixes.append("prompt.canonical_system")
            if content != content.strip():
                content = content.strip()
                fixes.append(f"content.trim_{role}")
            if re.search(r"&(?:amp|lt|gt|quot|#39);", content):
                content = _fix_html_entities(content)
                fixes.append(f"content.unescape_{role}")
            if role == "assistant":
                fixed = _fix_unbalanced_fences(content)
                if fixed != content:
                    content = fixed
                    fixes.append("markdown.close_fence")
                fixed, ellipsis_changed = _fix_ellipsis_shorthand(content)
                if ellipsis_changed:
                    content = fixed
                    fixes.append("content.expand_ellipsis")
        new_msgs.append({"role": role, "content": content})

    if fixes or len(new_msgs) != len(msgs) or role_order_wrong:
        if role_order_wrong and "structure.role_order" not in fixes:
            fixes.append("structure.role_order")
        return {"messages": new_msgs}, fixes
    return rec, fixes


def process_record(rec: dict[str, Any], *, fix: bool = True) -> AuditOutcome:
    if fix:
        rec, fixes = _normalize_record(rec)
    else:
        fixes = []

    findings = audit_record(rec)
    # Re-audit after fixes; ellipsis warnings should clear when auto-fixed.
    if fix and fixes:
        findings = audit_record(rec)

    quarantine = any(
        f.severity == SEVERITY_ERROR
        and f.rule_id
        in {
            "structure.empty_messages",
            "content.empty_system",
            "content.empty_user",
            "content.empty_assistant",
            "content.broken_placeholder",
            "content.assistant_too_short",
            "i18n.lang_mismatch",
            "markdown.unbalanced_fence",
        }
        for f in findings
    )

    return AuditOutcome(record=rec, findings=findings, fixes_applied=fixes, quarantine=quarantine)


def audit_shards(
    shards_dir: str = SHARDS,
    *,
    fix: bool = True,
    report_path: str | None = None,
    quarantine_path: str | None = None,
) -> dict[str, Any]:
    report_path = report_path or os.path.join(BASE, "qa_report.json")
    quarantine_path = quarantine_path or os.path.join(BASE, "quarantine.jsonl")

    files = sorted(glob.glob(os.path.join(shards_dir, "shard_*.jsonl")))
    rule_counts: dict[str, int] = {}
    severity_counts = {SEVERITY_ERROR: 0, SEVERITY_WARN: 0, SEVERITY_INFO: 0}
    fix_counts: dict[str, int] = {}
    samples: dict[str, list[dict[str, Any]]] = {}

    total_lines = 0
    kept_lines = 0
    quarantined: list[dict[str, Any]] = []
    invalid_json = 0

    for path in files:
        shard_name = os.path.basename(path)
        updated_lines: list[str] = []
        with open(path, "r", encoding="utf-8") as fh:
            raw_lines = fh.readlines()

        for line_no, raw in enumerate(raw_lines, 1):
            line = raw.strip()
            if not line:
                continue
            total_lines += 1
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                invalid_json += 1
                quarantined.append(
                    {
                        "source": f"{shard_name}:{line_no}",
                        "reason": "invalid_json",
                        "raw": line[:500],
                    }
                )
                rule_counts["invalid_json"] = rule_counts.get("invalid_json", 0) + 1
                continue

            outcome = process_record(rec, fix=fix)
            for f in outcome.findings:
                rule_counts[f.rule_id] = rule_counts.get(f.rule_id, 0) + 1
                severity_counts[f.severity] = severity_counts.get(f.severity, 0) + 1
                if len(samples.get(f.rule_id, [])) < 3:
                    samples.setdefault(f.rule_id, []).append(
                        {
                            "source": f"{shard_name}:{line_no}",
                            "message": f.message,
                            "user": _get_roles(outcome.record).get("user", "")[:120],
                        }
                    )

            for fx in outcome.fixes_applied:
                fix_counts[fx] = fix_counts.get(fx, 0) + 1

            if outcome.quarantine:
                quarantined.append(
                    {
                        "source": f"{shard_name}:{line_no}",
                        "findings": [
                            {"rule": f.rule_id, "severity": f.severity, "message": f.message}
                            for f in outcome.findings
                            if f.severity == SEVERITY_ERROR
                        ],
                        "record": outcome.record,
                    }
                )
                continue

            kept_lines += 1
            updated_lines.append(json.dumps(outcome.record, ensure_ascii=False))

        if fix:
            with open(path, "w", encoding="utf-8") as fh:
                if updated_lines:
                    fh.write("\n".join(updated_lines) + "\n")
                else:
                    fh.write("")

    with open(quarantine_path, "w", encoding="utf-8") as fh:
        for item in quarantined:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    health = 100
    if total_lines:
        health = round(100 * kept_lines / total_lines, 1)

    report = {
        "files_scanned": len(files),
        "lines_scanned": total_lines,
        "lines_kept": kept_lines,
        "lines_quarantined": len(quarantined),
        "invalid_json": invalid_json,
        "health_score": health,
        "severity_counts": severity_counts,
        "rule_counts": dict(sorted(rule_counts.items(), key=lambda x: -x[1])),
        "fixes_applied": dict(sorted(fix_counts.items(), key=lambda x: -x[1])),
        "samples": samples,
        "quarantine_path": quarantine_path,
        "fixed_in_place": fix,
    }
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit and auto-fix SFT dataset shards")
    parser.add_argument("--check-only", action="store_true", help="Audit without writing fixed shards")
    parser.add_argument("--shards", default=SHARDS, help="Path to shards directory")
    parser.add_argument("--report", default=os.path.join(BASE, "qa_report.json"))
    parser.add_argument("--quarantine", default=os.path.join(BASE, "quarantine.jsonl"))
    args = parser.parse_args()

    report = audit_shards(
        args.shards,
        fix=not args.check_only,
        report_path=args.report,
        quarantine_path=args.quarantine,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()