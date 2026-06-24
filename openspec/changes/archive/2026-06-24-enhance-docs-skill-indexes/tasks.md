# Tasks

## OpenSpec

- [x] Add OpenSpec artifacts for this change.

## Data And Generation

- [x] Extend site data with custom, curated external, installed external, all-skill, external-group, and install-script exports.
- [x] Treat installed-only skills as external rows unless they collide with custom skills.
- [x] Dedupe curated and installed external rows by normalized source/name.
- [x] Normalize curated external target-agent suffixes to supported Skills CLI IDs.
- [x] Add custom-only `/skills/`, combined `/skills/all/`, and `/skills/install/` generated pages.
- [x] Update `/external-skills/` to include curated external rows plus installed external rows.
- [x] Update generated sidebar with explicit Custom, All, Install Scripts, External, and optional Installed entries.

## Rendering And UI

- [x] Fix generated MDX escaping for inline angle-bracket placeholders in code spans.
- [x] Improve skill catalog filtering and compact command display for large indexes.

## Validation

- [x] Add tests for custom-only coverage, all-skills composition, external dedupe, install scripts, target validation, and MDX escaping.
- [x] Regenerate docs and README.
- [x] Run unit tests, repo validation, OpenSpec validation, skill sync dry-run, docs build, and browser QA.
