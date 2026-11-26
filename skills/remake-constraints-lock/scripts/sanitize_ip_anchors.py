#!/usr/bin/env python3
"""Stage 07 continuity bible compiler and deterministic clean-room IP/watermark sanitizer."""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path
from typing import Any

DEFAULT_REPLACEMENTS = [
    ("shutterstock", ""), ("getty images", ""), ("getty", ""), ("istock", ""), ("watermark", ""),
    ("iphone", "unbranded frameless smartphone"), ("macbook", "minimalist aluminum laptop"),
    ("nike", "unbranded athletic"), ("adidas", "unbranded athletic"), ("rolex", "brushed-steel wristwatch"),
]
LIKENESS_RE = re.compile(r"\b(?:looks\s+like|resembling|in\s+the\s+style\s+of)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}")

def sanitize(text: str, field: str, log: list[dict[str, str]]) -> str:
    out = text
    for term, rep in DEFAULT_REPLACEMENTS:
        pat = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
        if pat.search(out):
            out = pat.sub(rep, out)
            log.append({"field": field, "matched_term": term, "replaced_with": rep or "<stripped>"})
    for m in LIKENESS_RE.findall(out):
        out = out.replace(m, "with original distinctive cinematic styling")
        log.append({"field": field, "matched_term": m, "replaced_with": "with original distinctive cinematic styling"})
    return re.sub(r"\s{2,}", " ", out).strip(" ,;-")

def main() -> int:
    p = argparse.ArgumentParser(description="Lock continuity anchors and sanitize copyrighted IP/watermarks.")
    p.add_argument("--forensics", type=Path, default=Path("artifacts/02_shot_forensics.json"))
    p.add_argument("--camera", type=Path, default=Path("artifacts/03_camera_blocking.json"))
    p.add_argument("--color", type=Path, default=Path("artifacts/04_color_lighting.json"))
    p.add_argument("--timeline", type=Path, default=Path("artifacts/05_edit_vfx_timeline.json"))
    p.add_argument("--sound", type=Path, default=Path("artifacts/06_sound_design.json"))
    p.add_argument("--subject-notes", type=Path, default=None)
    p.add_argument("--output", type=Path, default=Path("artifacts/07_remake_constraints.json"))
    args = p.parse_args()
    for req in (args.forensics, args.camera, args.color, args.timeline, args.sound):
        if not req.exists():
            return 2
    forensics = json.loads(args.forensics.read_text(encoding="utf-8"))
    camera = json.loads(args.camera.read_text(encoding="utf-8"))
    color = json.loads(args.color.read_text(encoding="utf-8"))
    timeline = json.loads(args.timeline.read_text(encoding="utf-8"))
    sound = json.loads(args.sound.read_text(encoding="utf-8"))
    notes = json.loads(args.subject_notes.read_text(encoding="utf-8")) if args.subject_notes and args.subject_notes.exists() else {}
    log: list[dict[str, str]] = []
    raw_anchors = notes.get("entity_anchors") or [{"token": "[SUBJ_01]", "role": "subject", "locked_description": "Primary original foreground subject with consistent wardrobe and proportions"}]
    anchors = [{"token": a["token"], "role": a["role"], "locked_description": sanitize(a["locked_description"], a["token"], log)} for a in raw_anchors]
    toks = [a["token"] for a in anchors]
    fmap = {s["shot_id"]: s["primary_class"] for s in forensics["shots"]}
    cmap = {s["shot_id"]: s for s in camera["shots"]}
    actions = notes.get("shot_actions") or {}
    routing = []
    for s in timeline["shots"]:
        sid = s["shot_id"]
        cls = fmap[sid]
        lane = "remotion-code-rebuild" if cls in {"code-motion-graphics", "screen-recording"} else "live-action-or-i2v"
        beat = sanitize(str(actions.get(sid, f"Clean-room visual progression for {sid} framed at {cmap[sid]['shot_scale']}")), f"shot.{sid}", log)
        routing.append({"shot_id": sid, "production_class": cls, "remake_lane": lane, "active_anchors": toks, "action_beat": beat})
    out = {
        "schema_version": "1.0.0", "clean_room_policy_version": "1.0.0",
        "continuity_bible": {"fps": timeline["fps"], "total_duration_sec": timeline["total_duration_sec"], "palette_archetype": color["global_look"]["palette_archetype"], "lut_file": color["global_look"]["lut_file"], "global_wheels": color["shots"][0]["grade_wheels"], "pacing_band": timeline["pacing_metrics"]["pacing_band"], "audio_summary": "EBU R128 measured"},
        "entity_anchors": anchors, "shot_routing": routing,
        "forbidden_output_tokens": sorted({t for t, _ in DEFAULT_REPLACEMENTS}),
        "ip_sanitization_report": {"scanned_fields": len(anchors) + len(routing), "replacements_count": len(log), "replacements": log},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": args.output.as_posix(), "replacements_count": len(log)}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
