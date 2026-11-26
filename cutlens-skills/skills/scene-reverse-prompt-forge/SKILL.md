---
name: scene-reverse-prompt-forge
description: Synthesizes exact scene-by-scene reverse-engineered prompts (Start/End Keyframe T2I, Veo 3.1, Kling 3.0, Seedance 2.5, Runway Gen-4.5, Sora 2, and live-shoot specs) plus a Markdown blueprint and standalone HTML report from Stages 03-07 telemetry. Use after Stage 07 constraints lock. Do NOT use for IP scrubbing or final QA; use remake-constraints-lock or remake-plan-qa-audit instead.
license: MIT
compatibility: Requires Python 3.12+ (stdlib only).
metadata:
  author: "Harsh Mohan (mohanharsh33)"
  version: "1.0.0"
  pack: "pack-02-reverse-prompt-qa"
  pipeline-stage: "08-prompt-forge"
---

# Scene Reverse Prompt Forge

Run [`./scripts/compile_scene_prompts.py`](./scripts/compile_scene_prompts.py) to emit `artifacts/08_scene_prompts.json` matching [`./assets/scene_prompts.schema.json`](./assets/scene_prompts.schema.json), `artifacts/08_REMAKE_BLUEPRINT.md`, and `artifacts/report.html`. Reference [`./references/model-dialect-syntax.md`](./references/model-dialect-syntax.md).

## Gotchas

- **Dialect limits:** Keep Sora 2 strictly `<= 80` words, Runway Gen-4.5 concise (`<= 320` chars), and Veo 3.1 with an explicit `Audio:` sentence.
