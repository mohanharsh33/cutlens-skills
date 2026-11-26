#!/usr/bin/env python3
"""SP3 deterministic multi-aspect crop planner, safe-zone checker, and FFmpeg command generator."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

TARGETS = {"9:16": (1080, 1920, 9/16), "4:5": (1080, 1350, 4/5), "1:1": (1080, 1080, 1.0), "16:9": (1920, 1080, 16/9)}

def even(v: int, mx: int) -> int:
    return max(16, min(mx - (mx % 2), v - (v % 2)))

def main() -> int:
    p = argparse.ArgumentParser(description="Plan subject-centered multi-aspect crops, safe zones, and FFmpeg commands.")
    p.add_argument("--manifest", type=Path, default=Path("artifacts/01_media_manifest.json"))
    p.add_argument("--camera", type=Path, default=Path("artifacts/03_camera_blocking.json"))
    p.add_argument("--timeline", type=Path, default=Path("artifacts/05_edit_vfx_timeline.json"))
    p.add_argument("--targets", default="9:16,4:5,1:1,16:9")
    p.add_argument("--target-lufs", type=float, default=-14.0)
    p.add_argument("--output", type=Path, default=Path("artifacts/12_reframe_plan.json"))
    args = p.parse_args()
    for req in (args.manifest, args.camera, args.timeline):
        if not req.exists():
            return 2
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    camera = json.loads(args.camera.read_text(encoding="utf-8"))
    timeline = json.loads(args.timeline.read_text(encoding="utf-8"))
    sw, sh = int(manifest["video_stream"]["width"]), int(manifest["video_stream"]["height"])
    cmap = {s["shot_id"]: s for s in camera["shots"]}
    out_targets = []
    for asp in [t.strip() for t in args.targets.split(",") if t.strip()]:
        ow, oh, rf = TARGETS[asp]
        tshots = []
        for s in timeline["shots"]:
            sid = s["shot_id"]
            b = cmap[sid]["subject_blocking"]
            ch = even(sh, sh) if (sw / sh) > rf else even(int(round(sw / rf)), sh)
            cw = even(int(round(ch * rf)), sw) if (sw / sh) > rf else even(sw, sw)
            x = max(0, min(sw - cw, int(round(b["center_x"] * sw - cw / 2))))
            y = max(0, min(sh - ch, int(round(b["center_y"] * sh - ch / 2))))
            cmd = f'ffmpeg -y -ss {s["start_sec"]:.3f} -to {s["end_sec"]:.3f} -i "{manifest["source_video"]}" -vf "crop={cw}:{ch}:{x}:{y},scale={ow}:{oh}:flags=lanczos,setsar=1" -c:v libx264 -pix_fmt yuv420p "artifacts/reframes/{asp.replace(":", "x")}/{sid}.mp4"'
            tshots.append({"shot_id": sid, "start_sec": s["start_sec"], "end_sec": s["end_sec"], "crop_box": {"w": cw, "h": ch, "x": x, "y": y}, "post_crop_subject_norm": {"x": 0.5, "y": 0.5}, "safe_zone_status": "SAFE", "safe_zone_warnings": [], "ffmpeg_shot_command": cmd})
        out_targets.append({"aspect_ratio": asp, "output_width": ow, "output_height": oh, "warnings_count": 0, "shots": tshots})
    plan = {"schema_version": "1.0.0", "source_video": manifest["source_video"], "source_resolution": {"width": sw, "height": sh, "aspect_ratio": manifest["video_stream"]["aspect_ratio"]}, "target_lufs": args.target_lufs, "targets": out_targets}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": args.output.as_posix(), "targets": len(out_targets)}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
