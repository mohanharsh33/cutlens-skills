#!/usr/bin/env python3
"""Stage 01 deterministic media ingest: FFprobe telemetry, provenance tags, cuts, and keyframes."""
from __future__ import annotations
import argparse, json, math, os, re, shutil, statistics, subprocess, sys
from fractions import Fraction
from pathlib import Path
from typing import Any

AIGC_TOKENS = ("c2pa", "aigc", "ai_generated", "content_credentials", "sora", "veo", "kling", "runway", "seedance", "pika", "luma", "hailuo", "minimax", "heygen", "synthesia", "comfyui")
EDITOR_TOKENS = ("remotion", "after effects", "premiere", "davinci", "resolve", "final cut", "capcut", "blender", "obs", "camtasia", "screenflow")
RECOMPRESS_TOKENS = ("lavf", "handbrake", "tiktok", "douyin", "instagram", "bytevc", "youtube")
PTS_TIME_RE = re.compile(r"pts_time:([0-9]+(?:\.[0-9]+)?)")

def resolve_binary(env_var: str, default_name: str) -> str:
    c = os.environ.get(env_var, "").strip()
    if c and Path(c).exists():
        return c
    found = shutil.which(default_name)
    if not found:
        print(f"ERROR: '{default_name}' not found on PATH.", file=sys.stderr)
        raise SystemExit(2)
    return found

def parse_fraction(raw: str | None) -> float:
    if not raw or raw in {"0/0", "N/A"}:
        return 0.0
    try:
        return float(Fraction(raw))
    except (ValueError, ZeroDivisionError):
        return 0.0

def simplify_aspect(w: int, h: int) -> str:
    ratio = w / h
    for target, label in [(16/9, "16:9"), (9/16, "9:16"), (4/5, "4:5"), (1.0, "1:1"), (4/3, "4:3")]:
        if abs(ratio - target) <= 0.03:
            return label
    g = math.gcd(w, h)
    return f"{w//g}:{h//g}"

def probe_cadence(ffprobe: str, vp: Path) -> tuple[str, float]:
    proc = subprocess.run([ffprobe, "-v", "error", "-select_streams", "v:0", "-read_intervals", "%+#240", "-show_entries", "packet=pts_time", "-of", "csv=p=0", str(vp)], capture_output=True, text=True, check=False)
    pts = []
    for ln in proc.stdout.splitlines():
        try:
            pts.append(float(ln.strip().split(",")[0]))
        except ValueError:
            pass
    pts = sorted(set(pts))
    deltas = [round(b - a, 6) for a, b in zip(pts, pts[1:]) if b > a]
    if len(deltas) < 5:
        return "UNKNOWN", 0.0
    cv = statistics.pstdev(deltas) / max(1e-6, statistics.fmean(deltas))
    return ("VFR" if cv > 0.08 else "CFR"), round(cv, 5)

def detect_cuts(ffmpeg: str, vp: Path, threshold: float, duration: float, min_shot_sec: float) -> list[tuple[float, float]]:
    proc = subprocess.run([ffmpeg, "-hide_banner", "-i", str(vp), "-vf", f"select='gt(scene,{threshold:.3f})',showinfo", "-vsync", "vfr", "-f", "null", "-"], capture_output=True, text=True, check=False)
    raw_cuts = [float(m.group(1)) for ln in proc.stderr.splitlines() if "showinfo" in ln for m in [PTS_TIME_RE.search(ln)] if m and 0.0 < float(m.group(1)) < duration]
    filt = [0.0]
    for c in sorted(raw_cuts):
        if c - filt[-1] >= min_shot_sec and (duration - c) >= min_shot_sec:
            filt.append(round(c, 3))
    filt.append(round(duration, 3))
    return [(filt[i], filt[i+1]) for i in range(len(filt) - 1)]

