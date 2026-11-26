#!/usr/bin/env python3
"""End-to-end synthetic smoke test exercising all 13 cutlens-skills scripts and fail-closed QA."""

from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent


def resolve_ffmpeg() -> str:
    env_bin = os.environ.get("CUTLENS_FFMPEG_BIN", "").strip()
    if env_bin and Path(env_bin).exists():
        return env_bin
    found = shutil.which("ffmpeg")
    if not found:
        raise RuntimeError("ffmpeg not found on PATH.")
    return found


def run_cmd(cmd: list[str], cwd: Path = REPO_ROOT, expect_rc: int | None = 0) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)
    if expect_rc is not None and proc.returncode != expect_rc:
        raise AssertionError(
            f"Command failed (expected rc={expect_rc}, got rc={proc.returncode}):\n"
            f"  CMD: {' '.join(cmd)}\n  STDOUT: {proc.stdout.strip()}\n  STDERR: {proc.stderr.strip()}"
        )
    return proc


def synthesize_test_video(ffmpeg: str, output_video: Path) -> None:
    output_video.parent.mkdir(parents=True, exist_ok=True)
    filter_complex = (
        "testsrc2=size=640x360:rate=24:duration=2[v0];"
        "smptebars=size=640x360:rate=24:duration=2[v1];"
        "color=c=0xD47A3C:size=640x360:rate=24:duration=2,noise=alls=25:allf=t+u[v2];"
        "[v0][v1][v2]concat=n=3:v=1:a=0[vout];"
        "aevalsrc='0.10*sin(2*PI*220*t)+0.55*sin(2*PI*110*t)*gt(mod(t,0.5),0.42)':s=44100:d=6[aout]"
    )
    run_cmd([
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-g", "24",
        "-c:a", "aac", "-b:a", "128k", str(output_video),
    ])


