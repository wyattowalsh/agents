# Tasks

## OpenSpec

- [x] T000 Create `openspec/changes/integrate-apm-package-manager/` with proposal, design, tasks, affected-surfaces, validation-matrix.

### Wave 0 — Research & Baseline

- [x] T001 Research microsoft/apm manifest, CLI verbs, harness matrix, .apm/ layout, MCP handling, policy, AGENTS.md import pattern (cite github + docs).
- [x] T002 Confirm disambiguation (APM != observability); document in change notes.
- [x] T003 Snapshot current `agent-bundle.json`, `wagents self doctor` output, catalog generation, sync-manifest, instructions/global.md.
- [x] T004 Verify `apm` global install methods and `apm --version` / `which apm` behavior (non-fatal if absent).
- [ ] T005 Identify exact catalog authoring path (docs/src/authoring/skills/ for tool row).

### Wave 1 — Docs, Doctor, Catalog Entry

- [x] T010 Add APM awareness and non-blocking row to `wagents self doctor` (presence, version, policy note, install hint).
- [x] T011 Author `docs/src/authoring/skills/apm-cli.mdx` (or id) with scope ("remote packages only"), install, policy, trust notes, examples (audit-style per §2.7).
- [x] T012 Run `uv run wagents docs generate` and confirm APM row appears in catalog index + generated pages.
- [x] T013 Update README doctor example and any distribution text if affected (via generator only).
- [x] T014 Add minimal tests for doctor APM check (optional presence).

### Wave 2 — Bundle Metadata + Policy Wording

- [x] T020 Extend `agent-bundle.json` `adapters` / `updateCommands` / notes with APM CLI references (complementary).
- [ ] T021 Add policy paragraph to `instructions/global.md` (and generated mirrors) explaining SSOT split, remote-only use, no duplication.
- [ ] T022 Update harness-specific globals (opencode, codex, claude, copilot, gemini, cursor) with import notes or cross-ref where relevant.
- [ ] T023 Update `config/harness-surface-registry.json` support notes for APM-overlapping harnesses (informational).
- [ ] T024 Ensure `config/sync-manifest.json` lists any new canonical or generated APM-related files.

### Wave 3 — Facade Skeleton (wagents apm)

- [x] T030 Scaffold `wagents apm` subcommand group (install, sync, doctor, list, etc.) as thin delegates.
- [x] T031 Wire delegation to `apm` binary when present; else helpful error + install hint.
- [ ] T032 Enforce repo policy inside facade (block self-bundle via apm, warn on MCP overlap, allowed-source hints).
- [x] T033 Add `--dry-run` friendly behavior and structured output parity with other wagents commands.
- [x] T034 Unit tests for facade policy guards (no network execution in unit scope).

### Wave 4 — OpenCode MCP Separation + Merge Notes

- [x] T040 Document and (if needed) add tests that APM MCP declarations do not collide with MCPHub projections in OpenCode.
- [x] T041 Add OpenCode-specific notes in `.opencode/PLUGINS.md` or opencode-global about APM as separate MCP source.
- [x] T042 Verify `scripts/sync_agent_stack.py` (or render paths) tolerates or ignores APM-deployed MCPs for OpenCode without overwriting.
- [x] T043 Add evidence to affected surfaces and validation for MCP split.

### Wave 5 — Validation, Polish, Cross-Harness

- [x] T050 Run full validation matrix (`wagents validate`, doctor, openspec validate, docs generate, catalog checks).
- [x] T051 Add or extend distribution / site-model tests for APM catalog row and doctor output.
- [ ] T052 Update any AGENTS.md references or KB if public surfaces change.
- [x] T053 `uv run pytest` focused + full where changed; ruff/ty.
- [ ] T054 Confirm Grok/Crush paths remain unaffected (use repo sync).

### Wave 6 — Harness Instruction Overlays + Final Audit

- [x] T060 Add progressive `AGENTS.md` import guidance example (e.g., consumer `apm/AGENTS.md` pattern) in instructions.
- [x] T061 Audit all touched instruction files for duplication or policy drift.
- [x] T062 Run `wagents skills sync --dry-run` (no APM content expected in output for repo bundle).
- [x] T063 Final docs build + `wagents openspec validate`.
- [x] T064 Produce evidence pack (doctor output, catalog row screenshot/json, command traces) and close change.
