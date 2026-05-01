# Provenance

- Source: `https://github.com/ChromeDevTools/chrome-devtools-mcp/tree/main/skills/a11y-debugging`
- Repository commit: `a90378adf3226e8b27a05cdcfdd801c199acaa93`
- Package: `chrome-devtools-mcp`
- Package version: `0.23.0`
- Author: Google LLC
- License: Apache-2.0
- Access date: 2026-05-01
- Source-list evidence: `npx skills add github:ChromeDevTools/chrome-devtools-mcp --list` returned upstream `a11y-debugging`.

## Adaptation Notes

- Renamed from upstream `a11y-debugging` to avoid a broad namespace collision.
- Kept the upstream Lighthouse, issue-listing, snapshot, focus, tap target, and contrast workflow.
- Added repo-required frontmatter, dispatch routing, and output-size safeguards.
- No hooks, command substitutions, or automatic install side effects are present.