def load_json(path: Path) -> dict[str, Any]:
    assert path.exists(), f"Expected JSON artifact missing: {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def run_smoke_pipeline(work_dir: Path, validate_repo: bool = True) -> dict[str, Any]:
    py = sys.executable
    ffmpeg = resolve_ffmpeg()
    if validate_repo:
        run_cmd([py, "scripts/validate_skills.py", "--strict-manifest", "--check-scripts"], expect_rc=0)

    sample_video = work_dir / "synthetic_3shot_6s.mp4"
    artifacts = work_dir / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    synthesize_test_video(ffmpeg, sample_video)

    raw_srt = work_dir / "input_overlapping.srt"
    raw_srt.write_text(
        "1\n00:00:00,000 --> 00:00:02,200\nFirst opening hook line.\n\n"
        "2\n00:00:02,000 --> 00:00:04,100\nSecond motion graphic line.\n\n"
        "3\n00:00:04,000 --> 00:00:05,950\nFinal warm workshop takeaway.\n",
        encoding="utf-8",
    )
    subject_notes = work_dir / "subject_notes.json"
    subject_notes.write_text(json.dumps({
        "entity_anchors": [
            {"token": "[CHAR_01]", "role": "character", "locked_description": "Studio designer wearing Nike jacket holding an iPhone with a Shutterstock badge"},
            {"token": "[ENV_01]", "role": "environment", "locked_description": "Clean minimalist editing suite styled looks like John Wick neon ambiance"},
        ],
        "shot_actions": {
            "SHOT_001": "opens a brushed workstation monitor displaying audio waveforms",
            "SHOT_002": "transitions across crisp geometric motion-graphic analytics bars",
            "SHOT_003": "adjusts warm tungsten practical desk lamp over dark timber bench",
        },
    }, indent=2), encoding="utf-8")

    state_file = artifacts / "pipeline_state.json"
    orch = "skills/video-breakdown-orchestrator/scripts/manage_pipeline_state.py"
    run_cmd([py, orch, "init", "--video", str(sample_video), "--profile", "full", "--artifacts-dir", str(artifacts)])

    manifest_p = artifacts / "01_media_manifest.json"
    run_cmd([py, "skills/video-media-ingest/scripts/probe_media.py", "--video", str(sample_video), "--output", str(manifest_p), "--keyframes-dir", str(artifacts / "keyframes"), "--scene-threshold", "0.25", "--min-shot-sec", "0.5"])
    run_cmd([py, orch, "complete", "--state", str(state_file), "--stage", "01-ingest"])

    forensics_p = artifacts / "02_shot_forensics.json"
    run_cmd([py, "skills/shot-forensics-classify/scripts/score_shot_signals.py", "--manifest", str(manifest_p), "--output", str(forensics_p)])
    run_cmd([py, orch, "complete", "--state", str(state_file), "--stage", "02-forensics"])

    camera_p = artifacts / "03_camera_blocking.json"
    run_cmd([py, "skills/camera-lens-blocking-audit/scripts/analyze_camera_motion.py", "--manifest", str(manifest_p), "--forensics", str(forensics_p), "--output", str(camera_p)])
    run_cmd([py, orch, "complete", "--state", str(state_file), "--stage", "03-camera-lens"])

    color_p, lut_p = artifacts / "04_color_lighting.json", artifacts / "look_starter.cube"
    run_cmd([py, "skills/color-grade-lighting-audit/scripts/extract_color_lut.py", "--manifest", str(manifest_p), "--camera", str(camera_p), "--output", str(color_p), "--lut-output", str(lut_p)])
    run_cmd([py, orch, "complete", "--state", str(state_file), "--stage", "04-color-lighting"])

    timeline_p, srt_p = artifacts / "05_edit_vfx_timeline.json", artifacts / "captions.srt"
    run_cmd([py, "skills/edit-rhythm-vfx-transitions/scripts/extract_edit_vfx_srt.py", "--manifest", str(manifest_p), "--forensics", str(forensics_p), "--camera", str(camera_p), "--captions-in", str(raw_srt), "--output", str(timeline_p), "--srt-output", str(srt_p)])
    run_cmd([py, orch, "complete", "--state", str(state_file), "--stage", "05-edit-vfx"])

    sound_p = artifacts / "06_sound_design.json"
    run_cmd([py, "skills/sound-design-foley-audit/scripts/analyze_audio_layers.py", "--manifest", str(manifest_p), "--timeline", str(timeline_p), "--output", str(sound_p)])
    run_cmd([py, orch, "complete", "--state", str(state_file), "--stage", "06-sound-design"])

    constraints_p = artifacts / "07_remake_constraints.json"
    run_cmd([py, "skills/remake-constraints-lock/scripts/sanitize_ip_anchors.py", "--forensics", str(forensics_p), "--camera", str(camera_p), "--color", str(color_p), "--timeline", str(timeline_p), "--sound", str(sound_p), "--subject-notes", str(subject_notes), "--output", str(constraints_p)])
    run_cmd([py, orch, "complete", "--state", str(state_file), "--stage", "07-constraints-lock"])

    prompts_p, md_p, html_p = artifacts / "08_scene_prompts.json", artifacts / "08_REMAKE_BLUEPRINT.md", artifacts / "report.html"
    run_cmd([py, "skills/scene-reverse-prompt-forge/scripts/compile_scene_prompts.py", "--manifest", str(manifest_p), "--camera", str(camera_p), "--color", str(color_p), "--timeline", str(timeline_p), "--sound", str(sound_p), "--constraints", str(constraints_p), "--json-output", str(prompts_p), "--md-output", str(md_p), "--html-output", str(html_p)])
    run_cmd([py, orch, "complete", "--state", str(state_file), "--stage", "08-prompt-forge"])

    run_cmd([py, "skills/viral-hook-pacing-audit/scripts/score_retention_curve.py", "--timeline", str(timeline_p), "--sound", str(sound_p), "--format", "shorts", "--json-output", str(artifacts / "10_retention_audit.json"), "--md-output", str(artifacts / "10_RETENTION_AUDIT.md")])
    remotion_dir = artifacts / "11_remotion_bundle"
    run_cmd([py, "skills/remotion-code-rebuilder/scripts/validate_remotion_timing.py", "--forensics", str(forensics_p), "--color", str(color_p), "--timeline", str(timeline_p), "--constraints", str(constraints_p), "--manifest", str(manifest_p), "--out-dir", str(remotion_dir)])
    run_cmd([py, "skills/multi-aspect-reframe-plan/scripts/plan_reframe_crops.py", "--manifest", str(manifest_p), "--camera", str(camera_p), "--timeline", str(timeline_p), "--targets", "9:16,4:5,1:1,16:9", "--output", str(artifacts / "12_reframe_plan.json")])

    qa_p = artifacts / "09_qa_report.json"
    run_cmd([py, "skills/remake-plan-qa-audit/scripts/audit_remake_plan.py", "--manifest", str(manifest_p), "--constraints", str(constraints_p), "--prompts", str(prompts_p), "--lut", str(lut_p), "--remotion-parity", str(remotion_dir / "timing_parity.json"), "--require-lut", "--output", str(qa_p)], expect_rc=0)
    run_cmd([py, orch, "complete", "--state", str(state_file), "--stage", "09-qa-audit"])

    prompts_doc = load_json(prompts_p)
    corrupt_p, corrupt_qa_p = work_dir / "corrupt_prompts.json", work_dir / "corrupt_qa.json"
    bad = copy.deepcopy(prompts_doc)
    bad["shots"][0]["camera_movements"] = ["dolly-in", "pull-out"]
    bad["shots"][0]["prompts"]["veo_3_1_i2v"] += " Featured Shutterstock logo."
    corrupt_p.write_text(json.dumps(bad, indent=2), encoding="utf-8")
    run_cmd([py, "skills/remake-plan-qa-audit/scripts/audit_remake_plan.py", "--manifest", str(manifest_p), "--constraints", str(constraints_p), "--prompts", str(corrupt_p), "--output", str(corrupt_qa_p)], expect_rc=1)
    return {"status": "ALL_13_SKILLS_PASSED"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run end-to-end synthetic FFmpeg smoke test across all 13 cutlens-skills.")
    parser.add_argument("--work-dir", type=Path, default=None)
    parser.add_argument("--skip-repo-validate", action="store_true")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="cutlens_smoke_") as tmp:
        target = args.work_dir.resolve() if args.work_dir else Path(tmp)
        target.mkdir(parents=True, exist_ok=True)
        print(json.dumps(run_smoke_pipeline(target, validate_repo=not args.skip_repo_validate), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
