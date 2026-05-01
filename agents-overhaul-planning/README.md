# Agents Overhaul Planning Docs — Maximal Progressive-Disclosure Bundle

Generated: `2026-05-01T07:19:13Z`

This bundle refactors the existing planning corpus into an execution-grade, repository-ready documentation tree for evolving `wyattowalsh/agents` into a skills-first, OpenSpec-governed, multi-harness agent control plane.

## Primary design posture

1. **Agent Skills first.** Prefer Agent Skills packages for static/semi-static knowledge, reusable workflows, deterministic scripts, docs, rules, planning playbooks, and CLI-first automation.
2. **MCP second.** Use MCP for live external state, authenticated SaaS, browser/runtime interaction, current docs/search, database/cloud state, and telemetry streams.
3. **Plugins/adapters as projection layers.** Native harness plugins are used to package and distribute canonical capabilities, not to fork behavior per tool.
4. **OpenSpec governs changes.** Major behavior changes should land through proposal/design/tasks/spec-delta flow.
5. **Docs are product.** README, AGENTS.md, generated docs, support matrices, AI instructions, and audit docs are first-class implementation artifacts.

## Progressive read paths

### 30-minute executive read

1. `planning/00-overview/00-executive-outline.md`
2. `planning/00-overview/01-proposed-changes.md`
3. `planning/00-overview/07-progressive-disclosure-map.md`
4. `planning/10-architecture/10.10-extension-decision-tree.md`
5. `planning/99-task-graph/critical-path.md`

### 2-hour architect read

1. Everything in the 30-minute path
2. `planning/10-architecture/10.13-canonical-manifest-contracts.md`
3. `planning/10-architecture/10.15-idempotent-cli-interface.md`
4. `planning/20-harness-registry/01-harness-compatibility-matrix.md`
5. `planning/30-adapters/harness-projection-contract.md`
6. `planning/40-skills-ecosystem/10-skill-audit-model.md`
7. `planning/50-config-safety/10-transaction-engine-spec.md`
8. `planning/90-ui-ux/10-productized-cli-flows.md`

### Full execution read

Read all `planning/**`, then `openspec/**`, then the generated manifests under `planning/manifests/**`.

## New/refactored areas in this bundle

- Expanded progressive-disclosure documentation index.
- Added repo-sync and drift ledger reflecting the latest public repo structure.
- Added deeper harness-specific extension surface docs.
- Added Agent Skills-first registry, audit, lifecycle, and CLI conformance docs.
- Added MCP index and registry gap-filling docs, with explicit replacement-by-skill classification.
- Added plugin ecosystem docs for Claude, Copilot, Gemini, OpenCode, Cursor, ChatGPT Apps/Actions, and harness-native packaging.
- Added UI/UX product blueprints for `wagents doctor`, `catalog`, `sync`, `rollback`, `audit`, `skill`, `mcp`, and `openspec` flows.
- Added more granular task graph nodes for docs, AI instructions, README, manifests, CI gates, skill audit, MCP audit, and OpenSpec reconciliation.

## Authoritative source policy

All external ecosystem claims must be traced to `planning/appendix/source-index.md` or `planning/manifests/source-ledger.json`. Community indexes are discovery inputs only; they are never trust roots.



## Finalization Addendum

This final bundle includes:

- `planning/00-overview/11-finalization-audit.md`
- `planning/15-ecosystem-research/20-user-provided-repo-evaluation.md`
- `planning/manifests/external-repo-evaluation-final.json`
- `planning/99-task-graph/subagent-graph-final.json`
- `planning/99-task-graph/codex-master-orchestration-prompt.md`
- `planning/99-task-graph/dispatch/*.md`
- `openspec/changes/agents-platform-overhaul/final-codex-dispatch-plan.md`

The final execution model is OpenSpec-governed, skills-first, MCP-second, and optimized for parallel Codex subagents.
