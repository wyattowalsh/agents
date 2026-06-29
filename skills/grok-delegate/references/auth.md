# Grok OAuth auth for delegation

Portable auth guidance for `/grok-delegate`. Fast checks run inside bundled `doctor.py`; deep smoke is optional.

## OAuth-primary policy

1. **Default:** SuperGrok OAuth via `grok login` (or `grok login --device-auth` in headless/agent contexts).
2. **Preflight:** `bash skills/grok-delegate/scripts/preflight.sh [--cwd <target>]`
3. **Deep smoke (optional):** `bash skills/grok-delegate/scripts/auth_verify.sh --cwd <target>`
4. **API key fallback:** `XAI_API_KEY` only when the active user explicitly requests API-key billing. Set `GROK_DELEGATE_ALLOW_API_KEY=1` for that session only.

## Auth store shape (evidence-based)

Grok Build stores OAuth under `~/.grok/auth.json`. Observed principals use a namespaced key:

```
https://auth.x.ai::<client_id>
```

Expected fields on the principal object:

| Field | Role |
| --- | --- |
| `refresh_token` | OAuth refresh credential (never log) |
| `expires_at` | Unix timestamp or ISO-8601 timestamp for access token expiry (required for fast preflight pass) |

Missing `access_token` with a present `refresh_token` usually means refresh is pending—run `grok login` interactively before fleet dispatch.

## Fast vs deep preflight

| Mode | Command | Blocks dispatch |
| --- | --- | --- |
| Fast (default) | `preflight.sh` / `doctor.py` | Any `fail` check |
| Deep (optional) | `auth_verify.sh` | `grok -p` smoke failure |

Deep verify uses a 20s timeout and may fail in non-interactive agent shells until OAuth refresh completes.

## Remediation ladder

1. `grok login` or `grok login --device-auth`
2. Re-run `preflight.sh`
3. If still failing on expiry, run `auth_verify.sh`
4. API key only after explicit user request + `GROK_DELEGATE_ALLOW_API_KEY=1`

## Security

- Never print `refresh_token`, `access_token`, or `XAI_API_KEY` values in logs or doctor output.
- Doctor summaries use presence/expiry only.
- `auth_verify.sh` failure JSON may include redacted stderr; treat as operator-only diagnostics, not for shared logs.
