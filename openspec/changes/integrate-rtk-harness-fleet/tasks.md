# Tasks

## OpenSpec

- [x] T000 Create `openspec/changes/integrate-rtk-harness-fleet/` with proposal, design, tasks, affected-surfaces, validation-matrix, and downstream-tooling spec delta.

## Wave 0 - Research And Baseline

- [x] T001 Capture current `rtk --version`, `rtk init --help`, `rtk init --show`, target dry-runs, and `rtk gain` behavior.
- [x] T002 Confirm existing repo RTK references and prior stale `@RTK.md` cleanup evidence.
- [x] T003 Identify the active research write blocker in `~/.claude/settings.json` and repo hook code.
- [x] T004 Review `wagents grok doctor`, `wagents self doctor`, and OpenSpec command patterns.
- [x] T005 Snapshot current branch and dirty state before edits.

## Wave 1 - Hook Handoff Fix

- [x] T010 Add explicit implementation-handoff state clearing to `hooks/wagents-hook.py`.
- [x] T011 Add regression coverage showing `/research` activates state, then "continue and fix" clears it and write guard allows edits.
- [x] T012 Verify direct `skills/research/scripts/research_hook.py` remains strict for direct env-forced research sessions.

## Wave 2 - RTK Policy And CLI

- [x] T020 Add `config/rtk-integration.json`.
- [x] T021 Implement `wagents/rtk.py` for policy loading, doctor checks, sync plans, apply execution, and gain wrapper.
- [x] T022 Register `wagents rtk doctor`, `wagents rtk sync`, and `wagents rtk gain`.
- [x] T023 Add non-fatal RTK row to `wagents self doctor`.
- [x] T024 Keep live `--apply` behavior explicit and never invoked by default.

## Wave 3 - Tests

- [x] T030 Add tests for RTK policy loading and doctor JSON shape.
- [x] T031 Add tests for dry-run sync command rendering and unsupported platform handling.
- [x] T032 Add tests for `wagents rtk doctor --format json` and `wagents rtk sync --dry-run --format json`.
- [x] T033 Extend self doctor tests for RTK row presence.
- [x] T034 Add hook regressions proving research-continuation prompts do not clear read-only state.
- [x] T035 Add hook regression proving env-forced research mode cannot be cleared by prompt triage.
- [x] T036 Add RTK live-apply regressions for noninteractive subprocess options, timeout handling, missing binary handling, and non-zero exit preservation.

## Wave 4 - Future Fleet Rollout Tasks

- [x] T040 Add optional `--with-rtk` / `RTK_ENABLED=1` integration to `scripts/sync_agent_stack.py`.
- [ ] T041 Implement Grok custom RTK hook only after live Grok hook schema proof. **Blocker:** Grok RTK shim deferred — no live bash-rewrite hook schema proof for Grok Build (only plannotator/wagents-fleet hooks verified in hook-surface-registry).
- [x] T042 Add docs or catalog entry if maintainers want RTK surfaced publicly.
- [x] T043 Add no-stale-include validation for `@RTK.md` in shared instruction surfaces.
- [x] T044 Add usage-review lane for `rtk gain --history` and missed savings.

## Wave 5 - Validation

- [x] T050 Run focused hook tests.
- [x] T051 Run focused RTK CLI tests.
- [x] T052 Run `uv run wagents rtk doctor --format json`.
- [x] T053 Run `uv run wagents rtk sync --dry-run --format json`.
- [x] T054 Run `uv run wagents openspec validate`.
- [x] T055 Run `uv run wagents validate`.
- [x] T056 Inspect final diff and confirm no unrelated dirty state was reverted.

## Wave 6 - Review Findings

- [x] T060 Fix RV-001 by narrowing implementation-handoff detection to explicit implementation/fix/apply prompts.
- [x] T061 Fix RV-001 by preserving stored research state for research-continuation, note-writing, and research-edit prompts.
- [x] T062 Fix RV-001 by preserving env-forced research sessions until the user/tool explicitly exits that mode.
- [x] T063 Fix RV-002 by running RTK live apply with closed stdin and a fixed timeout.
- [x] T064 Fix RV-002 by returning structured results for timeout and missing-binary failures.
- [x] T065 Re-run focused and repo validations after the review fixes.
- [x] T066 Fix RV-003 by enforcing init-only RTK commands in sync plan building and live apply.
- [x] T067 Add regressions proving non-init RTK sync commands are skipped or rejected before subprocess execution.
