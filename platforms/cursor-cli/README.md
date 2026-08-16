# Cursor Agent CLI harness

Terminal harness for Cursor Agent CLI (`agent` / `cursor-agent`). Registry id is `cursor-cli`. Skills CLI and hook **render** stay on `cursor`.

## Classify aliases

Harness-master maps these tokens to `["cursor-cli"]`:

| Token | Canonical |
| --- | --- |
| `cursor-cli` | `cursor-cli` |
| `cursor-agent` | `cursor-cli` |
| `cursor-agent-cli` | `cursor-cli` |
| `agent-cli` | `cursor-cli` |
| `agent` | `cursor-cli` |

Editor aliases stay on `cursor`: `cursor`, `cursor-editor`, `cursor-desktop`, `cursor-web` (cloud/Bugbot aliases remain folded there). Deterministic `all` order is `cursor` then `cursor-cli`.

```bash
uv run python skills/harness-master/scripts/discovery/classify_intent.py --args "agent both" --json
```

## Sync does not write cli-config

Repo / home sync uses `wagents/platforms/cursor.py` (`harness="cursor"`):

- **Writes:** `.cursor/cli.json` (project `permissions` only), shared `.cursor/hooks.json`, `.cursor/mcp.json`, agents, skills
- **Must not write:** `~/.cursor/cli-config.json`, live `state.vscdb`

Operators SHOULD set `exploreSubagentModel=inherit` in user-owned `~/.cursor/cli-config.json`.

## Skills stay `-a cursor`

There is no Skills CLI agent id `cursor-cli` and no native `agent` adapter.

```bash
uv run wagents skills sync -a cursor --dry-run
# live install only when the maintainer explicitly asks:
# uv run wagents install -a cursor
# npx skills add github:wyattowalsh/agents ... -a cursor
```

## Doctor

```bash
uv run wagents cursor-cli doctor --format json
```

Redact email, tokens, and API keys. Do not print `agent about` / `agent status` account identifiers.

## No marketplace add

Load local plugins with `agent --plugin-dir <path>` when needed. `agent plugin marketplace` (including `add`) is operator-opt-in. Never run marketplace add from sync.

## Overlay

- Instructions: `instructions/cursor-cli-global.md`
- Thin rule pointer: `.cursor/rules/cursor-cli.mdc`
- ACP: existing `cursor-acp` row (`agent acp`)
- Worker: `agent worker` is out of repo sync
