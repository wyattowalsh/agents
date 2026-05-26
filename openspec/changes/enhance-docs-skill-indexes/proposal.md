# Proposal

## Problem

The docs skill catalog currently blends repo-owned custom skills, curated external skills, and optional installed skills into one broad `/skills/` surface. That makes it hard to verify that custom docs cover exactly `./skills/`, hard to distinguish curated external provenance from local installed inventory, and hard to find copyable install scripts for the full catalog.

The current generated docs build also fails when skill body content includes inline code with angle-bracket placeholders, because generated MDX can interpret placeholders like `<harness|all>` as malformed tags.

## Intent

Restructure generated skill documentation so custom, external, installed, and combined skill views are explicit, deduped, searchable, and build-safe.

## Scope

- Keep repo-owned custom skills sourced only from `./skills/*/SKILL.md`.
- Treat installed skills as external skills unless their name already exists in `./skills/`.
- Keep curated external skill data sourced from `config/external-skills.md`.
- Add generated custom-only, external, all-skills, and install-script views.
- Add generated site data exports for filtered skill indexes and install scripts.
- Normalize curated external target-agent suffixes against the repo-supported Skills CLI target IDs.
- Fix generated MDX escaping for inline code containing angle-bracket placeholders.
- Improve the skill catalog component for large mixed indexes.

## Out Of Scope

- Adding new external skill sources.
- Promoting external or installed skills into repo-owned `skills/`.
- Removing or renaming custom skills.
- Replacing the canonical `npx skills add` install path with `uvx`.
