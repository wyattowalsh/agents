# wagents init Bootstrap Runbook

Planned one-command bootstrap for new clones and greenfield projects. **The `wagents init` CLI may not exist yet** — this runbook documents the intended workflow maintainers should follow manually until the command ships (IDEAS W13 T-760).

## Goals

- Detect or clone the agents bundle root.
- Install Python tooling (`uv`, `wagents` CLI).
- Sync harness projections for the active platform.
- Run validate + doctor gates before first skill/agent work.

## Planned CLI Shape (draft)

```bash
wagents init                          # interactive: detect harness, sync, validate
wagents init --path /path/to/project  # bootstrap a consumer project
wagents init --check                  # exit 1 if bootstrap prerequisites missing
wagents init --format json            # machine-readable status for agents
```

## Manual Bootstrap Until `wagents init` Ships

### 1. Install CLI

```bash
uv tool install wagents --from git+https://github.com/wyattowalsh/agents
wagents self doctor
```

When working outside the canonical clone:

```bash
export WAGENTS_REPO_ROOT=/path/to/agents
```

### 2. Python environment

```bash
cd "$WAGENTS_REPO_ROOT"
uv sync
uv run wagents validate
```

### 3. Harness sync (repo targets)

```bash
uv run python scripts/sync_agent_stack.py --apply --targets repo
uv run wagents hooks validate --harness all
```

Optional home parity (explicit maintainer intent only):

```bash
uv run python scripts/sync_agent_stack.py --apply --targets home
```

### 4. Docs tooling (maintainers)

```bash
uv run wagents docs init
uv run wagents docs generate --no-installed
```

### 5. Skills inventory (read-only)

```bash
uv run wagents skills sync --dry-run --format json
```

Do not run `--apply` unless explicitly requested.

## Success Criteria

| Gate | Command |
| ---- | ------- |
| CLI healthy | `wagents self doctor` |
| Assets valid | `uv run wagents validate` |
| Hooks projected | `uv run wagents hooks validate --harness all` |
| Bridge parity | `uv run python scripts/check_bridge_consistency.py` |

## Related

- `AGENTS.md` §4 Workflow
- `docs/runbooks/asset-authoring-workflow.md`
- `docs/runbooks/install-smoke.md`
- OpenSpec: W13 T-760 (`wagents init` implementation)
