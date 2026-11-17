# Tasks: elevate-cursor-agent-cli-harness

## W1 OpenSpec

- [x] Proposal / design / affected-surfaces / validation-matrix
- [x] Delta spec + main `openspec/specs/cursor-harness/spec.md` requirement
- [x] OpenSpec validate all (change included; 35/35 changes passed)

## W2 Implementation `[P]` file shards

- [x] `[P]` T-HM-01/02 classify_intent.py + SKILL.md
- [x] `[P]` T-HM-03 discover_surfaces.py
- [x] `[P]` T-HM-04 usage_probe.py
- [x] `[P]` T-HM-05/06 references + evals
- [x] `[P]` T-HM-07 authoring MDX
- [x] `[P]` T-REG-01 harness-surface-registry.json
- [x] `[P]` T-REG-02 hook-surface-registry.json
- [x] `[P]` T-REG-03 harness-fixture-support.json
- [x] `[P]` T-REG-04 sync-manifest.json
- [x] `[P]` T-REG-04b repo-sync-inventory.json + repo-drift-ledger.json companions
- [x] `[P]` T-REG-05 plugin-extension-registry.json
- [x] `[P]` T-REG-06 image-input + rtk
- [x] `[P]` T-INS-01..05 overlay, rule, AGENTS.md, README
- [x] `[P]` T-DOC-01..03 doctor, justfile, optional wrapper

## W3 Tests

- [x] T-TST-01 classify tests
- [x] T-TST-02 distribution metadata
- [x] T-TST-03 doctor unit tests
- [x] T-TST-04 discover smoke
- [x] T-TST-05 editor cursor regression
- [x] T-PERM-01 read-only permission gap note

## W4 Docs generate

- [x] `wagents readme` if needed
- [x] `wagents web generate --no-installed`

## W5 Review

- [x] Three-list / hooks / fixtures / generated-docs review


## Residual (RV-008)

- [x] Leftover Starlight generated pages under `docs/src/content/docs/harness-support.mdx` and `docs/src/content/docs/skills/catalog/custom/harness-master.mdx` stay unedited. CI SSOT is `uv run wagents web generate --no-installed --check` → `web/content/docs/`. Do not regenerate the abandoned Starlight tree in this change.
