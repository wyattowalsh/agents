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

If `scripts/preflight.sh` reports `grok-binary` fail, stop all dispatch. Use `grok login` or `XAI_API_KEY` per x.ai docs.