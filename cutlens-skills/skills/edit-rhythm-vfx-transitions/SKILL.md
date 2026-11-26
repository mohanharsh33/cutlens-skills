---
name: edit-rhythm-vfx-transitions
description: Measures editing pacing (ASL, cuts per minute), classifies shot transitions (hard cut, dip-to-black, whip-pan, dissolve, speed ramp), catalogs VFX/HUD overlays, and exports overlap-validated SRT captions. Use after Stage 03 camera audit. Do NOT use for audio stem forensics or hook retention scoring; use sound-design-foley-audit or viral-hook-pacing-audit instead.
license: MIT
compatibility: Requires Python 3.12+ (stdlib only) and FFmpeg/FFprobe on PATH.
metadata:
  author: "Harsh Mohan (mohanharsh33)"
  version: "1.0.0"
  pack: "pack-01-core-forensics"
  pipeline-stage: "05-edit-vfx"
---

# Edit Rhythm, VFX and Transitions

Run [`./scripts/extract_edit_vfx_srt.py`](./scripts/extract_edit_vfx_srt.py) to emit `artifacts/05_edit_vfx_timeline.json` matching [`./assets/edit_vfx_timeline.schema.json`](./assets/edit_vfx_timeline.schema.json) and `artifacts/captions.srt`. Reference [`./references/transitions-vfx-and-srt.md`](./references/transitions-vfx-and-srt.md).

## Gotchas

- **Overlapping SRT cues:** Raw auto-captions often overlap; `extract_edit_vfx_srt.py` repairs them deterministically.
