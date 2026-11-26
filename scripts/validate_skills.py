#!/usr/bin/env python3
"""Zero-dependency cross-agent validator for cutlens-skills (agentskills.io)."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ALLOWED_FRONTMATTER_KEYS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}
NAME_REGEX = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_REGEX = re.compile(r"\[[^\]]+\]\((\./[^)#]+)\)")
TEXT_SCAN_SUFFIXES = {".md", ".py", ".json", ".yml", ".yaml", ".txt", ".tsx", ".ts", ".js", ".env"}
SECRET_PATTERNS = [
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "OpenAI/OpenRouter-style API key"),
    (re.compile(r"ghp_[A-Za-z0-9]{30,}"), "GitHub Personal Access Token"),
    (re.compile(r"AIza[0-9A-Za-z\-_]{35}"), "Google API key"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS Access Key ID"),
    (re.compile(r"xox[baprs]-[0-9A-Za-z\-]{10,}"), "Slack token"),
]


def parse_frontmatter(text: str) -> tuple[dict[str, str], list[str], str]:
    errors: list[str] = []
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        return {}, ["SKILL.md must start at line 1 with '---' YAML frontmatter."], text

    lines = text.splitlines()
    end_idx: int | None = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_idx = idx
            break
    if end_idx is None:
        return {}, ["YAML frontmatter is not closed with '---'."], text

    fields: dict[str, str] = {}
    current_key: str | None = None
    for line in lines[1:end_idx]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith(" ") or line.startswith("\t"):
            if current_key:
                fields[current_key] = (fields[current_key] + " " + line.strip()).strip()
            continue
        if ":" not in line:
            errors.append(f"Malformed frontmatter line: {line}")
            continue
        key, val = line.split(":", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        fields[key] = val
        current_key = key

    body = "\n".join(lines[end_idx + 1 :])
    return fields, errors, body


def validate_openai_yaml(yaml_path: Path) -> list[str]:
    errors: list[str] = []
    content = yaml_path.read_text(encoding="utf-8")
    required_tokens = ("interface:", "display_name:", "short_description:", "policy:", "allow_implicit_invocation:")
    for token in required_tokens:
        if token not in content:
            errors.append(f"{yaml_path}: missing required key '{token}'.")
    return errors


def validate_json_file(json_path: Path) -> list[str]:
    try:
        json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{json_path}: invalid JSON ({exc.msg} at line {exc.lineno}, col {exc.colno})."]
    return []


def validate_skill_dir(skill_dir: Path, max_lines: int = 500, check_scripts: bool = False) -> tuple[list[str], int]:
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return [f"{skill_dir}: missing required SKILL.md"], 0

    raw = skill_md.read_text(encoding="utf-8")
    total_lines = len(raw.splitlines())
    if total_lines > max_lines:
        errors.append(f"{skill_md}: {total_lines} lines exceeds max {max_lines} lines.")

    fields, fm_errors, body = parse_frontmatter(raw)
    errors.extend(f"{skill_md}: {e}" for e in fm_errors)

    unknown = set(fields.keys()) - ALLOWED_FRONTMATTER_KEYS
    if unknown:
        errors.append(f"{skill_md}: non-portable frontmatter keys {sorted(unknown)}")

    name = fields.get("name", "")
    if not name:
        errors.append(f"{skill_md}: missing required 'name' field.")
    else:
        if len(name) > 64 or not NAME_REGEX.match(name):
            errors.append(f"{skill_md}: invalid name '{name}'.")
        if name != skill_dir.name:
            errors.append(f"{skill_md}: frontmatter name '{name}' does not match folder '{skill_dir.name}'.")

    desc = fields.get("description", "")
    if not desc:
        errors.append(f"{skill_md}: missing required 'description' field.")
    elif len(desc) > 1024:
        errors.append(f"{skill_md}: description length {len(desc)} exceeds 1024 chars.")

    if not body.strip():
        errors.append(f"{skill_md}: instruction body is empty.")
    if "## Gotchas" not in body:
        errors.append(f"{skill_md}: missing required '## Gotchas' section.")

    for rel_link in LINK_REGEX.findall(body):
        target = (skill_dir / rel_link).resolve()
        if not target.exists():
            errors.append(f"{skill_md}: broken relative link '{rel_link}'.")

    openai_yaml = skill_dir / "agents" / "openai.yaml"
    if openai_yaml.exists():
        errors.extend(validate_openai_yaml(openai_yaml))

    for file_path in sorted(skill_dir.rglob("*")):
        if not file_path.is_file():
            continue
        if file_path.suffix == ".json":
            errors.extend(validate_json_file(file_path))
        if file_path.suffix in TEXT_SCAN_SUFFIXES:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            for pattern, label in SECRET_PATTERNS:
                if pattern.search(content):
                    errors.append(f"{file_path}: potential hardcoded secret detected ({label}).")
        if check_scripts and file_path.parent.name == "scripts" and file_path.suffix == ".py":
            proc = subprocess.run(
                [sys.executable, str(file_path), "--help"],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            if proc.returncode != 0:
                errors.append(f"{file_path}: '--help' failed with exit code {proc.returncode}.")

    return errors, len(desc)


def validate_manifest(manifest_path: Path, skills_dir: Path, strict_manifest: bool) -> list[str]:
    if not manifest_path.exists():
        return [f"Missing manifest file: {manifest_path}"]
    errors = validate_json_file(manifest_path)
    if errors:
        return errors

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if strict_manifest:
        for pack in data.get("packs", []):
            for skill in pack.get("skills", []):
                skill_path = Path(skill["path"])
                if not (skill_path / "SKILL.md").exists():
                    errors.append(f"manifest.json: listed skill missing SKILL.md at '{skill_path}'.")
                if skill.get("has_openai_yaml") and not (skill_path / "agents" / "openai.yaml").exists():
                    errors.append(f"manifest.json: listed skill missing agents/openai.yaml at '{skill_path}'.")
                if skill.get("has_script") and skill.get("script"):
                    script_path = skill_path / skill["script"]
                    if not script_path.exists():
                        errors.append(f"manifest.json: listed script missing at '{script_path}'.")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate cutlens-skills against portable agentskills.io rules.")
    parser.add_argument("--skills-dir", type=Path, default=Path("skills"))
    parser.add_argument("--manifest", type=Path, default=Path("manifest.json"))
    parser.add_argument("--schemas-dir", type=Path, default=Path("schemas"))
    parser.add_argument("--max-lines", type=int, default=500)
    parser.add_argument("--max-total-desc-chars", type=int, default=8000)
    parser.add_argument("--strict-manifest", action="store_true")
    parser.add_argument("--check-scripts", action="store_true")
    args = parser.parse_args()

    all_errors: list[str] = []
    all_errors.extend(validate_manifest(args.manifest, args.skills_dir, args.strict_manifest))

    if args.schemas_dir.exists():
        for schema_file in sorted(args.schemas_dir.glob("*.json")):
            all_errors.extend(validate_json_file(schema_file))

    if not args.skills_dir.exists():
        if args.strict_manifest:
            all_errors.append(f"Skills directory not found: {args.skills_dir}")
        else:
            return 1 if all_errors else 0

    skill_dirs = sorted(p for p in args.skills_dir.iterdir() if p.is_dir() and not p.name.startswith("."))
    total_desc_chars = 0
    for sdir in skill_dirs:
        skill_errors, desc_len = validate_skill_dir(sdir, max_lines=args.max_lines, check_scripts=args.check_scripts)
        all_errors.extend(skill_errors)
        total_desc_chars += desc_len

    if total_desc_chars > args.max_total_desc_chars:
        all_errors.append(f"Combined skill description length ({total_desc_chars}) exceeds budget ({args.max_total_desc_chars}).")

    if all_errors:
        print(f"FAILED: {len(all_errors)} validation issue(s):", file=sys.stderr)
        for err in all_errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"PASSED: validated {len(skill_dirs)} skill(s) cleanly (startup metadata: {total_desc_chars}/{args.max_total_desc_chars} chars).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
