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

- Bugs: when you fix an error the user reported, first file an agent bug report issue from the user's account (`gh issue create -R BrainCOGS/U19-Data-Viewer`, template `.github/ISSUE_TEMPLATE/agent_bug_report.md`). Put the error exactly as the user pasted it under **Reported error**; don't ask for or invent a Slack link. Then fix it with the `bugfix-from-slack` skill (`.claude/skills/bugfix-from-slack/`, vendored from [agent-tooling](https://github.com/BrainCOGS/agent-tooling)); the PR says `Fixes #<issue>`. Commits, pushes, issues and PRs all go through the user's account.
- Commits end with one `Assisted-by: <Harness>:<model>` trailer per agent, e.g. `Assisted-by: ClaudeCode:claude-opus-5-5`. No AI co-authors, and no `Generated with` lines.
- PRs target `master` on `BrainCOGS/U19-Data-Viewer`, opened from the user's own account.
