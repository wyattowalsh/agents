# Agents docs site

Public documentation for [agents.w4w.dev](https://agents.w4w.dev). Astro 6 + Starlight + `starlight-theme-black`.

## Maintainer quickstart

```bash
uv run wagents docs init
uv run wagents docs generate --no-installed
cd docs && pnpm dev
uv run wagents docs build
uv run wagents docs lint
uv run wagents docs compose --check-composed --min-pct 100
uv run wagents docs score --write-manifest
```

## Source of truth

| Content | Edit here |
| --- | --- |
| Custom skills catalog | `skills/<name>/SKILL.md` |
| Curated external skills | `docs/src/authoring/skills/<id>.mdx` |
| Composed catalog pages | `docs/src/content/docs/skills/catalog/**` (`HAND-MAINTAINED`) |
| MCP registry stubs | `config/mcp-registry.json` + `wagents docs generate` |
| Hand hubs | `mcp/index.mdx`, `hooks/index.mdx`, `start-here.mdx`, `contributing.mdx` |

Research cache: `docs/src/skill-research/*.md` (embedded on catalog pages; no standalone `/skill-research/` URLs).
