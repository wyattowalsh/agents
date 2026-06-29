# Safety and permissions

## Cross-harness defaults

| Setting | Default for delegation |
| --- | --- |
| `--always-approve` | **Never** auto-enable |
| `--permission-mode` | `default` or wave-specific (see below) |
| `--no-auto-update` | **Always** in automation |
| `--cwd` | Required absolute path |
| `--sandbox` | Optional; project policy |

## By wave

| Wave | `--permission-mode` | Notes |
| --- | --- | --- |
| Scout | `plan` | Read-biased |
| Build | `default` or `acceptEdits` | Parent approves destructive git |
| Verify | `dontAsk` + narrow tools | Read/test focused |
| Tune | Inherit originating wave | Delta prompts only |

## Destructive operations

Parent must approve before Grok nodes run: `git push`, `rm -rf`, production deploys, `skills sync --apply`.

## Auth

If `scripts/preflight.sh` reports any `fail` check (including `grok-binary` or `grok-auth-*`), stop all dispatch.

Remediation order:

1. `grok login` (or `grok login --device-auth` in headless contexts)
2. Re-run `bash skills/grok-delegate/scripts/preflight.sh`
3. Optional deep smoke: `bash skills/grok-delegate/scripts/auth_verify.sh --cwd <target>`
4. `XAI_API_KEY` only when the active user explicitly requests API-key billing and `GROK_DELEGATE_ALLOW_API_KEY=1` is set for that session