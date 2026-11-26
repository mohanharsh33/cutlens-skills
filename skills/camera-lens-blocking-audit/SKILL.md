---
name: camera-lens-blocking-audit
description: Analyzes every video shot for camera movement vectors (static, pan, tilt, dolly-in, pull-out, handheld jitter), estimated focal length, depth of field proxy, shot scale, camera angle, and subject blocking coordinates. Use after Stage 02 forensics. Do NOT use for color grading or aspect-ratio cropping; use color-grade-lighting-audit or multi-aspect-reframe-plan instead.
license: MIT
compatibility: Requires Python 3.12+ (stdlib only) and FFmpeg on PATH.
metadata:
  author: "Harsh Mohan (mohanharsh33)"
  version: "1.0.0"
  pack: "pack-01-core-forensics"
  pipeline-stage: "03-camera-lens"
---

# Camera Lens and Blocking Audit

Run [`./scripts/analyze_camera_motion.py`](./scripts/analyze_camera_motion.py) to emit `artifacts/03_camera_blocking.json` matching [`./assets/camera_blocking.schema.json`](./assets/camera_blocking.schema.json). Reference [`./references/optics-and-rig-grammar.md`](./references/optics-and-rig-grammar.md).

## Gotchas

- **Max-2 Motion Grammar Rule:** Never combine contradictory camera movements (`dolly-in` + `pull-out`).
