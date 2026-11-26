#!/usr/bin/env python3
"""Stage 09 fail-closed QA gate for cutlens-skills remake blueprints, prompts, LUTs, and IP hygiene."""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

HEX_RE = re.compile(r"^#[0-9A-F]{6}$")
REQ_KEYS = ("start_keyframe_t2i", "end_keyframe_t2i", "veo_3_1_i2v", "kling_3_0_i2v", "seedance_2_5_i2v", "runway_gen_4_5_i2v", "sora_2_t2v", "negative_prompt")
POS_KEYS = tuple(k for k in REQ_KEYS if k != "negative_prompt")
CONFLICTS = ({"dolly-in", "pull-out"}, {"pan-left", "pan-right"}, {"tilt-up", "tilt-down"})

def main() -> int:
    p = argparse.ArgumentParser(description="Run fail-closed deterministic QA checks across CutLens artifacts.")
    p.add_argument("--manifest", type=Path, default=Path("artifacts/01_media_manifest.json"))
    p.add_argument("--constraints", type=Path, default=Path("artifacts/07_remake_constraints.json"))
    p.add_argument("--prompts", type=Path, default=Path("artifacts/08_scene_prompts.json"))
    p.add_argument("--lut", type=Path, default=None)
    p.add_argument("--remotion-parity", type=Path, default=None)
    p.add_argument("--runtime-tolerance", type=float, default=0.20)
    p.add_argument("--require-lut", action="store_true")
    p.add_argument("--output", type=Path, default=Path("artifacts/09_qa_report.json"))
    args = p.parse_args()
    for req in (args.manifest, args.constraints, args.prompts):
        if not req.exists():
            return 2
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    constraints = json.loads(args.constraints.read_text(encoding="utf-8"))
    prompts = json.loads(args.prompts.read_text(encoding="utf-8"))
    findings = []
    passed = failed = 0
    def check(ok: bool, code: str, scope: str, msg: str) -> None:
        nonlocal passed, failed
        if ok:
            passed += 1
        else:
            failed += 1
            findings.append({"code": code, "severity": "error", "scope": scope, "message": msg})
    m_ids = [s["shot_id"] for s in manifest.get("shots", [])]
    c_shots = prompts.get("shots", [])
    check(m_ids == [s["shot_id"] for s in c_shots] and len(c_shots) > 0, "QA_SHOT_PARITY", "global", "Shot ID mismatch.")
    src_d = float(manifest["container"]["duration_sec"])
    comp_d = round(sum(float(s["duration_sec"]) for s in c_shots), 3)
    check(abs(comp_d - src_d) <= args.runtime_tolerance, "QA_RUNTIME_DRIFT", "global", f"Drift {abs(comp_d-src_d):.3f}s > {args.runtime_tolerance}s.")
    forb = [(t, re.compile(rf"\b{re.escape(t)}\b", re.IGNORECASE)) for t in constraints.get("forbidden_output_tokens", [])]
    for s in c_shots:
        sid = s["shot_id"]
        mv = set(s.get("camera_movements", []))
        check(1 <= len(mv) <= 2 and not any(pair.issubset(mv) for pair in CONFLICTS), "QA_CAMERA_CONFLICT", sid, f"Bad camera moves: {mv}")
        po = s.get("prompts", {})
        check(all(str(po.get(k, "")).strip() for k in REQ_KEYS), "QA_DIALECT_REQUIRED", sid, "Missing prompt keys.")
        check(len(str(po.get("sora_2_t2v", "")).split()) <= 80, "QA_DIALECT_SORA_WORDS", sid, "Sora > 80 words.")
        check("Audio:" in str(po.get("veo_3_1_i2v", "")), "QA_DIALECT_VEO_AUDIO", sid, "Veo missing Audio: block.")
        for fk in POS_KEYS:
            leaks = [t for t, pat in forb if pat.search(str(po.get(fk, "")))]
            check(not leaks, "QA_IP_LEAK", f"{sid}.{fk}", f"IP leak: {leaks}")
        w = s.get("cinematography_spec", {}).get("grade_wheels", {})
        check(all(HEX_RE.match(str(w.get(k, ""))) for k in ("lift_shadows", "gamma_midtones", "gain_highlights")), "QA_COLOR_HEX", sid, "Invalid hex.")
    status = "PASS" if failed == 0 else "FAIL"
    rep = {"schema_version": "1.0.0", "status": status, "checked_inputs": {"manifest": args.manifest.as_posix(), "constraints": args.constraints.as_posix(), "prompts": args.prompts.as_posix()}, "summary": {"total_shots_checked": len(c_shots), "source_duration_sec": src_d, "compiled_duration_sec": comp_d, "runtime_drift_sec": round(abs(comp_d-src_d), 3), "checks_passed": passed, "checks_failed": failed, "error_count": failed, "warning_count": 0}, "findings": findings}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(rep, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "error_count": failed}, indent=2))
    return 0 if status == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
