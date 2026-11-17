# Proposal

## Problem

The canonical host-panel skill provides three useful deliberation formats, but its quoted slash-command input, claims of independent initial positions, and global evidence badge do not accurately describe ordinary Chat execution. The repository's full agent bundle also includes unrelated MCP and agent surfaces, so it is not an appropriate distribution for this focused plugin.

## Intent

Adapt `skills/host-panel/` for natural Chat requests and capability-aware execution, then export a narrow skills-only plugin from those canonical files. Preserve research grounding, roundtable/Oxford/Socratic formats, source integrity, and useful final synthesis.

This requires OpenSpec because it changes a public skill interaction contract, distribution metadata, behavioral evaluations, and generated documentation together.

## Scope

- Revise the canonical skill and references, with explicit preservation decisions in `design.md`.
- Add versionless plugin metadata and a deterministic exporter that injects release identity only into the artifact.
- Extend the existing behavioral evaluation manifest and add focused exporter tests.
- Refresh the affected generated skill documentation through the owning tooling.
- Validate the package separately from discovery and behavior in a fresh Chat session.

## Boundaries

No backend, MCP server, app widget, external model credentials, telemetry, automatic persistence, or live account changes are part of the source implementation. A package is not proof that every ChatGPT mode discovers or loads it. Installation and live invocation need their own observed results. Existing generic plugin-builder and distribution-metadata drift are outside this change.

## Source Baseline

Implementation began from `99a5692a0df01e3b6ea416448efde842e3c94e6f`. `skills/host-panel/` remains the sole instruction source. No copied skill tree is maintained under a platform-specific plugin directory.
