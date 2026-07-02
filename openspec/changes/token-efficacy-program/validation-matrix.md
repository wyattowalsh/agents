# Validation Matrix

## Wave 0 — OpenSpec Scaffold

| ID | Command | From wave | Expected |
| --- | --- | --- | --- |
| V-W0-01 | `uv run wagents openspec validate` | W0+ | Change package and spec deltas validate |

## Wave 1 — Research (read-only)

| ID | Command | From wave | Expected |
| --- | --- | --- | --- |
| V-W1-01 | Manual review of R1–R5 artifacts | W1 | Decision matrix, MCP crux doc, trim list, landscape journal, DCP summary present |
| V-W1-02 | Gate table documents approve/deny per category | W1 | No install recommendations without explicit gate pass |

## Wave 2 — RTK Live Apply

| ID | Command | From wave | Expected |
| --- | --- | --- | --- |
| V-W2-01 | `uv run wagents rtk doctor --format json` | W2+ | JSON with `ok`, `summary`, and checks; block apply on fail |
| V-W2-02 | `RTK_TELEMETRY_DISABLED=1 uv run wagents rtk sync --apply --platforms claude-code,cursor,opencode,codex,gemini-cli,github-copilot` | W2 | Explicit maintainer approval only; local harness hooks applied |
| V-W2-03 | `uv run wagents rtk gain --graph` | W2+ | Savings graph or structured report after apply |
| V-W2-04 | `uv run pytest tests/test_rtk_cli.py -q -k "apply or non_init"` | W2+ | RTK apply and init-only regressions pass |
| V-W2-05 | `rg '@RTK\.md' instructions AGENTS.md .github/copilot-instructions.md` | W2+ | No new shared-corpus matches (T043) |

## Wave 3 — Docs Steward

| ID | Command | From wave | Expected |
| --- | --- | --- | --- |
| V-W3-01 | `uv run wagents readme --check` | W3+ | README reflects token posture updates |
| V-W3-02 | `uv run wagents docs generate --no-installed` | W3+ | Harness-config hub MDX generated |
| V-W3-03 | `uv run wagents docs build` | W3+ | Static docs build passes link validation |
| V-W3-04 | `uv run python scripts/sync_agent_stack.py --check --targets repo` | W3+ | Instruction projections in sync |

## Wave 4 — DCP Tuning (conditional)

| ID | Command | From wave | Expected |
| --- | --- | --- | --- |
| V-W4-01 | Review `~/.config/opencode/logs/dcp/` and DCP stats | W4 | Evidence supports or rejects tune |
| V-W4-02 | `rg 'modelMaxLimits|modelMinLimits' config/opencode-dcp.jsonc` | W4 | No per-model limit maps unless explicitly requested |
| V-W4-03 | Post-tune DCP stats spot-check | W4 | No regression in compaction behavior |

## Wave 5 — Final Validation

| ID | Command | From wave | Expected |
| --- | --- | --- | --- |
| V-W5-01 | `uv run wagents rtk doctor --format json` | W5 | Pass |
| V-W5-02 | `uv run wagents rtk gain --graph` | W5 | Baseline or history report captured |
| V-W5-03 | DCP stats / log spot-check | W5 | Pass or N/A if Wave 4 skipped |
| V-W5-04 | `uv run wagents validate` | W5 | Repo asset validation passes |
| V-W5-05 | `uv run pytest tests/test_rtk_cli.py -q` | W5 | RTK CLI tests pass |
| V-W5-06 | `uv run wagents docs build` && `uv run wagents readme --check` | W5 | Docs and README current |
| V-W5-07 | `uv run wagents openspec validate` | W5 | All OpenSpec changes and specs pass |

## Safety Probes

| Probe | Command | Expected |
| --- | --- | --- |
| No shared RTK include | `rg '@RTK\.md' instructions AGENTS.md .github/copilot-instructions.md` | No matches in shared corpus |
| OpenCode plugin ownership | `rg 'rtk' opencode.json` | Only allowed bash permissions; no RTK plugin entry |
| No ungated OSS | Manual review of Wave 1–2 artifacts | No Sleev/Headroom/Cozempic/mcp-compressor/jCodeMunch install without gate approval |
| DCP model-neutral | `rg 'modelMaxLimits|modelMinLimits' config/opencode-dcp.jsonc` | Absent unless user explicitly requested |

## Deferred — Requires Explicit Maintainer Approval

These checks are **not** part of Wave 0 and require explicit approval before execution:

- `RTK_TELEMETRY_DISABLED=1 uv run wagents rtk sync --apply ...`
- `rtk init --show` on each harness
- `rtk gain --history`
- Installing any surveyed third-party token tool
- `uv run python scripts/sync_agent_stack.py --apply --targets home`
