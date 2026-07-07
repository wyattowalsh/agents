# Proposal

## Problem

The docs site plugin requests span additive Markdown helpers, theme/navigation owners, content-source plugins, output generators, search providers, and examples. Installing the whole list blindly would create Starlight component override conflicts, route-policy drift, live network build behavior, and peer dependency failures.

## Intent

Enable the Astro/Starlight plugins that are compatible with the current Astro 7, Starlight 0.41, Vite 8, generated-sidebar, Black theme, site-graph, links-validator, and llms.txt owners. Record every deferred requested plugin in a public docs ledger with the concrete unblock condition.

## Validation

- `pnpm peers check`
- `pnpm exec astro check`
- `pnpm exec astro build`
- `uv run wagents openspec validate`
- `uv run wagents docs generate --no-installed`
