# Affected Surfaces

## Source Of Truth

`skills/files-buddy/` and this OpenSpec change. Native metadata is reconciled
against actual repository support; no inert global registry is invented.
The canonical skill audit recognizes portable Input/Mode dispatch tables and
harness-neutral state paths, with positive and negative regression tests in
`tests/test_skill_creator_audit.py`. This corrects false negatives exposed by
the portable source change without lowering behavioral acceptance requirements.
The documentation renderer recognizes the same portable dispatch heading and
keeps the required Starlight component import in generated research pages.
Authoring projection falls back to valid portable metadata author/version fields
while preserving legacy top-level precedence.

## Generated Outputs

The files-buddy authoring/catalog page and catalog index, and README if changed
by its owning generator. Generated changes are delegated to docs-steward.

## Downstream Agent Artifacts

Portable skill packaging only. No live harness configuration or installation.

## Tests

Skill-local executable tests and focused repository integration/portability tests.
`.github/workflows/files-buddy.yml` runs the isolated package on Linux and macOS
and a Chromium dashboard fixture using the existing root Playwright lock. The
existing repository suite includes `tests/test_files_buddy_runtime.py`.

## Validation Commands

`uv run python scripts/check.py` from the skill, focused pytest and Ruff,
package dry-run, generated-document parity, OpenSpec validation, and relevant
repository validation. Exact outcomes are recorded in validation-matrix.md.
