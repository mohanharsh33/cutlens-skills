---
name: remotion-code-rebuilder
description: Rebuilds code-motion-graphics and screen-recording shots into clean-room React/Remotion TSX compositions using measured FPS, hex color wheels, transitions, and sanitized anchor text, then verifies exact frame-count parity. Use after Stages 02, 04, 05, and 07. Do NOT use for live-action/AI video prompts or FFmpeg cropping; use scene-reverse-prompt-forge or multi-aspect-reframe-plan instead.
license: MIT
compatibility: Requires Python 3.12+ (stdlib only); generated TSX targets Remotion v4+ and React 18+.
metadata:
  author: "Harsh Mohan (mohanharsh33)"
  version: "1.0.0"
  pack: "pack-03-specialists"
  pipeline-stage: "sp2-remotion-rebuild"
---

# Remotion Code Rebuilder

Run [`./scripts/validate_remotion_timing.py`](./scripts/validate_remotion_timing.py) using [`./assets/remotion_scene_template.tsx`](./assets/remotion_scene_template.tsx) and [`./references/motion-easing-mapping.md`](./references/motion-easing-mapping.md) to generate `artifacts/11_remotion_bundle/Composition.tsx` and `timing_parity.json`.

## Gotchas

- **Zero CSS animations:** Drive all motion strictly from `useCurrentFrame()`, `interpolate()`, and `spring()`.
