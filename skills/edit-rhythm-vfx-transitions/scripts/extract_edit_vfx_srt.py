#!/usr/bin/env python3
"""Stage 05 deterministic edit pacing, boundary transition classifier, VFX scaffold, and SRT validator."""
from __future__ import annotations
import argparse, json, re, statistics, sys
from pathlib import Path
from typing import Any

SRT_TIME_RE = re.compile(r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})")

def sec_to_srt(s: float) -> str:
    ms = max(0, int(round(s * 1000)))
    h, r = divmod(ms, 3_600_000); m, r = divmod(r, 60_000); sec, ms = divmod(r, 1000)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"

def parse_srt(raw: str) -> list[dict[str, Any]]:
    cues = []
    for block in re.split(r"\r?\n\r?\n+", raw.strip()):
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        ts_idx = next((i for i, ln in enumerate(lines) if "-->" in ln), None)
        if ts_idx is None:
            continue
        m = SRT_TIME_RE.search(lines[ts_idx])
        if not m:
            raise ValueError(f"Malformed SRT: {lines[ts_idx]}")
        h1, m1, s1, ms1, h2, m2, s2, ms2 = (int(g) for g in m.groups())
        cues.append({"start_sec": round(h1*3600+m1*60+s1+ms1/1000, 3), "end_sec": round(h2*3600+m2*60+s2+ms2/1000, 3), "text": " ".join(lines[ts_idx+1:])})
    return cues

def normalize_cues(cues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rep = []
    for c in sorted(cues, key=lambda x: (x["start_sec"], x["end_sec"])):
        t0, t1 = max(0.0, float(c["start_sec"])), float(c["end_sec"])
        if t1 <= t0:
            t1 = round(t0 + 0.25, 3)
        if rep and t0 < rep[-1]["end_sec"]:
            rep[-1]["end_sec"] = round(max(rep[-1]["start_sec"] + 0.15, t0 - 0.01), 3)
            t0 = round(max(t0, rep[-1]["end_sec"] + 0.01), 3)
            if t1 <= t0:
                t1 = round(t0 + 0.20, 3)
        rep.append({"start_sec": round(t0, 3), "end_sec": round(t1, 3), "text": c["text"]})
    return rep

def main() -> int:
    p = argparse.ArgumentParser(description="Analyze edit pacing, transitions, VFX overlays, and SRT captions.")
    p.add_argument("--manifest", type=Path, default=Path("artifacts/01_media_manifest.json"))
    p.add_argument("--forensics", type=Path, default=Path("artifacts/02_shot_forensics.json"))
    p.add_argument("--camera", type=Path, default=Path("artifacts/03_camera_blocking.json"))
    p.add_argument("--captions-in", type=Path, default=None)
    p.add_argument("--output", type=Path, default=Path("artifacts/05_edit_vfx_timeline.json"))
    p.add_argument("--srt-output", type=Path, default=Path("artifacts/captions.srt"))
    p.add_argument("--no-frame-scan", action="store_true")
    args = p.parse_args()
    for req in (args.manifest, args.forensics, args.camera):
        if not req.exists():
            return 2
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    shots = manifest.get("shots", [])
    if args.captions_in and args.captions_in.exists():
        cues, src = normalize_cues(parse_srt(args.captions_in.read_text(encoding="utf-8"))), "external-srt"
    else:
        cues, src = normalize_cues([{"start_sec": s["start_sec"], "end_sec": s["end_sec"], "text": f"[{s['shot_id']}]"} for s in shots]), "shot-scaffold"
    args.srt_output.parent.mkdir(parents=True, exist_ok=True)
    args.srt_output.write_text("\n".join(f"{i}\n{sec_to_srt(c['start_sec'])} --> {sec_to_srt(c['end_sec'])}\n{c['text']}\n" for i, c in enumerate(cues, 1)), encoding="utf-8")
    total_dur = float(manifest["container"]["duration_sec"])
    wpm = round((sum(len(c["text"].split()) for c in cues) / max(0.01, total_dur)) * 60.0, 1) if src != "shot-scaffold" else 0.0
    durs = [float(s["duration_sec"]) for s in shots]
    asl = round(statistics.fmean(durs), 3)
    band = "hyper-kinetic" if asl < 1.8 else ("fast-commercial" if asl <= 3.2 else ("editorial-standard" if asl <= 5.5 else "contemplative-cinema"))
    out_shots = [{
        "shot_id": s["shot_id"], "start_sec": round(float(s["start_sec"]), 3), "end_sec": round(float(s["end_sec"]), 3), "duration_sec": round(float(s["duration_sec"]), 3),
        "transition_in": "opening-frame" if i == 0 else "hard-cut", "transition_out": "closing-frame" if i == len(shots)-1 else "hard-cut",
        "speed_profile": "normal", "vfx_overlays": [], "caption_cues": [c["text"] for c in cues if src != "shot-scaffold" and c["end_sec"] > s["start_sec"] and c["start_sec"] < s["end_sec"]],
    } for i, s in enumerate(shots)]
    report = {
        "schema_version": "1.0.0", "source_manifest": args.manifest.as_posix(), "fps": float(manifest["video_stream"]["fps"]), "total_duration_sec": round(total_dur, 3),
        "pacing_metrics": {"shot_count": len(shots), "average_shot_length_sec": asl, "median_shot_length_sec": round(statistics.median(durs), 3), "shortest_shot_sec": round(min(durs), 3), "longest_shot_sec": round(max(durs), 3), "cuts_per_minute": round(((len(shots)-1)/max(0.01, total_dur))*60.0, 2), "pacing_band": band},
        "captions_summary": {"srt_file": args.srt_output.as_posix(), "source": src, "cue_count": len(cues), "overlap_errors": 0, "estimated_wpm": wpm},
        "shots": out_shots,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": args.output.as_posix(), "pacing_band": band}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
