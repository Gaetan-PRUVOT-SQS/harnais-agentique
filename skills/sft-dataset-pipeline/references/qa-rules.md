# QA Rules Reference

Implémentées dans `templates/audit.py`. Garder les rule IDs stables pour que fixtures et tests restent portables entre domaines.

## Severity levels

- `error` — triggers quarantine if not auto-fixable
- `warning` — auto-fix attempted; quarantine only if still failing critical checks
- `info` — cosmetic, always auto-fixable

## Structure rules

| Rule ID | Severity | Auto-fix | Description |
|---------|----------|----------|-------------|
| `structure.empty_messages` | error | no | Missing or empty `messages` array |
| `structure.missing_role` | error | partial | Missing system/user/assistant |
| `structure.role_order` | warn | yes | Not system → user → assistant |
| `structure.insert_system` | — | yes | Inject canonical system if absent |

## Prompt rules

| Rule ID | Severity | Auto-fix | Description |
|---------|----------|----------|-------------|
| `prompt.non_canonical_system` | warn | yes | System prompt ≠ `CANONICAL_SYSTEM` |
| `prompt.canonical_system` | — | yes | Fix applied: replaced system prompt |

## Content rules

| Rule ID | Severity | Auto-fix | Description |
|---------|----------|----------|-------------|
| `content.empty_{role}` | error | no | Empty system/user/assistant text |
| `content.html_entities` | warn | yes | `&amp;`, `&lt;`, etc. — unescape |
| `content.trim_whitespace` | info | yes | Leading/trailing whitespace |
| `content.assistant_too_short` | error | no | Assistant < 80 chars → quarantine |
| `content.assistant_short` | warn | no | Assistant < 180 chars (warning only) |
| `content.broken_placeholder` | error | no | `... rest of`, `[insert]`, lorem, TODO: implement |
| `content.ellipsis_shorthand` | warn | yes | `// ...`, `{/* ... */}`, `/* ... */` in code |
| `content.missing_code_block` | warn | no | User asks for code, no ``` in assistant |

### Broken placeholder patterns

```python
BROKEN_PLACEHOLDER_RE = re.compile(
    r"(?:"
    r"\.\.\.\s*(?:rest of|omitted|truncated|your code)|"
    r"\[insert(?:\s+code)?\]|<insert|<your[\s_-]?code[\s_-]?here>|"
    r"lorem ipsum|TODO:\s*implement|FIXME:\s*implement"
    r")",
    re.IGNORECASE,
)
```

### Ellipsis auto-fix

Inside fenced code blocks only:
- Drop lines matching `^\s*//\s*\.\.\.\s*$`
- Drop lines matching `^\s*\{/\*\s*\.\.\.\s*\*/\}\s*$`
- Replace inline `/* ... */` with `{}`

## Markdown rules

| Rule ID | Severity | Auto-fix | Description |
|---------|----------|----------|-------------|
| `markdown.unbalanced_fence` | error | yes | Odd count of ``` — append closing fence |

## i18n rules

| Rule ID | Severity | Auto-fix | Description |
|---------|----------|----------|-------------|
| `i18n.lang_mismatch` | error | no | High-confidence user≠assistant language |
| `i18n.lang_mismatch_soft` | warn | no | Medium-confidence mismatch |

Language detection uses marker word counts + accented chars (FR). Thresholds:
- `high`: ≥3 markers one lang, ≤1 other
- `medium`: ≥2 markers with +1 margin

Quarantine only on **high-confidence** mismatch.

## process_record flow

```
audit_record(rec) → findings
_apply_fixes(rec, findings) → fixed record + fixes_applied
_recheck_quarantine(fixed) → quarantine bool
```

`role_order_wrong` must trigger write even when no content changed.

## Post-build gates (`test_qa.py`)

For every line in `train.jsonl` / `val.jsonl`:
- Valid JSON
- `roles[:3] == ["system", "user", "assistant"]`
- `system content == CANONICAL_SYSTEM`
- `process_record(fix=False).quarantine == False`

## Fixture categories (minimum set)

| ID pattern | Purpose |
|------------|---------|
| `pass.valid_en` | Clean English example |
| `pass.valid_fr` | Clean French example |
| `fix.system_prompt` | Wrong system → canonical |
| `fix.html_entities` | `&lt;` → `<` |
| `fix.role_order` | Reorder messages |
| `fix.unbalanced_fence` | Append ``` |
| `fix.ellipsis` | Strip `// ...` in code |
| `quarantine.placeholder` | Broken placeholder stays out |
| `quarantine.lang_mismatch` | FR user + EN assistant |
| `quarantine.too_short` | Assistant < 80 chars |

## qa_report.json shape

```json
{
  "shards_scanned": 90,
  "records_total": 1081,
  "records_fixed": 42,
  "quarantine_count": 0,
  "health_score": 100.0,
  "fixes_by_rule": {"prompt.canonical_system": 12, ...},
  "findings_by_rule": {...}
}
```

`health_score = 100 * (1 - quarantine_count / records_total)`