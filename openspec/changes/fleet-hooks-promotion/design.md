# Design

## Lane model

| Lane | Paths | Rule |
|------|-------|------|
| R | `config/hook-registry.json` | Serial — one editor |
| D | `hooks/wagents-hook.py`, `wagents/hooks/policies/` | Parallel with R after schema stable |
| P | `wagents/hooks/render.py` | After R bundle_group stable |
| T | `tests/hooks/**` | Parallel |
| S | `scripts/hooks/` | Parallel |
| POL | `config/tooling-policy.json` | W5 only |
| L0/O/CI | OpenSpec, runbooks, workflows | W0, W7 |

## Mega-bundle contract (`fleet-pre-tool-enforce`)

Per-harness PreToolUse enforce-chain bundle members (union matchers via
`union_bundle_matchers()`):

| Harness | Members |
|---------|---------|
| cursor | `cursor-destructive-shell-guard`, `cursor-protected-file-guard`, `git-commit-push-guard` |
| codex | `codex-destructive-shell-guard`, `codex-protected-file-guard`, `git-commit-push-guard` |
| github-copilot | `destructive-shell-guard`, `protected-file-guard`, `git-commit-push-guard` |
| claude-code / gemini-cli | `git-commit-push-guard` only (single member — no collapse) |

Registry rows for Copilot shell/file guards move adjacent to `git-commit-push-guard`
so PostToolUse post-edit rows do not break PreToolUse bundle contiguity.

Rendered bundle command shape (bundle/worker tiers):

```text
{hook_runner} --bundle <policy-ids> --harness {harness} --bundle-mode enforce-chain --bundle-timeout <sum>
```

## Copilot dispatcher migration

Shell scripts `hooks/guard-destructive.sh` and `hooks/protect-files.sh` logic
migrates into stdlib-only policy modules:

- `wagents/hooks/policies/destructive_shell_guard.py` → `evaluate_destructive_shell(command)`
- `wagents/hooks/policies/protected_file_guard.py` → `evaluate_protected_file(path)`

Registry commands become `{hook_runner} destructive-shell-guard --harness {harness}` (and
protected-file analogue). `_shell_bundle_command()` no longer returns `./hooks/*.sh` for
PreToolUse Copilot guards — all members are dispatcher-backed so `--bundle` emits.

## Spawn budget (planning targets, authoritative via inventory)

| Harness | PreToolUse Bash (legacy) | after W5 bundle |
|---------|--------------------------|-----------------|
| cursor | 6 | ≤3 |
| codex | 6 | ≤3 |
| github-copilot | 3 | ≤2 |

Authoritative counts: `uv run python scripts/hooks/hook_perf_inventory.py --tier bundle --json`.

## Rollback ladder

1. `hook_perf.tier: bundle` → `g1` (matcher/caches only, no collapse)
2. `g1` → `legacy` (byte-identical pre-performance renders)
3. Re-run `sync_agent_stack.py --apply --targets repo` after each step

## Invariants

- Enforce deny: JSON on stdout, exit 0 (per harness transport).
- `union_bundle_matchers()` on every bundle collapse.
- OpenCode/Grok fail-open not widened on dispatcher crash.
- `legacy` tier render tests byte-stable.
