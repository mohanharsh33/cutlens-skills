---
name: color-grade-lighting-audit
description: Measures per-shot luminance IRE distribution, contrast ratio, color temperature proxy, saturation, and Lift/Gamma/Gain hex color wheels via FFmpeg signalstats, then exports a starter .cube 3D LUT and lighting topology spec. Use after Stage 03 camera audit. Do NOT use for camera motion or VFX transitions; use camera-lens-blocking-audit or edit-rhythm-vfx-transitions instead.
license: MIT
compatibility: Requires Python 3.12+ (stdlib only) and FFmpeg on PATH.
metadata:
  author: "Harsh Mohan (mohanharsh33)"
  version: "1.0.0"
  pack: "pack-01-core-forensics"
  pipeline-stage: "04-color-lighting"
---

# Color Grade and Lighting Audit

Run [`./scripts/extract_color_lut.py`](./scripts/extract_color_lut.py) to emit `artifacts/04_color_lighting.json` matching [`./assets/color_lighting.schema.json`](./assets/color_lighting.schema.json) and `artifacts/look_starter.cube`. Reference [`./references/signalstats-and-lut-math.md`](./references/signalstats-and-lut-math.md).

## Gotchas

- **`.cube` triplet count:** `LUT_3D_SIZE 17` must contain exactly `4913` RGB floats inside `[0.0, 1.0]`.
