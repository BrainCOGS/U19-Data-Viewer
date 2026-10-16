# U19-Data-Viewer

A Flask web viewer for the U19 DataJoint pipeline data (`viewer/`), hosted on
braincogs01 behind Apache (`apache/`, `docker-compose.yml`). Run it locally with
`uv run viewer/server.py`. Python >= 3.10, managed with uv.

## Setup and tests

```bash
uv sync --locked
uv run --locked pytest      # CI: Python 3.10 and 3.14
```

Lint: `uvx prek run --all-files` (the same as CI's Lint workflow).

## Pins and gotchas

- `datajoint==0.14.10` exactly, as in every BrainCOGS repo.

## Agent workflow

- Errors reported in Slack: use the `bugfix-from-slack` skill (agent-tooling). The agent files nothing itself: commits, pushes and PRs are the user's.
- Commits end with one `Assisted-by: <Harness>:<model>` trailer per agent, e.g. `Assisted-by: ClaudeCode:claude-opus-5-5`. No AI co-authors, and no `Generated with` lines. `prek install` sets up the `ai-attribution` commit-msg hook (`.github/scripts/check_ai_attribution.py`, vendored from agent-tooling), and CI checks every commit of a PR.
- PRs target `master` on `BrainCOGS/U19-Data-Viewer`, opened from the user's own account.
