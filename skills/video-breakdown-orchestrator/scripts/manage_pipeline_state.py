#!/usr/bin/env python3
"""Stateful fail-closed orchestrator tracker for cutlens-skills pipelines."""
from __future__ import annotations
import argparse, hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STAGE_SPECS: dict[str, dict[str, Any]] = {
    "01-ingest": {"skill": "video-media-ingest", "inputs": [], "outputs": ["01_media_manifest.json"]},
    "02-forensics": {"skill": "shot-forensics-classify", "inputs": ["01_media_manifest.json"], "outputs": ["02_shot_forensics.json"]},
    "03-camera-lens": {"skill": "camera-lens-blocking-audit", "inputs": ["01_media_manifest.json", "02_shot_forensics.json"], "outputs": ["03_camera_blocking.json"]},
    "04-color-lighting": {"skill": "color-grade-lighting-audit", "inputs": ["01_media_manifest.json", "03_camera_blocking.json"], "outputs": ["04_color_lighting.json", "look_starter.cube"]},
    "05-edit-vfx": {"skill": "edit-rhythm-vfx-transitions", "inputs": ["01_media_manifest.json", "02_shot_forensics.json", "03_camera_blocking.json"], "outputs": ["05_edit_vfx_timeline.json", "captions.srt"]},
    "06-sound-design": {"skill": "sound-design-foley-audit", "inputs": ["01_media_manifest.json", "05_edit_vfx_timeline.json"], "outputs": ["06_sound_design.json"]},
    "07-constraints-lock": {"skill": "remake-constraints-lock", "inputs": ["02_shot_forensics.json", "03_camera_blocking.json", "04_color_lighting.json", "05_edit_vfx_timeline.json", "06_sound_design.json"], "outputs": ["07_remake_constraints.json"]},
    "08-prompt-forge": {"skill": "scene-reverse-prompt-forge", "inputs": ["03_camera_blocking.json", "04_color_lighting.json", "05_edit_vfx_timeline.json", "06_sound_design.json", "07_remake_constraints.json"], "outputs": ["08_scene_prompts.json", "08_REMAKE_BLUEPRINT.md", "report.html"]},
    "09-qa-audit": {"skill": "remake-plan-qa-audit", "inputs": ["01_media_manifest.json", "07_remake_constraints.json", "08_scene_prompts.json"], "outputs": ["09_qa_report.json"]},
    "sp1-retention-audit": {"skill": "viral-hook-pacing-audit", "inputs": ["05_edit_vfx_timeline.json", "06_sound_design.json"], "outputs": ["10_retention_audit.json", "10_RETENTION_AUDIT.md"]},
    "sp2-remotion-rebuild": {"skill": "remotion-code-rebuilder", "inputs": ["02_shot_forensics.json", "04_color_lighting.json", "05_edit_vfx_timeline.json", "07_remake_constraints.json"], "outputs": ["11_remotion_bundle/Composition.tsx", "11_remotion_bundle/timing_parity.json"]},
    "sp3-reframe-plan": {"skill": "multi-aspect-reframe-plan", "inputs": ["01_media_manifest.json", "03_camera_blocking.json", "05_edit_vfx_timeline.json"], "outputs": ["12_reframe_plan.json"]},
}
PROFILES = {
    "full": ["01-ingest", "02-forensics", "03-camera-lens", "04-color-lighting", "05-edit-vfx", "06-sound-design", "07-constraints-lock", "08-prompt-forge", "09-qa-audit"],
    "cinema-forensics": ["01-ingest", "02-forensics", "03-camera-lens", "04-color-lighting", "05-edit-vfx", "06-sound-design"],
    "shorts-growth": ["01-ingest", "02-forensics", "03-camera-lens", "05-edit-vfx", "06-sound-design", "sp1-retention-audit", "sp3-reframe-plan"],
    "motion-code": ["01-ingest", "02-forensics", "04-color-lighting", "05-edit-vfx", "07-constraints-lock", "sp2-remotion-rebuild", "09-qa-audit"],
}

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def sha256_file(path: Path) -> str:
    d = hashlib.sha256()
    with path.open("rb") as h:
        for chunk in iter(lambda: h.read(1024 * 1024), b""):
            d.update(chunk)
    return d.hexdigest()

def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        print(f"ERROR: state file not found: {path}", file=sys.stderr)
        raise SystemExit(2)
    return json.loads(path.read_text(encoding="utf-8"))

def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at_utc"] = utc_now()
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

