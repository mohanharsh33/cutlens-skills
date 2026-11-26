---
name: viral-hook-pacing-audit
description: Audits video retention mechanics by scoring 0-3 second hook velocity, flagging static holds over 4.0 seconds, detecting mid-roll pacing decay, evaluating caption WPM readability, and outputting a timecoded re-edit punch list. Use after Stages 05 and 06. Do NOT use to extract raw cuts or write scene prompts; use edit-rhythm-vfx-transitions or scene-reverse-prompt-forge instead.
license: MIT
compatibility: Requires Python 3.12+ (stdlib only).
metadata:
  author: "Harsh Mohan (mohanharsh33)"
  version: "1.0.0"
  pack: "pack-03-specialists"
  pipeline-stage: "sp1-retention-audit"
---

# Viral Hook and Pacing Audit

Run [`./scripts/score_retention_curve.py`](./scripts/score_retention_curve.py) to emit `artifacts/10_retention_audit.json` matching [`./assets/retention_audit.schema.json`](./assets/retention_audit.schema.json) and `artifacts/10_RETENTION_AUDIT.md`. Reference [`./references/hook-retention-heuristics.md`](./references/hook-retention-heuristics.md).

## Gotchas

- **Format thresholds:** Always pass `--format youtube-long` for long-form essays so 4.5s holds are not penalized as Shorts defects.
