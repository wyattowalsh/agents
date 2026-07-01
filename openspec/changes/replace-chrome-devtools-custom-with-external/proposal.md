# Proposal

## Why

The repository previously vendored six Chrome DevTools skills into `skills/` with
`chrome-devtools*` repo names. That duplicated upstream guidance from
`ChromeDevTools/chrome-devtools-mcp`, increased maintenance burden, and drifted
from the repo policy that curated external skills stay install-now catalog rows
rather than copied trees.

Upstream now publishes the canonical skill bundle with provenance, MCP pairing,
and harness plugin support. Removing repo copies and advertising the official
upstream skills reduces duplication while preserving Chrome DevTools MCP registry
and `/design` rendered-proof integration.

## What Changes

- Demote the prior `integrate-chrome-devtools-skills` promotion outcome from
  repo `skills/` copies to `curated-external-catalog` rows.
- Update `planning/manifests/external-skills/chrome-devtools-mcp.json` promotion
  metadata to record six curated-external catalog rows and zero repo skill names.
- Remove custom `chrome-devtools*` skill directories, authoring rows, and
  generated custom catalog pages when implementation waves execute.
- Add curated-external authoring rows and install commands for the six upstream
  skills sourced from `ChromeDevTools/chrome-devtools-mcp`.
- Update `/design` boundary docs and evals to hand off standalone browser
  debugging to upstream skill IDs instead of retained repo copies.
- Supersede `upgrade-design-skill` chrome-retention language with
  curated-external upstream handoff semantics.
- Trim `wagents/eval_adequacy.py` high-risk name lists that assumed repo-owned
  Chrome skill directories.

## Impact

- Consumers install Chrome DevTools skills via `npx skills add
  github:ChromeDevTools/chrome-devtools-mcp` with named `--skill` selectors.
- `/design` keeps UI-facing proof patterns in `rendered-proof.md`; deep browser
  debugging routes to upstream skills.
- Repo MCP registry, plugin/extension ownership, and dedupe rules stay unchanged.
- Generated catalog shifts Chrome family rows from `skills/catalog/custom/` to
  `skills/catalog/external/`.

## Scope

- Planning manifest promotion metadata.
- OpenSpec change artifacts and delta specs.
- `upgrade-design-skill` supersession edits.
- Eval adequacy tooling and design eval boundary assertions.
- Skill-research boundary tables and comparable-alternatives wording.

## Out Of Scope

- Mutating MCP registry, harness config, or browser launch defaults.
- Running live `npx skills add` installs during tooling-only waves.
- Changing upstream skill bodies or plugin packaging.
- Removing `/design` Chrome proof references.

## Affected Users And Tools

- Maintainers of catalog authoring, external skill manifests, and docs generation.
- Users invoking `/chrome-devtools`, `/a11y-debugging`, or related upstream skills.
- `/design` consumers that hand off non-UI browser debugging.
- `wagents eval adequacy` and design eval validation.

## Risks

- Slash-command migration may confuse users accustomed to prefixed repo names:
  mitigate with an explicit migration table in `design.md` and catalog notes.
- Stale generated custom catalog pages may linger until docs generation runs:
  mitigate with validation-matrix checks for zero custom chrome rows.
- High-risk eval adequacy lists may under-count if upstream skill names differ:
  mitigate by keeping `chrome-devtools` as an R3 keyword, not a hard-coded skill
  directory name.