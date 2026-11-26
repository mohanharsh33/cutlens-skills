# AGENTS.md

Operating contract for human contributors and AI coding agents (Claude Code, OpenAI Codex, Cursor, GitHub Copilot, Gemini CLI, Gemini Skills) working in `cutlens-skills`.

## Architecture Invariants

1. **Open Standard Portability (`agentskills.io`):**
   - Every skill lives under `skills/<skill-name>/SKILL.md`.
   - YAML frontmatter starts at line 1 (`---`) and uses ONLY the 6 official portable keys: `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`.
   - Include `skills/<skill-name>/agents/openai.yaml` for OpenAI Codex UI metadata and implicit-invocation policy.
2. **Progressive Disclosure & Context Budget:**
   - Keep every `SKILL.md` strictly under **500 lines**.
   - Keep every `description` between **150 and 350 characters** stating WHAT it does, WHEN to trigger, and an explicit negative trigger.
   - Combined startup metadata across all skills in `skills/` must stay under **8,000 characters**.
3. **Deterministic Scripts Over LLM Guesswork:**
   - Implement all parsing, probing, telemetry, math, sanitization, and validation in **Python 3.12+ stdlib-first scripts** under `skills/<skill-name>/scripts/`.
4. **Windows 11, macOS & Linux Parity:**
   - Always use `pathlib.Path` and `encoding="utf-8"`.
5. **Artifact Contract & Fail-Closed Handoffs:**
   - Stages communicate strictly through numbered artifacts in `artifacts/`.
6. **BYOK, Clean-Room MIT & Zero Secrets:**
   - Never hardcode API keys, model IDs, or personal endpoints.

## Required Verification Before Every Commit

```bash
python scripts/validate_skills.py --strict-manifest --check-scripts
python -m compileall -q scripts skills tests
python tests/test_pipeline_smoke.py
```
