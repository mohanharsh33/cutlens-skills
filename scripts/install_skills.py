#!/usr/bin/env python3
"""Zero-dependency cross-platform installer and zip packager for cutlens-skills."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent

PACK_ALIASES = {
    "pack1": "pack-01-core-forensics",
    "pack-1": "pack-01-core-forensics",
    "core": "pack-01-core-forensics",
    "pack-01-core-forensics": "pack-01-core-forensics",
    "pack2": "pack-02-reverse-prompt-qa",
    "pack-2": "pack-02-reverse-prompt-qa",
    "prompts": "pack-02-reverse-prompt-qa",
    "pack-02-reverse-prompt-qa": "pack-02-reverse-prompt-qa",
    "pack3": "pack-03-specialists",
    "pack-3": "pack-03-specialists",
    "specialists": "pack-03-specialists",
    "pack-03-specialists": "pack-03-specialists",
}

CLIENT_PATHS = {
    "claude-code": {"project": Path(".claude/skills"), "global": Path.home() / ".claude" / "skills"},
    "codex": {"project": Path(".agents/skills"), "global": Path.home() / ".agents" / "skills"},
    "cursor": {"project": Path(".cursor/skills"), "global": Path.home() / ".cursor" / "skills"},
    "copilot": {"project": Path(".github/skills"), "global": None},
    "gemini-cli": {"project": Path(".gemini/skills"), "global": Path.home() / ".gemini" / "skills"},
    "gemini-skills": {"project": Path("dist/gemini-skills-zips"), "global": None},
    "claude-ai": {"project": Path("dist/claude-ai-zips"), "global": None},
}


def load_manifest(manifest_path: Path) -> dict[str, Any]:
    if not manifest_path.exists():
        print(f"ERROR: manifest.json not found at {manifest_path}", file=sys.stderr)
        raise SystemExit(2)
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def resolve_selected_skills(manifest: dict[str, Any], pack_arg: str, skills_arg: str | None) -> list[dict[str, Any]]:
    packs_by_id = {p["id"]: p for p in manifest.get("packs", [])}
    all_skills = [s for p in manifest.get("packs", []) for s in p.get("skills", [])]
    skills_by_name = {s["name"]: s for s in all_skills}

    if skills_arg:
        names = [n.strip() for n in skills_arg.split(",") if n.strip()]
        unknown = [n for n in names if n not in skills_by_name]
        if unknown:
            print(f"ERROR: unknown skill name(s): {unknown}", file=sys.stderr)
            raise SystemExit(2)
        return [skills_by_name[n] for n in names]

    if pack_arg == "all":
        return all_skills

    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for token in [p.strip().lower() for p in pack_arg.split(",") if p.strip()]:
        canonical = PACK_ALIASES.get(token)
        if not canonical or canonical not in packs_by_id:
            print(f"ERROR: unknown pack '{token}'.", file=sys.stderr)
            raise SystemExit(2)
        for skill in packs_by_id[canonical]["skills"]:
            if skill["name"] not in seen:
                seen.add(skill["name"])
                selected.append(skill)
    return selected


def resolve_destination(client: str, scope: str, project_dir: Path, custom_dest: Path | None) -> Path:
    if custom_dest is not None:
        return custom_dest.resolve()
    mapping = CLIENT_PATHS[client]
    if scope == "global":
        if mapping["global"] is None:
            print(f"ERROR: client '{client}' has no default global path; use --scope project or --dest.", file=sys.stderr)
            raise SystemExit(2)
        return mapping["global"].resolve()
    assert mapping["project"] is not None
    return (project_dir.resolve() / mapping["project"]).resolve()


def main() -> int:
    parser = argparse.ArgumentParser(description="Install or package cutlens-skills across AI coding clients.")
    parser.add_argument("--client", choices=sorted(CLIENT_PATHS.keys()), default="codex")
    parser.add_argument("--scope", choices=["project", "global"], default="project")
    parser.add_argument("--pack", default="all")
    parser.add_argument("--skills", default=None)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--dest", type=Path, default=None)
    parser.add_argument("--manifest", type=Path, default=REPO_ROOT / "manifest.json")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--uninstall", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    if args.list:
        for pack in manifest.get("packs", []):
            print(f"[{pack['id']}] {pack['name']}")
            for s in pack["skills"]:
                print(f"  - {s['name']}")
        return 0

    selected = resolve_selected_skills(manifest, args.pack, args.skills)
    dest_root = resolve_destination(args.client, args.scope, args.project_dir, args.dest)
    zip_mode = args.client in {"gemini-skills", "claude-ai"}
    gemini_chat_safe = args.client == "gemini-skills"

    results = []
    for skill in selected:
        src_dir = (REPO_ROOT / skill["path"]).resolve()
        if not (src_dir / "SKILL.md").exists():
            print(f"ERROR: source skill missing: {src_dir}", file=sys.stderr)
            return 1
        if zip_mode:
            target = dest_root / f"{skill['name']}.zip"
            if args.uninstall:
                if target.exists() and not args.dry_run:
                    target.unlink()
                status = "removed" if target.exists() else "not_found"
            elif target.exists() and not args.force:
                status = "skipped_exists"
            else:
                if not args.dry_run:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                        for item in sorted(src_dir.rglob("*")):
                            if not item.is_file() or "__pycache__" in item.parts or item.suffix == ".pyc":
                                continue
                            if gemini_chat_safe and item.suffix in {".py", ".sh", ".ps1", ".bat"}:
                                continue
                            zf.write(item, arcname=(Path(src_dir.name) / item.relative_to(src_dir)).as_posix())
                status = "packaged"
        else:
            target = dest_root / skill["name"]
            if args.uninstall:
                if target.exists() and not args.dry_run:
                    shutil.rmtree(target)
                status = "removed"
            elif target.exists() and not args.force:
                status = "skipped_exists"
            else:
                if not args.dry_run:
                    if target.exists():
                        shutil.rmtree(target)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(src_dir, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
                status = "installed"
        results.append({"skill": skill["name"], "status": status, "target": target.as_posix()})

    print(json.dumps({"client": args.client, "destination": dest_root.as_posix(), "count": len(results), "items": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
