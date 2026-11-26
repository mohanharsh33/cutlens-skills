---
name: video-breakdown-orchestrator
description: Orchestrates end-to-end CutLens video reverse-engineering across ingest, forensics, camera, color, editing, audio, reverse prompting, and fail-closed QA. Use when breaking down a full local video into scene prompts or lookbooks. Do NOT use for single-stage tasks like LUT extraction alone; invoke color-grade-lighting-audit directly.
license: MIT
compatibility: Requires Python 3.12+ (stdlib only) and FFmpeg/FFprobe on PATH.
metadata:
  author: "Harsh Mohan (mohanharsh33)"
  version: "1.0.0"
  pack: "pack-01-core-forensics"
  pipeline-stage: "00-orchestrator"
---

# Video Breakdown Orchestrator

Manage stateful, resumable, fail-closed execution across the CutLens video forensics and reverse-prompting pipeline. Read [`./references/stage-handoff-contract.md`](./references/stage-handoff-contract.md) for profile stage lists and required handoff files.

## Procedure

1. Initialize or resume state with [`./scripts/manage_pipeline_state.py`](./scripts/manage_pipeline_state.py):
   `python skills/video-breakdown-orchestrator/scripts/manage_pipeline_state.py init --video path/to/video.mp4 --profile full --artifacts-dir artifacts`
2. Query next stage with `next`, execute its skill, and record `complete` or `fail`.
3. Never mark a `full` run complete until `09-qa-audit` exits with code `0`.

## Gotchas

- **Stale artifacts from a different video:** `init` checks SHA-256 and refuses to overwrite a mismatched run unless `--force-reset` is passed.
- **Partial re-runs after QA failure:** Repair Stage 07 or 08 and re-run Stage 09 instead of re-probing from scratch.
