# Provenance

- Source: `https://github.com/ChromeDevTools/chrome-devtools-mcp/tree/main/skills/troubleshooting`
- Repository commit: `a90378adf3226e8b27a05cdcfdd801c199acaa93`
- Package: `chrome-devtools-mcp`
- Package version: `0.23.0`
- Author: Google LLC
- License: Apache-2.0
- Access date: 2026-05-01
- Source-list evidence: `npx skills add github:ChromeDevTools/chrome-devtools-mcp --list` returned upstream `troubleshooting`.

## Adaptation Notes

- Renamed from upstream `troubleshooting` to avoid a broad namespace collision.
- Kept the upstream config discovery, connection triage, missing-tools, and diagnostic workflow.
- Added repo-specific guidance to modify canonical sources rather than generated surfaces.
- No hooks, command substitutions, or automatic install side effects are present.
