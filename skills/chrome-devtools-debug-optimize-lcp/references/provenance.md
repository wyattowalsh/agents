# Provenance

- Source: `https://github.com/ChromeDevTools/chrome-devtools-mcp/tree/main/skills/debug-optimize-lcp`
- Repository commit: `a90378adf3226e8b27a05cdcfdd801c199acaa93`
- Package: `chrome-devtools-mcp`
- Package version: `0.23.0`
- Author: Google LLC
- License: Apache-2.0
- Access date: 2026-05-01
- Source-list evidence: `npx skills add github:ChromeDevTools/chrome-devtools-mcp --list` returned upstream `debug-optimize-lcp`.

## Adaptation Notes

- Renamed from upstream `debug-optimize-lcp` to make the Chrome DevTools dependency explicit.
- Kept LCP subpart, trace, insight, network waterfall, and snippet workflows.
- Added repo-required frontmatter, dispatch routing, and telemetry/privacy note.
- No hooks, command substitutions, or automatic install side effects are present.
