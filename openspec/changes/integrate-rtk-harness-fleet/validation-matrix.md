# Validation Matrix

## Focused Local Validation

| Check | Command | Expected |
| --- | --- | --- |
| Hook handoff | `uv run pytest tests/test_wagents_hook.py -q -k "prompt_triage or readonly_guard"` | Pass |
| RTK CLI tests | `uv run pytest tests/test_rtk_cli.py tests/test_wagents_self.py -q -k "rtk or self_doctor"` | Pass |
| Hook research-continuation regressions | `uv run pytest tests/test_wagents_hook.py -q -k "prompt_triage_does_not_clear"` | Pass |
| RTK apply subprocess regressions | `uv run pytest tests/test_rtk_cli.py -q -k "apply"` | Pass |
| RTK init-only sync regressions | `uv run pytest tests/test_rtk_cli.py -q -k "non_init or invalid_argv or malformed_non_init"` | Pass |
| Hook and RTK compile check | `uv run python -m py_compile hooks/wagents-hook.py wagents/rtk.py` | Pass |
| RTK doctor | `uv run wagents rtk doctor --format json` | JSON with `ok`, `summary`, and checks |
| RTK sync dry-run | `uv run wagents rtk sync --dry-run --format json` | JSON command plan; no writes |
| OpenSpec | `uv run wagents openspec validate` | Pass or report unrelated pre-existing drift |
| Repo validation | `uv run wagents validate` | Pass or report unrelated pre-existing drift |
| Whitespace diff check | `git diff --check -- hooks/wagents-hook.py wagents/rtk.py tests/test_wagents_hook.py tests/test_rtk_cli.py openspec/changes/integrate-rtk-harness-fleet` | Pass |

## Safety Probes

| Probe | Command | Expected |
| --- | --- | --- |
| No shared RTK include | `rg '@RTK\.md' instructions AGENTS.md .github/copilot-instructions.md` | No new shared-corpus matches |
| OpenCode plugin ownership | `rg 'rtk' opencode.json` | Only allowed bash command permissions, no plugin entry |
| Dry-run default | `uv run wagents rtk sync --format json` | `dry_run: true` |
| Non-init sync rejection | Directly call `run_rtk_sync_plan()` with `argv=["rtk", "gain"]` | Structured `returncode: 2`; subprocess not called |
| Unsupported apply | `uv run wagents rtk sync --platforms cherry-studio --dry-run --format json` | Skip or no-op, not failure |
| Research-continuation negative probe | Activate `/research`, submit `continue researching and write notes`, then run read-only write guard against `README.md` in a temp home | Deny source write; no inactive-context output |
| Forced research negative probe | Set `RESEARCH_SKILL_ACTIVE=1`, submit `continue and fix the hooks`, then run read-only write guard against `README.md` | Deny source write; no inactive-context output |

## Live Rollout Validation - Deferred

These checks require explicit maintainer approval before local global hook writes:

- `RTK_TELEMETRY_DISABLED=1 uv run wagents rtk sync --apply --platforms claude-code,cursor,opencode`
- `rtk init --show`
- `rtk gain --history`
- Harness-specific shell smoke in Claude, Cursor, OpenCode, Gemini, and Copilot.
