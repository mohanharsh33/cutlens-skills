# cutlens-skills v1.0.0 — Modular Cinema-Grade Video Forensics & Clean-Room Reverse Prompting

`cutlens-skills` is an open-source, MIT-licensed collection of **13 atomic AI agent skills** (3 modular packs) built on the open `agentskills.io` standard.

## Quickstart

```bash
git clone https://github.com/mohanharsh33/cutlens-skills.git
cd cutlens-skills
python scripts/validate_skills.py --strict-manifest --check-scripts
python tests/test_pipeline_smoke.py
python scripts/install_skills.py --client claude-code --pack all
```

Maintained by **Harsh Mohan ([@mohanharsh33](https://github.com/mohanharsh33))** under the MIT License.
