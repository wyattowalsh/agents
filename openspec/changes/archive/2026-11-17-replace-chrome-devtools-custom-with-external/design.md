# Design

## Approach

Replace vendored `skills/chrome-devtools*` copies with six curated-external
catalog rows sourced from `ChromeDevTools/chrome-devtools-mcp`. Keep repo MCP
registry ownership, plugin/extension dedupe, and `/design` rendered-proof
patterns unchanged. Record promotion outcome in
`planning/manifests/external-skills/chrome-devtools-mcp.json` as
`curated-external-catalog` with `repo_skill_names: []`.

## Upstream Intake

- Source repository: `https://github.com/ChromeDevTools/chrome-devtools-mcp`
- Upstream skills path: `skills/`
- Inspected upstream commit: `a90378adf3226e8b27a05cdcfdd801c199acaa93`
- Package: `chrome-devtools-mcp` version `0.23.0`
- Author: `Google LLC`; license: `Apache-2.0`
- List evidence: `npx skills add github:ChromeDevTools/chrome-devtools-mcp --list`

## Skill Mapping

| Upstream skill ID | Previous repo custom directory | Curated-external catalog row | Notes |
| --- | --- | --- | --- |
| `chrome-devtools` | `skills/chrome-devtools/` | `chrome-devtools` | Canonical broad MCP page-debug workflow; same slash command after upstream install. |
| `chrome-devtools-cli` | `skills/chrome-devtools-cli/` | `chrome-devtools-cli` | Terminal CLI workflow; same slash command after upstream install. |
| `a11y-debugging` | `skills/chrome-devtools-a11y-debugging/` | `a11y-debugging` | Upstream ID drops the `chrome-devtools-` prefix; `/design` hands off standalone a11y browser debugging here. |
| `debug-optimize-lcp` | `skills/chrome-devtools-debug-optimize-lcp/` | `debug-optimize-lcp` | Upstream LCP trace workflow; `/design` keeps UI-facing hero/LCP heuristics only. |
| `memory-leak-debugging` | `skills/chrome-devtools-memory-leak-debugging/` | `memory-leak-debugging` | Upstream heap/snapshot workflow; `/design` keeps UI lifecycle smell checks only. |
| `troubleshooting` | `skills/chrome-devtools-troubleshooting/` | `troubleshooting` | MCP setup and connection repair; `/design` records blockers but does not own harness repair. |

No repo `skills/` copies remain after implementation waves complete. Provenance
lives in the external manifest, curated-external authoring MDX rows, and
skill-research boundary tables.

## Slash Command Migration

| Previous repo slash (removed) | Upstream slash after install | Install selector |
| --- | --- | --- |
| `/chrome-devtools` | `/chrome-devtools` | `--skill chrome-devtools` |
| `/chrome-devtools-cli` | `/chrome-devtools-cli` | `--skill chrome-devtools-cli` |
| `/chrome-devtools-a11y-debugging` | `/a11y-debugging` | `--skill a11y-debugging` |
| `/chrome-devtools-debug-optimize-lcp` | `/debug-optimize-lcp` | `--skill debug-optimize-lcp` |
| `/chrome-devtools-memory-leak-debugging` | `/memory-leak-debugging` | `--skill memory-leak-debugging` |
| `/chrome-devtools-troubleshooting` | `/troubleshooting` | `--skill troubleshooting` |

Grouped install for all six skills:

```bash
npx skills add github:ChromeDevTools/chrome-devtools-mcp \
  --skill chrome-devtools \
  --skill chrome-devtools-cli \
  --skill a11y-debugging \
  --skill debug-optimize-lcp \
  --skill memory-leak-debugging \
  --skill troubleshooting \
  -y -g
```

## `/design` Boundary

`/design` continues to use Chrome DevTools MCP tools for UI-facing rendered
proof via `skills/design/references/rendered-proof.md`. Standalone browser
debugging, MCP setup repair, CLI automation, deep LCP profiling, and heap
analysis hand off to the curated-external upstream skills listed above—not to
removed repo copies.

## Alternatives Rejected

- Keep vendored `skills/chrome-devtools*` copies: rejected—duplicates upstream
  and violates curated-external catalog policy.
- Fold all Chrome skills into `/design` only: rejected—operational browser
  debugging remains a distinct upstream surface.
- Rename upstream skills to repo-prefixed IDs in catalog: rejected—install
  commands must match upstream `--skill` selectors.

## Migration Notes

- Delete `skills/chrome-devtools*` directories and custom authoring/research
  pages during implementation waves; regenerate docs so custom catalog paths
  disappear.
- Update cross-skill handoffs (`review`, `harness-master`, etc.) from prefixed
  repo names to upstream IDs where slash commands changed.
- `upgrade-design-skill` retention language is superseded by this change.