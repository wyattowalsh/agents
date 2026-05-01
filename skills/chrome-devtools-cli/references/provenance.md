# Provenance

- Source: `https://github.com/ChromeDevTools/chrome-devtools-mcp/tree/main/skills/chrome-devtools-cli`
- Repository commit: `a90378adf3226e8b27a05cdcfdd801c199acaa93`
- Package: `chrome-devtools-mcp`
- Package version: `0.23.0`
- Author: Google LLC
- License: Apache-2.0
- Access date: 2026-05-01
- Source-list evidence: `npx skills add github:ChromeDevTools/chrome-devtools-mcp --list` returned this skill and five sibling Chrome DevTools skills.

## Adaptation Notes

- Kept the upstream CLI command patterns and setup reference.
- Added repo-required frontmatter, dispatch routing, and explicit global-install guardrails.
- No hooks, command substitutions, or automatic install side effects are present.
