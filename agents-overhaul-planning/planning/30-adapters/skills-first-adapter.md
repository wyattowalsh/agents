# Skills-First Adapter

## Objective

Render and validate skill packages across harnesses while preserving Agent Skills compatibility.

## Responsibilities

- Validate `SKILL.md` metadata.
- Ensure progressive-disclosure resources are structured under scripts/references/assets.
- Generate harness aliases/symlinks/copies where required.
- Produce docs snippets for skill install/use/update.
- Generate CLI conformance tests for script-backed skills.

## Required generated outputs

- skill inventory JSON.
- skill validation report.
- per-harness skill projection fixtures.
- generated skill docs.

## CI gates

- frontmatter schema validation.
- name/description rules.
- script executable tests.
- JSON output tests where applicable.
- no unsafe network/secrets unless declared.
