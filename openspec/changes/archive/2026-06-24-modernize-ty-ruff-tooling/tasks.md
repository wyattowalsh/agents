## Tasks

### Wave 0
- [x] T001 Snapshot baseline (`baseline.json`)
- [x] T003 OpenSpec scaffold
- [x] T004 Confirm ty 0.0.52 latest on PyPI

### Wave 1
- [x] T010 Expand pyproject Ruff/ty SSOT
- [x] T011 Bump ty/ruff pins; sync pre-commit rev
- [x] T012 Unify Makefile, CI, release-skills
- [x] T013 Update agent instructions + tooling-contract
- [x] T014 Add doctor ruff/ty checks
- [x] T015 Add tooling parity test
- [x] T016 Align nerdbot pyproject extend
- [x] T017 Align pre-commit ty hook

### Wave 2
- [x] T020 PKG-1 wagents ruff fixes
- [x] T021 PKG-2 tests ruff fixes
- [x] T022 PKG-3 scripts ruff fixes
- [x] T023 PKG-4 skill-creator ruff fixes
- [x] T024 PKG-5 nerdbot ruff fixes
- [x] T025 PKG-6 hooks alignment

### Wave 3
- [x] T030 Enable preview=true
- [x] T031 Document preview ignores if needed
- [x] T032-T037 PKG re-fix preview delta

### Wave 4
- [x] T040-T044 ty fixes + type:ignore migration

### Wave 5
- [x] T050 Quality matrix green (`ruff check`, `ruff format --check`, `ty check`, tooling parity tests)
- [x] T051 OpenSpec deltas + `wagents openspec validate`
- [x] T052 Validation-matrix evidence
- [x] T053 Full pytest green (916 passed)

### Wave 6
- [x] T060 Expand `[tool.ruff].include` to `skills/**/scripts/**/*.py`
- [x] T061 Auto-fix + format portable skill scripts; per-file ignores for script ergonomics (E402/E501/E701/E702/E741/RUF001)
- [x] T062 Fix substantive lint issues (F821, SIM102) in skill scripts
- [x] T063 Drop runtime fold filter; stale authoring rows removed (docs-only)
- [x] T064 Ty scope unchanged for portable scripts (Ruff-only gate per OpenSpec delta)