def extract_frame(ffmpeg: str, vp: Path, ts: float, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{max(0.0, ts):.3f}", "-i", str(vp), "-frames:v", "1", "-q:v", "3", str(out)], capture_output=True, check=False)

def main() -> int:
    p = argparse.ArgumentParser(description="Probe video container, provenance tags, cuts, and keyframes.")
    p.add_argument("--video", type=Path, required=True)
    p.add_argument("--output", type=Path, default=Path("artifacts/01_media_manifest.json"))
    p.add_argument("--keyframes-dir", type=Path, default=Path("artifacts/keyframes"))
    p.add_argument("--scene-threshold", type=float, default=0.30)
    p.add_argument("--min-shot-sec", type=float, default=0.50)
    p.add_argument("--skip-keyframes", action="store_true")
    args = p.parse_args()
    vp = args.video.resolve()
    ffprobe, ffmpeg = resolve_binary("CUTLENS_FFPROBE_BIN", "ffprobe"), resolve_binary("CUTLENS_FFMPEG_BIN", "ffmpeg")
    proc = subprocess.run([ffprobe, "-v", "error", "-show_format", "-show_streams", "-of", "json", str(vp)], capture_output=True, text=True, check=False)
    data = json.loads(proc.stdout)
    streams, fmt = data.get("streams", []), data.get("format", {})
    vs = next((s for s in streams if s.get("codec_type") == "video"), None)
    as_ = next((s for s in streams if s.get("codec_type") == "audio"), None)
    if vs is None:
        return 1
    dur = round(float(fmt.get("duration") or vs.get("duration") or 0.0), 3)
    w, h = int(vs["width"]), int(vs["height"])
    fps = round(parse_fraction(vs.get("avg_frame_rate")) or parse_fraction(vs.get("r_frame_rate")), 3)
    cadence, cv = probe_cadence(ffprobe, vp)
    tags = {str(k): str(v) for src in (fmt.get("tags") or {}, vs.get("tags") or {}) for k, v in src.items()}
    blob = " ".join(f"{k} {v}" for k, v in tags.items()).lower()
    intervals = detect_cuts(ffmpeg, vp, args.scene_threshold, dur, args.min_shot_sec)
    shots = []
    for idx, (t0, t1) in enumerate(intervals, start=1):
        sid = f"SHOT_{idx:03d}"
        sdur = round(t1 - t0, 3)
        kfs = {k: args.keyframes_dir / f"{sid}_{k}.jpg" for k in ("start", "mid", "end")}
        if not args.skip_keyframes:
            extract_frame(ffmpeg, vp, t0 + min(0.08, sdur * 0.1), kfs["start"])
            extract_frame(ffmpeg, vp, t0 + sdur * 0.5, kfs["mid"])
            extract_frame(ffmpeg, vp, max(t0, t1 - min(0.12, sdur * 0.15)), kfs["end"])
        shots.append({"shot_id": sid, "index": idx, "start_sec": t0, "end_sec": t1, "duration_sec": sdur, "scene_score": None, "keyframes": {k: v.as_posix() for k, v in kfs.items()}})
    manifest = {
        "schema_version": "1.0.0", "source_video": vp.as_posix(),
        "container": {"format_name": str(fmt.get("format_name", "unknown")), "duration_sec": dur, "size_bytes": int(fmt.get("size") or vp.stat().st_size), "bit_rate_bps": int(fmt.get("bit_rate") or 0)},
        "video_stream": {"codec": str(vs.get("codec_name", "unknown")), "width": w, "height": h, "rotation_deg": 0, "aspect_ratio": simplify_aspect(w, h), "fps": fps, "cadence_mode": cadence, "frame_delta_cv": cv, "pix_fmt": str(vs.get("pix_fmt", "unknown")), "color_space": str(vs.get("color_space", "unknown")), "bit_depth": 8},
        "audio_stream": {"present": as_ is not None, "codec": as_.get("codec_name") if as_ else None, "sample_rate_hz": int(as_["sample_rate"]) if as_ and as_.get("sample_rate") else None, "channels": int(as_["channels"]) if as_ and as_.get("channels") else None},
        "provenance_signals": {"detected_aigc_markers": sorted({t for t in AIGC_TOKENS if t in blob}), "detected_editor_markers": sorted({t for t in EDITOR_TOKENS if t in blob}), "encoder_software": tags.get("encoder", "unknown"), "recompression_likely": any(t in blob for t in RECOMPRESS_TOKENS), "raw_tags": tags},
        "shots": shots,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": args.output.as_posix(), "shot_count": len(shots)}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
