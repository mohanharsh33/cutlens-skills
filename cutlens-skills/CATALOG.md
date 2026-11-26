# Skill Catalog & Trigger Routing Matrix (`cutlens-skills`)

Complete index of all **13 atomic skills** across **3 modular packs**.

| # | Skill Name | Pack | Helper Script | Primary Output Artifact |
| :-: | :--- | :--- | :--- | :--- |
| 00 | [`video-breakdown-orchestrator`](./skills/video-breakdown-orchestrator/SKILL.md) | Pack 1 | `manage_pipeline_state.py` | `artifacts/pipeline_state.json` |
| 01 | [`video-media-ingest`](./skills/video-media-ingest/SKILL.md) | Pack 1 | `probe_media.py` | `artifacts/01_media_manifest.json` |
| 02 | [`shot-forensics-classify`](./skills/shot-forensics-classify/SKILL.md) | Pack 1 | `score_shot_signals.py` | `artifacts/02_shot_forensics.json` |
| 03 | [`camera-lens-blocking-audit`](./skills/camera-lens-blocking-audit/SKILL.md) | Pack 1 | `analyze_camera_motion.py` | `artifacts/03_camera_blocking.json` |
| 04 | [`color-grade-lighting-audit`](./skills/color-grade-lighting-audit/SKILL.md) | Pack 1 | `extract_color_lut.py` | `artifacts/04_color_lighting.json` + `look_starter.cube` |
| 05 | [`edit-rhythm-vfx-transitions`](./skills/edit-rhythm-vfx-transitions/SKILL.md) | Pack 1 | `extract_edit_vfx_srt.py` | `artifacts/05_edit_vfx_timeline.json` + `captions.srt` |
| 06 | [`sound-design-foley-audit`](./skills/sound-design-foley-audit/SKILL.md) | Pack 1 | `analyze_audio_layers.py` | `artifacts/06_sound_design.json` |
| 07 | [`remake-constraints-lock`](./skills/remake-constraints-lock/SKILL.md) | Pack 2 | `sanitize_ip_anchors.py` | `artifacts/07_remake_constraints.json` |
| 08 | [`scene-reverse-prompt-forge`](./skills/scene-reverse-prompt-forge/SKILL.md) | Pack 2 | `compile_scene_prompts.py` | `artifacts/08_scene_prompts.json` + `08_REMAKE_BLUEPRINT.md` + `report.html` |
| 09 | [`remake-plan-qa-audit`](./skills/remake-plan-qa-audit/SKILL.md) | Pack 2 | `audit_remake_plan.py` | `artifacts/09_qa_report.json` |
| SP1 | [`viral-hook-pacing-audit`](./skills/viral-hook-pacing-audit/SKILL.md) | Pack 3 | `score_retention_curve.py` | `artifacts/10_retention_audit.json` + `10_RETENTION_AUDIT.md` |
| SP2 | [`remotion-code-rebuilder`](./skills/remotion-code-rebuilder/SKILL.md) | Pack 3 | `validate_remotion_timing.py` | `artifacts/11_remotion_bundle/Composition.tsx` |
| SP3 | [`multi-aspect-reframe-plan`](./skills/multi-aspect-reframe-plan/SKILL.md) | Pack 3 | `plan_reframe_crops.py` | `artifacts/12_reframe_plan.json` |
