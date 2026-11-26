---
name: multi-aspect-reframe-plan
description: Computes subject-centered per-shot crop windows for 9:16, 4:5, 1:1, and 16:9 delivery using Stage 03 blocking coordinates, detects TikTok/Reels/Shorts UI safe-zone collisions, and emits runnable even-pixel FFmpeg render commands targeting -14 LUFS. Use after Stages 01, 03, and 05. Do NOT use to analyze original camera lenses or retention pacing; use camera-lens-blocking-audit or viral-hook-pacing-audit instead.
license: MIT
compatibility: Requires Python 3.12+ (stdlib only); emitted render commands require FFmpeg on PATH.
metadata:
  author: "Harsh Mohan (mohanharsh33)"
  version: "1.0.0"
  pack: "pack-03-specialists"
  pipeline-stage: "sp3-reframe-plan"
---

# Multi-Aspect Reframe Plan

Run [`./scripts/plan_reframe_crops.py`](./scripts/plan_reframe_crops.py) to emit `artifacts/12_reframe_plan.json` matching [`./assets/reframe_plan.schema.json`](./assets/reframe_plan.schema.json). Reference [`./references/platform-safe-zones.md`](./references/platform-safe-zones.md).

## Gotchas

- **Even-pixel H.264 rule:** All crop widths and heights are rounded to even integers so `libx264` + `yuv420p` never fails.
