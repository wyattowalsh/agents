# Provenance

- Source: `https://github.com/ChromeDevTools/chrome-devtools-mcp/tree/main/skills/memory-leak-debugging`
- Repository commit: `a90378adf3226e8b27a05cdcfdd801c199acaa93`
- Package: `chrome-devtools-mcp`
- Package version: `0.23.0`
- Author: Google LLC
- License: Apache-2.0
- Access date: 2026-05-01
- Source-list evidence: `npx skills add github:ChromeDevTools/chrome-devtools-mcp --list` returned upstream `memory-leak-debugging`.

## Adaptation Notes

- Renamed from upstream `memory-leak-debugging` to make the Chrome DevTools dependency explicit.
- Kept the snapshot, memlab, common leak, and detached-node caution workflows.
- Did not vendor the upstream `compare_snapshots.js` fallback script to avoid adding tracked executable surface; use memlab or write a bounded analyzer only with user approval.
- No hooks, command substitutions, or automatic install side effects are present.
