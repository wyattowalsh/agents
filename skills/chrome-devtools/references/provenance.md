# Provenance

- Source: `https://github.com/ChromeDevTools/chrome-devtools-mcp/tree/main/skills/chrome-devtools`
- Repository commit: `a90378adf3226e8b27a05cdcfdd801c199acaa93`
- Package: `chrome-devtools-mcp`
- Package version: `0.23.0`
- Author: Google LLC
- License: Apache-2.0
- Access date: 2026-05-01
- Source-list evidence: `npx skills add github:ChromeDevTools/chrome-devtools-mcp --list` returned this skill and five sibling Chrome DevTools skills.

## Adaptation Notes

- Kept the upstream browser lifecycle, page-selection, snapshot-first, and output hygiene workflow.
- Added repo-required frontmatter, dispatch routing, NOT-for boundaries, and large-artifact safeguards.
- Removed no upstream functionality that affects MCP tool usage.
- No hooks, command substitutions, or automatic install side effects are present.
