---
name: remake-plan-qa-audit
description: Runs a fail-closed deterministic QA audit across Stages 01, 07, and 08 to verify shot ID parity, cumulative runtime within 0.20s, non-contradictory camera motion verbs, model dialect limits, .cube LUT integrity, and zero forbidden IP tokens. Use after Stage 08 prompt forge. Do NOT use to author prompts or score retention; use scene-reverse-prompt-forge or viral-hook-pacing-audit instead.
license: MIT
compatibility: Requires Python 3.12+ (stdlib only).
metadata:
  author: "Harsh Mohan (mohanharsh33)"
  version: "1.0.0"
  pack: "pack-02-reverse-prompt-qa"
  pipeline-stage: "09-qa-audit"
---

# Remake Plan QA Audit

Run [`./scripts/audit_remake_plan.py`](./scripts/audit_remake_plan.py) to emit `artifacts/09_qa_report.json` matching [`./assets/qa_report.schema.json`](./assets/qa_report.schema.json). Reference [`./references/fail-closed-qa-rules.md`](./references/fail-closed-qa-rules.md).

## Gotchas

- **Negative prompt exclusion:** Scans only positive generation prompts against `forbidden_output_tokens[]`.