def cmd_init(args: argparse.Namespace) -> int:
    vp = args.video.resolve()
    if not vp.exists():
        print(f"ERROR: source video not found: {vp}", file=sys.stderr)
        return 2
    ad = args.artifacts_dir.resolve()
    sp = ad / "pipeline_state.json"
    vh = sha256_file(vp)
    if sp.exists() and not args.force_reset:
        ex = load_state(sp)
        if ex.get("source_video_sha256") != vh:
            print("ERROR: existing pipeline_state.json belongs to a different video.", file=sys.stderr)
            return 1
        print(json.dumps({"action": "resumed", "state_path": str(sp)}, indent=2))
        return 0
    stages = {sid: {"skill": STAGE_SPECS[sid]["skill"], "status": "pending", "required_inputs": STAGE_SPECS[sid]["inputs"], "expected_outputs": STAGE_SPECS[sid]["outputs"], "completed_at_utc": None, "error": None} for sid in PROFILES[args.profile]}
    state = {"schema_version": "1.0.0", "profile": args.profile, "source_video": str(vp), "source_video_sha256": vh, "artifacts_dir": str(ad), "created_at_utc": utc_now(), "updated_at_utc": utc_now(), "stage_order": PROFILES[args.profile], "stages": stages}
    save_state(sp, state)
    print(json.dumps({"action": "initialized", "state_path": str(sp)}, indent=2))
    return 0

def cmd_next(args: argparse.Namespace) -> int:
    st = load_state(args.state)
    ad = Path(st["artifacts_dir"])
    for sid in st["stage_order"]:
        e = st["stages"][sid]
        if e["status"] == "failed":
            print(json.dumps({"action": "halted_on_failure", "stage": sid, "error": e["error"]}, indent=2))
            return 1
        if e["status"] == "pending":
            miss = [r for r in e["required_inputs"] if not (ad / r).exists()]
            if miss:
                print(json.dumps({"action": "blocked_missing_inputs", "stage": sid, "missing_inputs": miss}, indent=2))
                return 1
            print(json.dumps({"action": "run_stage", "stage": sid, "skill": e["skill"]}, indent=2))
            return 0
    print(json.dumps({"action": "pipeline_complete", "profile": st["profile"]}, indent=2))
    return 0

def cmd_complete(args: argparse.Namespace) -> int:
    st = load_state(args.state)
    ad = Path(st["artifacts_dir"])
    miss = [r for r in st["stages"][args.stage]["expected_outputs"] if not (ad / r).exists() or (ad / r).stat().st_size == 0]
    if miss:
        print(f"ERROR: missing outputs: {miss}", file=sys.stderr)
        return 1
    st["stages"][args.stage]["status"] = "completed"
    st["stages"][args.stage]["completed_at_utc"] = utc_now()
    save_state(args.state, st)
    print(json.dumps({"stage": args.stage, "status": "completed"}, indent=2))
    return 0

def cmd_fail(args: argparse.Namespace) -> int:
    st = load_state(args.state)
    st["stages"][args.stage]["status"] = "failed"
    st["stages"][args.stage]["error"] = args.reason
    save_state(args.state, st)
    return 1

def cmd_status(args: argparse.Namespace) -> int:
    st = load_state(args.state)
    s = {"profile": st["profile"], "completed": [k for k in st["stage_order"] if st["stages"][k]["status"] == "completed"], "pending": [k for k in st["stage_order"] if st["stages"][k]["status"] == "pending"], "failed": [k for k in st["stage_order"] if st["stages"][k]["status"] == "failed"]}
    print(json.dumps(s, indent=2))
    return 1 if s["failed"] else 0

def main() -> int:
    p = argparse.ArgumentParser(description="Manage CutLens pipeline checkpoints.")
    sub = p.add_subparsers(dest="command", required=True)
    pi = sub.add_parser("init")
    pi.add_argument("--video", type=Path, required=True)
    pi.add_argument("--profile", choices=sorted(PROFILES), default="full")
    pi.add_argument("--artifacts-dir", type=Path, default=Path("artifacts"))
    pi.add_argument("--force-reset", action="store_true")
    pi.set_defaults(func=cmd_init)
    pn = sub.add_parser("next"); pn.add_argument("--state", type=Path, default=Path("artifacts/pipeline_state.json")); pn.set_defaults(func=cmd_next)
    pc = sub.add_parser("complete"); pc.add_argument("--state", type=Path, default=Path("artifacts/pipeline_state.json")); pc.add_argument("--stage", required=True); pc.set_defaults(func=cmd_complete)
    pf = sub.add_parser("fail"); pf.add_argument("--state", type=Path, default=Path("artifacts/pipeline_state.json")); pf.add_argument("--stage", required=True); pf.add_argument("--reason", required=True); pf.set_defaults(func=cmd_fail)
    ps = sub.add_parser("status"); ps.add_argument("--state", type=Path, default=Path("artifacts/pipeline_state.json")); ps.set_defaults(func=cmd_status)
    args = p.parse_args()
    return args.func(args)

if __name__ == "__main__":
    raise SystemExit(main())
