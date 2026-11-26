---
name: shot-forensics-classify
description: Classifies every shot across six production methods (live-action, ai-generated, avatar-lipsync, 3d-animation, code-motion-graphics, screen-recording) using deterministic metadata, pixel-plane, and cadence heuristics before optional BYOK VLM tie-breaking. Use after Stage 01 ingest. Do NOT use to probe raw cuts or analyze camera lenses; use video-media-ingest or camera-lens-blocking-audit instead.
license: MIT
compatibility: Requires Python 3.12+ (stdlib only) and FFmpeg on PATH.
metadata:
  author: "Harsh Mohan (mohanharsh33)"
  version: "1.0.0"
  pack: "pack-01-core-forensics"
  pipeline-stage: "02-forensics"
---

# Shot Forensics Classify

Run [`./scripts/score_shot_signals.py`](./scripts/score_shot_signals.py) to emit `artifacts/02_shot_forensics.json` matching [`./assets/shot_forensics.schema.json`](./assets/shot_forensics.schema.json). Reference [`./references/six-class-forensics-rubric.md`](./references/six-class-forensics-rubric.md) for visual tie-breaking.

## Gotchas

- **Recompressed social clips flatten sensor noise:** Never claim cryptographic deepfake proof; preserve `epistemic_disclaimer`.
