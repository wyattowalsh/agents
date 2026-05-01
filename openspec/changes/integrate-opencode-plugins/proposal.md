# Proposal

## Problem

OpenCode has a growing plugin inventory split across the repo-managed project mirror and the live user config. The requested additions include runtime plugins, TUI-only plugins, scheduler behavior, Claude credential reuse, Langfuse telemetry, and plan-review tooling. Without a tracked change, future sync or validation work can lose the distinction between runtime and TUI surfaces, accidentally commit secrets, overexpose plan-review tools to execution agents, or introduce unsupported plugin specs.

## Intent

Integrate the requested OpenCode plugins with the smallest safe config changes, document the runtime/TUI boundary, and add tests that protect the repo-managed plugin inventory from regressions.

## Scope

- Add requested runtime plugin specs to `opencode.json` and `~/.config/opencode/opencode.json`.
- Add requested TUI plugin specs to `~/.config/opencode/tui.json` only.
- Replace `open-plan-annotator@latest` with `@plannotator/opencode@latest` scoped to the `plan` agent.
- Enable OpenTelemetry support needed by the Langfuse plugin without storing Langfuse credentials.
- Update OpenCode docs and global instructions with guardrails for scheduler jobs, Claude auth, Langfuse secrets, plan-review scope, and UI/workflow plugin deferrals.
- Extend distribution metadata tests for the new plugin inventory rules.

## Out Of Scope

- Creating `opencode-scheduler` jobs.
- Enabling optional Claude Auth 1M context beta behavior.
- Re-adding `open-plan-annotator@latest` unless the user explicitly requests the older broader workflow.
- Adding CodeMCP workflow plugins or running setup that writes additional workflow artifacts without explicit approval.
- Installing remote dashboard, browser-control, tunnel, checkpoint, or orchestration-bundle plugins.
- Committing generated downstream OpenSpec tool artifacts.

## Affected Users And Tools

- OpenCode users on this machine using the live global config.
- Repo maintainers reviewing `opencode.json` as the OpenCode runtime plugin mirror.
- Future sync and validation workflows that enforce plugin inventory conventions.
- Docs readers using the OpenCode integration plan and install manifest.

## Generated Surfaces To Refresh

No generated README or docs catalog refresh is expected because this change updates tracked docs and config surfaces, not generated skill or agent catalogs.

## Risks

- Langfuse and the existing OTEL plugin may both emit telemetry hooks; startup validation must check for plugin load failures or duplicate-export warnings.
- TUI plugin syntax may differ from runtime plugin syntax; live TUI config must be JSON-validated and startup-tested.
- Plannotator's package is substantially larger and has postinstall command-copy side effects; config and docs must constrain the active behavior to `workflow: "plan-agent"`.
- Scheduler and dashboard-style plugins can alter host behavior; this change installs scheduler only and documents that jobs require explicit approval.
- Live user config contains secrets outside the touched sections; edits must avoid exposing or rewriting those values.
