# Bundled doctor JSON output

Portable preflight for `/grok-delegate`. Ships with the skill; no repo `wagents` dependency.

## Commands

```bash
bash skills/grok-delegate/scripts/preflight.sh
bash skills/grok-delegate/scripts/preflight.sh --cwd /absolute/target/repo
python3 skills/grok-delegate/scripts/doctor.py --format json --cwd /absolute/target/repo
```

Stdout is JSON only. Exit `0` when top-level `ok` is true; exit `1` when any check is `fail`.

## Top-level shape

```json
{
  "ok": true,
  "summary": { "total": 8, "ok": 5, "warn": 3, "fail": 0 },
  "checks": [
    { "name": "grok-binary", "status": "ok", "summary": "Found at /path/to/grok" }
  ]
}
```

Compatible with parent bash pipelines that parse machine-readable doctor JSON.

## Check matrix

| name | Blocks dispatch | Meaning |
| --- | --- | --- |
| `grok-binary` | yes (`fail`) | `grok` on PATH or `~/.grok/bin/grok` |
| `grok-home-config` | yes (`fail`) | `~/.grok/config.toml` exists |
| `grok-target-config` | no (`warn`) | `{--cwd}/.grok/config.toml` for target project |
| `grok-cli-smoke` | no (`warn`) | `grok version` succeeds |
| `grok-env-grok_*` | no (`warn`) | `GROK_WEB_FETCH`, `GROK_MEMORY`, `GROK_SUBAGENTS`, `GROK_LSP_TOOLS` |

Set env vars in your shell profile or project env file. In the agents clone, `config/grok-env.sh` is a convenience source script — not required when the skill is installed elsewhere.

## Classification gate

- **`fail`** — stop fleet dispatch; fix before parallel Grok nodes.
- **`warn`** — advisory; parent may proceed unless policy requires zero warnings.
- **`ok`** — check passed.

## Delegation vs harness diagnostics

| Surface | When | Command |
| --- | --- | --- |
| **Delegation preflight** | Parent harness dispatches Grok task nodes | `/grok-delegate preflight` or `scripts/preflight.sh` |
| **Harness maintainer doctor** | Grok home config, LSP, MCP, compat hooks | `uv run wagents grok doctor --format json` (agents clone only) |

## Out of scope (harness maintainer only)

MCP managed blocks, Plannotator hooks, mcphub endpoints, LSP binary matrix, and policy-template sync are not part of the bundled doctor.