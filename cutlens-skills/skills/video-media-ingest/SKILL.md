---
name: video-media-ingest
description: Probes local video files with FFprobe and FFmpeg to extract container specs, color space, AIGC/C2PA provenance tags, CFR vs VFR cadence jitter, shot cut boundaries, and start/mid/end keyframes. Use as Stage 01 before any video analysis. Do NOT use to classify AI vs live shots or write prompts; use shot-forensics-classify or scene-reverse-prompt-forge instead.
license: MIT
compatibility: Requires Python 3.12+ (stdlib only) and FFmpeg/FFprobe on PATH.
metadata:
  author: "Harsh Mohan (mohanharsh33)"
  version: "1.0.0"
  pack: "pack-01-core-forensics"
  pipeline-stage: "01-ingest"
---

# Video Media Ingest

Run [`./scripts/probe_media.py`](./scripts/probe_media.py) to emit `artifacts/01_media_manifest.json` matching [`./assets/media_manifest.schema.json`](./assets/media_manifest.schema.json). Reference [`./references/ffprobe-provenance-tags.md`](./references/ffprobe-provenance-tags.md) for provenance signals.

## Gotchas

- **VFR mobile clips:** Inspect `frame_delta_cv > 0.08` before trusting frame-index math.
- **Rotated vertical phone videos:** Effective width/height accounts for rotation metadata.
