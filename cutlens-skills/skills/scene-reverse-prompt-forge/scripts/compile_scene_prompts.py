#!/usr/bin/env python3
"""Stage 08 deterministic reverse-prompt compiler: 5 video dialects, Markdown bible, and standalone HTML report."""
from __future__ import annotations
import argparse, html, json, sys
from pathlib import Path

NEG = "morphing hands, warped anatomy, inconsistent face, flickering shadows, sudden unwanted zoom, stock watermark, logo artifact"

def trim_words(t: str, n: int) -> str:
    w = t.split()
    return t if len(w) <= n else " ".join(w[:n]).rstrip(",;:") + "."

def main() -> int:
    p = argparse.ArgumentParser(description="Compile scene-by-scene reverse prompts, Markdown blueprint, and HTML report.")
    p.add_argument("--manifest", type=Path, default=Path("artifacts/01_media_manifest.json"))
    p.add_argument("--camera", type=Path, default=Path("artifacts/03_camera_blocking.json"))
    p.add_argument("--color", type=Path, default=Path("artifacts/04_color_lighting.json"))
    p.add_argument("--timeline", type=Path, default=Path("artifacts/05_edit_vfx_timeline.json"))
    p.add_argument("--sound", type=Path, default=Path("artifacts/06_sound_design.json"))
    p.add_argument("--constraints", type=Path, default=Path("artifacts/07_remake_constraints.json"))
    p.add_argument("--json-output", type=Path, default=Path("artifacts/08_scene_prompts.json"))
    p.add_argument("--md-output", type=Path, default=Path("artifacts/08_REMAKE_BLUEPRINT.md"))
    p.add_argument("--html-output", type=Path, default=Path("artifacts/report.html"))
    args = p.parse_args()
    for req in (args.camera, args.color, args.timeline, args.sound, args.constraints):
        if not req.exists():
            return 2
    cam_map = {s["shot_id"]: s for s in json.loads(args.camera.read_text(encoding="utf-8"))["shots"]}
    col_map = {s["shot_id"]: s for s in json.loads(args.color.read_text(encoding="utf-8"))["shots"]}
    tl = json.loads(args.timeline.read_text(encoding="utf-8"))
    snd_map = {s["shot_id"]: s for s in json.loads(args.sound.read_text(encoding="utf-8"))["shots"]}
    con = json.loads(args.constraints.read_text(encoding="utf-8"))
    route_map = {s["shot_id"]: s for s in con["shot_routing"]}
    aspect = json.loads(args.manifest.read_text(encoding="utf-8"))["video_stream"]["aspect_ratio"] if args.manifest.exists() else "16:9"
    alook = {a["token"]: a["locked_description"] for a in con["entity_anchors"]}
    tok = con["entity_anchors"][0]["token"]
    shots_out = []
    for s in tl["shots"]:
        sid = s["shot_id"]
        c, col, r, snd = cam_map[sid], col_map[sid], route_map[sid], snd_map[sid]
        mv = " with ".join(c["camera_movements"])
        w = col["grade_wheels"]
        lt = col["lighting_topology"]
        beat = r["action_beat"]
        shots_out.append({
            "shot_id": sid, "start_sec": s["start_sec"], "end_sec": s["end_sec"], "duration_sec": s["duration_sec"],
            "production_class": r["production_class"], "remake_lane": r["remake_lane"], "remotion_handoff": r["remake_lane"] == "remotion-code-rebuild",
            "camera_movements": c["camera_movements"],
            "cinematography_spec": {"shot_scale": c["shot_scale"], "grade_wheels": w, "kelvin_proxy_k": col["kelvin_proxy_k"], "lighting_topology": lt, "audio_bridge": snd["audio_bridge"]},
            "prompts": {
                "start_keyframe_t2i": f"{tok} ({alook[tok]}). Opening frame of {sid}: {beat}. {c['shot_scale']} {c['camera_angle']}, {c['focal_length_proxy_mm']}, {col['kelvin_proxy_k']}K {lt['key_direction']}, lift {w['lift_shadows']}, gain {w['gain_highlights']} --ar {aspect}",
                "end_keyframe_t2i": f"{tok} ({alook[tok]}). Closing frame of {sid}: {beat}. Identical {c['focal_length_proxy_mm']} optics and {w['lift_shadows']}/{w['gain_highlights']} palette --ar {aspect}",
                "veo_3_1_i2v": f"{mv.capitalize()} on {tok} during {beat}, {c['shot_scale']} {c['focal_length_proxy_mm']}, {col['kelvin_proxy_k']}K {lt['key_direction']}. Audio: clean continuous room tone and crisp foley.",
                "kling_3_0_i2v": f"Element {tok} executes: {beat}. Camera: {mv}, {c['shot_scale']}. Lighting: {col['kelvin_proxy_k']}K {lt['key_direction']}.",
                "seedance_2_5_i2v": f"Subject: {tok}. Action: {beat}. Camera: {c['shot_scale']} {mv}. Lighting: {col['kelvin_proxy_k']}K {lt['key_direction']}.",
                "runway_gen_4_5_i2v": f"{mv.capitalize()} from locked start frame as {tok} executes: {beat}. Hold {c['focal_length_proxy_mm']} focus."[:315],
                "sora_2_t2v": trim_words(f"{alook[tok]} performs {beat} in a {c['shot_scale']} shot with {mv} on {c['focal_length_proxy_mm']} optics and {col['kelvin_proxy_k']}K {lt['key_direction']}.", 78),
                "negative_prompt": NEG,
            },
            "live_shoot_spec": {"framing": c["shot_scale"], "movement": mv, "lut": con["continuity_bible"]["lut_file"]},
        })
    payload = {"schema_version": "1.0.0", "aspect_ratio": aspect, "fps": tl["fps"], "total_duration_sec": tl["total_duration_sec"], "lut_file": con["continuity_bible"]["lut_file"], "entity_anchors": con["entity_anchors"], "shots": shots_out}
    for out_p, txt in [
        (args.json_output, json.dumps(payload, indent=2) + "\n"),
        (args.md_output, "# CutLens Remake Blueprint\n\n" + "\n".join(f"## {x['shot_id']}\n\n{x['prompts']['veo_3_1_i2v']}\n" for x in shots_out)),
        (args.html_output, f"<!DOCTYPE html><html><body><h1>CutLens Report</h1><p>Shots: {len(shots_out)}</p><pre>{html.escape(json.dumps(shots_out, indent=2))}</pre></body></html>"),
    ]:
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(txt, encoding="utf-8")
    print(json.dumps({"compiled_shots": len(shots_out)}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
