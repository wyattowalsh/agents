# Proposal

## Problem

The repository already contains strong agent asset conventions, generated docs, plugin manifests, OpenSpec state, and curated external skill inventory, but those surfaces are still harder than necessary for an outside user or contributor to navigate. Public onboarding does not yet provide a single contributor path, generated skill catalog rows conflate public source identity with local installed inventory, and external skill trust/provenance metadata is not exposed in a fully comparable way across repo-owned, curated external, and installed external skills.

The generated external skill docs can also surface machine-local paths from installed inventory as primary source labels. That is useful maintainer evidence, but it is not appropriate as public OSS catalog metadata.

## Intent

Standardize the whole repository for OSS use without weakening existing internal harness coverage. The change should make public docs, generated indexes, contribution guidance, skill metadata, external trust guidance, cleanup policy, and production-readiness validation easier to audit and maintain.

## Scope

- Add public contributor and safety entrypoints that explain install choices, source-of-truth files, generated artifacts, validation gates, and safe external-skill handling.
- Extend generated skill index rows so repo-owned, curated external, and installed external skills share comparable public fields while preserving trust distinctions.
- Redact or relabel local installed inventory in public docs and generated indexes so absolute local paths are not used as public source labels.
- Improve the skill catalog UI to filter and compare by source type, trust tier, status, provenance or review state, supported agents, installability, and local-only inventory.
- Clarify source-of-truth versus generated surfaces across README, docs, AGENTS/instructions, config, plugin manifests, OpenSpec, tests, and release/distribution metadata.
- Add cleanup and production-readiness checks for generated/local-only cruft, docs build health, package dry-runs, manifest consistency, and no local path/secret exposure.
- Preserve existing supported agents and harness coverage unless a later implementation step documents a verified reason to change a surface.

## Out Of Scope

- Installing new external skills or applying `wagents skills sync --apply`.
- Promoting external or installed skills into repo-owned `skills/` without a separate explicit request.
- Removing supported agents or harnesses.
- Replacing the current markdown source of truth for curated external skills with a new manifest format in the first pass.
- Editing live user configs, secrets, or local-only MCP credentials.
- Deleting uncertain dirty-tree files or unrelated generated output.

## Affected Users And Tools

- External users evaluating whether to install the repo skill bundle.
- Contributors adding or updating skills, agents, docs, MCP config, plugin metadata, or generated public surfaces.
- Maintainers auditing curated external skill sources and installed local inventory.
- Docs readers using the generated skill catalog and external skill index.
- CI and release workflows that validate agent assets, generated README/docs, package output, and OpenSpec state.

## Generated Surfaces To Refresh

- `README.md` if the generated README links or contributor text change.
- Generated docs pages from `uv run wagents docs generate`.
- Generated docs site data and skill index modules.
- Public generated JSON indexes under `docs/public/generated-skill-indexes/`.
- Docs sidebar data if new docs pages are added.

## Risks

- The worktree already contains unrelated dirty files. Implementation must preserve those edits and clearly separate this change's source edits from pre-existing work.
- Installed local inventory can still be useful for private diagnostics. Public redaction should not destroy internal evidence; it should separate display-safe fields from local-only metadata.
- Markdown parsing of `config/external-skills.md` has limits. Only derive structured fields when they are deterministic from existing commands, headings, and notes.
- Generated docs must be changed through generators, not by hand-editing generated pages as the lasting fix.
- Contributor and safety files affect public project posture. Keep them factual, lightweight, and consistent with existing repo policy.
