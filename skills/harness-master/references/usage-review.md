# Usage Review

Usage Review is a read-only advisory mode for understanding how a harness is used and where token, cost, tool, MCP, plugin, skill, workflow, or telemetry posture can improve.

## Scope

Use Usage Review for:

- token and cost posture
- quota pressure
- context health and compression pressure
- tool friction and repeated failures
- MCP, skill, plugin, and subagent usage fit
- approval safety and risky workflow patterns
- observability gaps in harness usage

Do not use Usage Review for:

- generic application observability
- SLO design or production telemetry strategy
- direct config edits
- raw transcript analysis unless the user provides a sanitized excerpt
- secret, auth, provider, WakaTime, Langfuse, or `.env*` inspection

## Source Classes

| Class                 | Collect?  | Examples                                                                 |
| --------------------- | --------- | ------------------------------------------------------------------------ |
| `aggregate-safe`      | yes       | token totals, counts, status summaries, quota percentages                |
| `metadata-safe`       | yes       | top-level config keys, file presence, plugin names, command availability |
| `sanitized-export`    | yes       | `opencode export --sanitize`, explicit sanitized token exports           |
| `credential-presence` | yes       | `LANGFUSE_PUBLIC_KEY` present: true/false, never the value               |
| `raw-sensitive`       | no        | raw prompts, completions, traces, session bodies, message rows           |
| `secret-file`         | no        | `.env*`, key files, auth DBs, token JSON, WakaTime keys                  |
| `manual-only`         | list only | cloud dashboards, UI-only settings, connector consoles                   |

## Preferred Tools

Prefer these runtime summaries when available:

- `token_stats` for current-session token posture
- `token_history` for date-range token trends
- `token_export` only when using sanitized or aggregate export settings
- `insights_collect` and `insights_generate` for aggregate OpenCode usage reports
- `agent_attribution` for assistant-message attribution by agent/model
- `quota_status` for local quota and pricing diagnostics
- `gemini_quota` for Gemini quota posture
- `workspace-summary` and `git-smart-status` for repo context and worktree risk

OpenCode command shapes that are safe to plan or run only when sanitized:

- `opencode stats`
- `opencode session list`
- `opencode export --sanitize`
- `opencode db path`

Do not run raw database queries against message, part, trace, prompt, completion, or reasoning tables.

## Usage Schema

`UsageSource` fields:

- `id`
- `harness`
- `level`
- `privacy_class`
- `access_method`
- `status`
- `blocked_reason`

`UsageMetric` fields:

- `name`
- `category`
- `window_days`
- `value`
- `unit`
- `source_id`

`UsageSignal` fields:

- `category`
- `source_id`
- `privacy_class`
- `harness`
- `level`
- `window_days`
- `summary`
- `confidence`

`UsageFinding` fields:

- `severity`
- `category`
- `evidence_tag`
- `problem`
- `why_it_matters`
- `recommendation_lane`
- `blocked_evidence`

`UsageRecommendation` fields:

- `lane`
- `target_surface`
- `action`
- `requires_audit_before_apply`
- `validation_step`

## Signal Categories

- `token-cost`
- `tool-friction`
- `mcp-usage`
- `skill-usage`
- `plugin-usage`
- `subagent-usage`
- `context-health`
- `approval-safety`
- `observability-gap`
- `workflow-fit`

## Scorecard

Score each dimension `0-3`:

- `source-coverage`
- `privacy-safety`
- `cost-token-posture`
- `tool-efficiency`
- `mcp-hygiene`
- `skill-fit`
- `plugin-fit`
- `context-health`
- `approval-safety`
- `recommendation-actionability`

Verdict mapping:

- `well-instrumented`: strong source coverage, safe evidence, and actionable recommendations
- `usable-with-gaps`: enough aggregate evidence for recommendations, with named blind spots
- `under-instrumented`: insufficient telemetry; recommend instrumentation before tuning behavior
- `unsafe-to-review`: requested sources require raw-sensitive or secret-file access

## Recommendation Lanes

- `keep`: evidence supports leaving behavior unchanged
- `tune-config`: config change may help; requires matching dry-run Audit approval before apply
- `tune-skill`: skill routing, install inventory, or skill docs need refinement
- `tune-mcp`: MCP ownership, duplication, validation, or usage fit needs refinement
- `tune-plugin`: plugin placement, overlap, or configuration needs refinement
- `tune-workflow`: user or team workflow should change without config edits
- `instrument`: add safer aggregate measurement before changing behavior
- `defer`: evidence is incomplete or blocked
- `do-not-change`: risk outweighs benefit

## OpenCode Baseline Sources

Useful local sources for OpenCode Usage Review:

- `opencode.json`: repo-managed runtime plugin and telemetry configuration; read top-level keys and plugin names only
- `.opencode/PLUGINS.md`: documented plugin behavior and known disabled plugins
- `config/opencode-token-monitor.json`: budget threshold metadata; do not print secret values if added later
- `config/opencode-quota-toast.json`: quota and session token settings metadata
- `config/plugin-extension-registry.json`: plugin ownership and support context
- `config/harness-surface-registry.json`: known telemetry surfaces and blind spots
- `instructions/opencode-global.md`: policy constraints for credential, telemetry, and session poisoning handling

## Apply Boundary

Usage Review never applies changes directly. If a recommendation needs a config, MCP, plugin, or skill-definition change, route it to a matching dry-run Audit or the correct specialized skill and require explicit approval before editing.
