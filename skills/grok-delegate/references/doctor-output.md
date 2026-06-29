# Bundled doctor JSON output

Portable preflight for `/grok-delegate`. Ships with the skill; no repo `wagents` dependency.

## Commands

```bash
bash skills/grok-delegate/scripts/preflight.sh
bash skills/grok-delegate/scripts/preflight.sh --cwd /absolute/target/repo
python3 skills/grok-delegate/scripts/doctor.py --format json --cwd /absolute/target/repo
bash skills/grok-delegate/scripts/auth_verify.sh --cwd /absolute/target/repo
```

Stdout is JSON only (except `auth_verify.sh` errors on stderr). Exit `0` when top-level `ok` is true; exit `1` when any check is `fail`.

## Top-level shape

```json
{
  "ok": true,
  "summary": { "total": 12, "ok": 8, "warn": 4, "fail": 0 },
  "checks": [
    { "name": "grok-binary", "status": "ok", "summary": "Found at /path/to/grok" }
  ]
}
```

## Check matrix

| name | Blocks dispatch | Meaning |
| --- | --- | --- |
| `grok-binary` | yes (`fail`) | `grok` on PATH or `~/.grok/bin/grok` |
| `grok-home-config` | yes (`fail`) | `~/.grok/config.toml` exists |
| `grok-target-config` | no (`warn`) | `{--cwd}/.grok/config.toml` for target project |
| `grok-auth-file` | yes (`fail`) | `~/.grok/auth.json` exists |
| `grok-auth-oauth` | yes (`fail`) | OAuth principal with `refresh_token` |
| `grok-auth-expiry` | yes (`fail`) | `expires_at` required; expired, missing, or malformed values block dispatch |
| `grok-auth-mode` | advisory | `oauth` or `api_key_fallback` |
| `grok-auth-policy` | yes (`fail`) | OAuth-primary policy satisfied |
| `grok-cli-smoke` | no (`warn`) | `grok version` succeeds |
| `grok-env-grok_*` | no (`warn`) | Experimental feature env vars |

## Classification gate

- **`fail`** — stop fleet dispatch; fix before parallel Grok nodes.
- **`warn`** — advisory; parent may proceed unless policy requires zero warnings.
- **`ok`** — check passed.

## Out of scope (repo maintainer only)

MCP managed blocks, Plannotator hooks, mcphub endpoints, LSP binary matrix, and policy-template sync are **not** part of the bundled doctor. Run `uv run wagents grok doctor --format json` from the agents clone when maintaining extended Grok harness surfaces.