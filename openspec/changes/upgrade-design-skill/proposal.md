## Summary

Rename the repo-owned `frontend-designer` skill to the single-word `design`
skill and upgrade it into the canonical frontend/product interface design
skill for UI implementation, UX, interaction, motion, accessibility, visual
taste, AI interface patterns, and rendered proof.

## Problem

`frontend-designer` is too narrow for the intended capability. It reads like a
role-specific frontend helper even though the maintained guidance now spans
product surfaces, UI/UX, design systems, motion, AI interfaces, accessibility,
and browser validation. The old slug also encourages overlap with external
design/taste skills instead of making one repo-owned canonical entry point.

## Proposed Change

- Move `skills/frontend-designer/` to `skills/design/`.
- Change the command from `/frontend-designer` to `/design`.
- Treat the first argument as an optional mode hint, not a required mode. Infer
  primary and secondary design modes from the request, path, URL, framework
  signals, visual risk, and proof needs.
- Keep the implementation as one compact skill body plus conditional reference
  files, not multiple overlapping local design skills.
- Fold repo-owned Chrome DevTools browser-proof wrapper skills into `/design`
  references, then remove those wrapper skill directories and catalog rows.
- Fold badge, ShieldCN, and shields-related status indicator workflows into
  `/design` Badge Surface, then remove active wrapper/catalog surfaces.
- Fold overlapping curated external UI/design/browser-proof catalog rows into
  the `/design` research note, then remove the active curated rows.
- Make available Chrome DevTools MCP tools the default rendered-proof path for
  browser-rendered UI, without changing MCP registry/config or running installs.
- Publish research and trust notes for the external UI/design/taste ecosystem
  under `docs/src/skill-research/design.md`.
- Refresh custom catalog authoring, generated catalog pages, generated research
  pages, install scripts, README, and downstream sync previews.

## Non-Goals

- Do not create a legacy alias unless concrete public-consumer evidence and
  maintainer approval require it.
- Do not vendor third-party skills.
- Do not run live external installs or `wagents skills sync --apply`.
- Do not mutate MCP registry, harness config, browser launch config, or global
  Chrome DevTools installs from `/design`.
- Do not hand-edit generated catalog registries or generated docs pages except
  as command output.
