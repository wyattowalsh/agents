# Design

## Runtime model

The installed wheel contains only `wagents/`. Commands that need repo assets call `get_repo_root()` which resolves a clone via env, cwd markers, or editable fallback.

Repo markers: `skills/` plus one of `agent-bundle.json`, `AGENTS.md`, or (`agents/` + `pyproject.toml`).

## Install surface

Primary install:

```bash
uv tool install wagents --from git+https://github.com/wyattowalsh/agents
```

## Plugins

Third-party packages register `[project.entry-points."wagents.commands"]` callables that receive the root Typer app.

## Telemetry

Opt-in via `WAGENTS_TELEMETRY=1`; append JSONL locally under `~/.cache/wagents/telemetry.jsonl`.