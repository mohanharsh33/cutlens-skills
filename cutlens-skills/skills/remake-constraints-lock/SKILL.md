---
name: remake-constraints-lock
description: Compiles immutable continuity anchors (subject tokens, lens/LUT bible, aspect ratio, color wheels) and deterministically scrubs copyrighted trademarks, stock watermarks, and real-person likenesses before reverse-prompting. Use after Stage 06 sound audit. Do NOT use to write final per-shot AI prompts or run final QA; use scene-reverse-prompt-forge or remake-plan-qa-audit instead.
license: MIT
compatibility: Requires Python 3.12+ (stdlib only).
metadata:
  author: "Harsh Mohan (mohanharsh33)"
  version: "1.0.0"
  pack: "pack-02-reverse-prompt-qa"
  pipeline-stage: "07-constraints-lock"
---

# Remake Constraints and Clean-Room IP Lock

Run [`./scripts/sanitize_ip_anchors.py`](./scripts/sanitize_ip_anchors.py) to emit `artifacts/07_remake_constraints.json` matching [`./assets/remake_constraints.schema.json`](./assets/remake_constraints.schema.json). Reference [`./references/clean-room-ip-policy.md`](./references/clean-room-ip-policy.md).

## Gotchas

- **Pronoun morphing:** Always reference locked `[CHAR_01]` / `[ENV_01]` tokens across shots.
