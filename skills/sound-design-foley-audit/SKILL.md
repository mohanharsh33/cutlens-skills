---
name: sound-design-foley-audit
description: Measures EBU R128 loudness (LUFS/LRA/True Peak), estimates music BPM, detects audio transient hits and cut-to-beat sync rate, flags J-cuts and L-cuts, and maps 4 sound layers (dialogue, music, foley/SFX, ambience). Use after Stage 05 edit timeline. Do NOT use for visual transitions or SRT formatting; use edit-rhythm-vfx-transitions instead.
license: MIT
compatibility: Requires Python 3.12+ (stdlib only) and FFmpeg on PATH.
metadata:
  author: "Harsh Mohan (mohanharsh33)"
  version: "1.0.0"
  pack: "pack-01-core-forensics"
  pipeline-stage: "06-sound-design"
---

# Sound Design and Foley Audit

Run [`./scripts/analyze_audio_layers.py`](./scripts/analyze_audio_layers.py) to emit `artifacts/06_sound_design.json` matching [`./assets/sound_design.schema.json`](./assets/sound_design.schema.json). Reference [`./references/four-layer-audio-rubric.md`](./references/four-layer-audio-rubric.md).

## Gotchas

- **Silent clips:** Handles `audio_stream.present: false` cleanly without crashing downstream stages.
