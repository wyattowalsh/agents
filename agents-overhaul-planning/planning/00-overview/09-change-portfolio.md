# Change Portfolio

## Portfolio themes

| Theme | Outcome | Main directories | Task clusters |
|---|---|---|---|
| Repo truth | Planning docs stay synchronized with live repo structure | `00-overview`, `manifests`, `99-task-graph` | C00, C08 |
| Skills-first extension | Portable CLI-backed skills become default capability unit | `40-skills-ecosystem`, `30-adapters/skills` | C02 |
| MCP live-systems layer | MCP collection becomes curated, audited, portable, non-redundant | `35-mcp-audit`, `50-config-safety` | C03, C06 |
| Harness projection | Every tool gets explicit support tier and projection contract | `20-harness-registry`, `30-adapters` | C01, C04 |
| Transactional UX | Users can inspect, preview, apply, and rollback safely | `90-ui-ux`, `50-config-safety` | C05, C06 |
| CI/evals/observability | Claims are validated automatically | `60-ci-cd`, `70-evals`, `80-observability` | C07 |
| Documentation truth | README, instructions, docs, matrices remain consistent | `60-ci-cd`, `95-migration`, `99-task-graph` | C08 |
| OpenSpec governance | Significant changes are spec-governed and auditable | `openspec/**`, `10-architecture` | C00, C09 |

## Prioritization rule

1. Freeze schemas and inventories before adapters.
2. Validate existing skills and MCPs before importing external candidates.
3. Implement dry-run preview before apply/rollback.
4. Generate docs from manifests before hand-editing tables.
5. Promote only source-backed capabilities to `validated`.
