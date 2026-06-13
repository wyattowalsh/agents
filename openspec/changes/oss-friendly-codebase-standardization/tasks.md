# Tasks

## OpenSpec And Coordination

- [x] Create OpenSpec artifacts for this whole-repo OSS-friendliness change.
- [x] Keep a current dirty-tree snapshot and avoid reverting unrelated changes.

## Onboarding And Safety

- [x] Add public contributor guidance covering install paths, source-of-truth files, generated artifacts, validation commands, external skill audits, and cleanup policy.
- [x] Add lightweight public safety guidance for secret handling and external skill trust boundaries.
- [x] Link the contributor and safety guidance from the docs onboarding path.
- [x] Update generated README content only through its generator if README contributor links are needed.

## Skill Metadata And Generated Indexes

- [x] Add display-safe source fields and local inventory flags to generated skill rows.
- [x] Standardize comparable repo-owned, curated external, and installed external skill fields.
- [x] Preserve existing custom and curated external install command behavior.
- [x] Merge curated and installed external rows without exposing local absolute paths as public source labels.
- [x] Extend external skill parser output only for deterministically derivable trust, status, risk, provenance, and target-agent fields.

## Generated Docs And Catalog UI

- [x] Update external skill source grouping to use display-safe labels.
- [x] Update installed skill provenance wording so public pages do not foreground absolute local paths.
- [x] Update repo-owned generated skill pages to expose standardized public fields where available.
- [x] Add catalog filters for provenance or review state, supported agents, installability, and local-only inventory.
- [x] Keep the catalog responsive, accessible, and scannable.

## Cleanup And Production Prep

- [x] Classify stale, generated, local-only, and source-of-truth artifacts before editing cleanup surfaces.
- [x] Apply only clearly safe cleanup or ignore-rule changes that are in scope.
- [x] Document uncertain cleanup candidates instead of deleting them.
- [x] Verify production docs build, generated indexes, package dry-runs, distribution metadata, and no local path or secret exposure.

## Tests

- [x] Add site-model tests for display-safe source fields and local inventory flags.
- [x] Add tests that generated public docs and public JSON display fields do not contain home-directory absolute paths.
- [x] Add curated-installed merge tests for installed agent preservation and local path redaction.
- [x] Add parser tests for external skill status, trust tier, target agents, and risk/provenance notes where deterministic.
- [x] Add catalog output assertions for new filter controls where feasible.
- [x] Preserve distribution metadata tests for supported agent and harness coverage.

## Verification

- [x] Run focused Python tests for site model, docs generation, README generation, and catalog UI controls.
- [x] Run `uv run wagents openspec validate`.
- [x] Run `uv run wagents validate`.
- [x] Run `uv run wagents readme --check`.
- [x] Run `uv run wagents docs generate --no-installed`.
- [x] Run optional installed inventory generation and local-path scan.
- [x] Run docs Astro check and production build.
- [x] Run package dry-run if packaging metadata changes.
- [x] Run `uv run wagents skills sync --dry-run`.
- [x] Run `git diff --check`.
- [x] Invoke docs stewardship after public docs, README, schema, or generated docs changes.
