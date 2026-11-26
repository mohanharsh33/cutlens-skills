# cutlens-skills

Modular, cinema-grade video forensics and clean-room reverse-prompting agent skills built on the open `agentskills.io` standard.

![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Spec: agentskills.io](https://img.shields.io/badge/Spec-agentskills.io-blue.svg)
![Python: 3.12+](https://img.shields.io/badge/Python-3.12%2B-3776AB.svg)
![Platform: Windows | macOS | Linux](https://img.shields.io/badge/Platform-Windows%2011%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)
![CI: Validate Skills](https://github.com/mohanharsh33/cutlens-skills/actions/workflows/validate.yml/badge.svg)

---

## Quickstart & Cross-Agent Installation

### 1. Prerequisites (Windows 11, macOS, Linux)

- **Python 3.12+** (`python --version`)
- **FFmpeg & FFprobe** on system `PATH`
  - **Windows 11 (PowerShell):** `winget install Gyan.FFmpeg`
  - **macOS:** `brew install ffmpeg`
  - **Ubuntu/Debian:** `sudo apt install ffmpeg`

### 2. Validate & Test Locally

```bash
python scripts/validate_skills.py --strict-manifest --check-scripts
python -m compileall -q scripts skills tests
python tests/test_pipeline_smoke.py
```

### 3. One-Command Multi-Client Installer

```bash
python scripts/install_skills.py --client claude-code --pack all
python scripts/install_skills.py --client codex --pack all
python scripts/install_skills.py --client cursor --pack pack1,pack2
python scripts/install_skills.py --client copilot --pack all
python scripts/install_skills.py --client gemini-cli --pack all
python scripts/install_skills.py --client gemini-skills --pack all
```

---

## Skill Pack Catalog (13 Atomic Skills)

See [`CATALOG.md`](./CATALOG.md) for the complete artifact contract and negative-trigger matrix.

- **Pack 1 (`pack-01-core-forensics`, 7 skills):** `video-breakdown-orchestrator`, `video-media-ingest`, `shot-forensics-classify`, `camera-lens-blocking-audit`, `color-grade-lighting-audit`, `edit-rhythm-vfx-transitions`, `sound-design-foley-audit`.
- **Pack 2 (`pack-02-reverse-prompt-qa`, 3 skills):** `remake-constraints-lock`, `scene-reverse-prompt-forge`, `remake-plan-qa-audit`.
- **Pack 3 (`pack-03-specialists`, 3 skills):** `viral-hook-pacing-audit`, `remotion-code-rebuilder`, `multi-aspect-reframe-plan`.

---

## Forensic Epistemics & Clean-Room IP Notice

- **Non-Proof Forensics:** Shot production classifications are evidence-backed engineering estimates, not cryptographic deepfake proof.
- **Clean-Room Remakes Only:** Study cinematography, pacing, lighting, color science, and motion grammar to produce original work. `remake-constraints-lock` and `remake-plan-qa-audit` enforce IP and watermark sanitization before prompt export.

---

## License

Released under the [MIT License](./LICENSE).

Maintained by **[Harsh Mohan (@mohanharsh33)](https://github.com/mohanharsh33)**
