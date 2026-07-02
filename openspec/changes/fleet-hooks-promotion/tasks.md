# Tasks

Canonical task graph for Hooks Bundle Promotion v2. Format: `ID — lane — [P] — done_when`.

## W0 — OpenSpec scaffold (gate: `uv run wagents openspec validate`)

- [ ] T-000a L0: `proposal.md`
- [ ] T-000b [P] L0: `design.md`
- [ ] T-000c [P] L0: `tasks.md`
- [ ] T-000d [P] L0: `validation-matrix.md`
- [ ] T-000e [P] L0: `affected-surfaces.md`
- [ ] T-000f [P] L0: `coordinator/wave-w0.json` … `wave-w7.json`
- [ ] T-001a L0: `uv run wagents openspec validate` green

## W1 — Baseline ship gate

- [ ] T-010a [P] S: commit `docs/public/generated-reports/hook-perf-baseline-legacy.json`
- [ ] T-010d [P] T: V-01..V-12 + V-RV subset
- [ ] T-011a L0: `coordinator/wave-w1.json`

## W2 — Mega-bundle registry

**R serial:** T-110b rename shell-file-guards → `fleet-pre-tool-enforce`; T-110c add group to `git-commit-push-guard`; T-110d narrow image matcher.

**T [P]:** T-120a–h mega-bundle render/deny/union tests.

**Gate:** T-121a `pytest tests/hooks/test_render_bundle_matchers.py tests/hooks/test_bundle_dispatch.py -q`

## W3 — Copilot dispatcher

**D:** T-130a `destructive_shell_guard.py`; T-130b `protected_file_guard.py`; T-130c POLICIES + normalize.

**R:** T-140a `{hook_runner}` commands; T-140b `fleet-pre-tool-enforce` for Copilot rows; reorder for contiguity.

**T [P]:** T-130d policy tests; T-140d–f copilot spawn + deny + snapshot.

## W4 — Tooling (parallel with W2/W3)

- [ ] T-150a [P] S: `hook_perf_inventory.py --tier legacy|g1|bundle`
- [ ] T-150b [P] S: `hook_assurance.py --json`
- [ ] T-150c [P] O: `docs/runbooks/hook-performance.md`
- [ ] T-150d–e [P] T: inventory + assurance tests

## W5 — Integration SERIAL

- [ ] T-200a POL: `"tier": "bundle"` in `config/tooling-policy.json`
- [ ] T-200b S: `sync --apply --targets repo`
- [ ] T-200d–f T: sync check, hooks validate, apm materialize
- [ ] T-200g S: `hook-perf-baseline-bundle.json`

## W6 — Harness assurance

- [ ] T-210a–g per-harness verify (7 harnesses)
- [ ] T-211a `hook_assurance.py --json` exit 0
- [ ] T-211b restart checklist in runbook

## W7 — Close

- [ ] T-220a CI: enhance `hook-perf` workflow_dispatch
- [ ] T-220b–c O: hooks hub MDX
- [ ] T-220d L0: archive `fleet-hooks-performance` + close promotion change
