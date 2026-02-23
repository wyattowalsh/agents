# Docs UI Smoke Harness

Lightweight screenshot and interaction smoke checks for the Astro/Starlight docs site.

## What it covers

- Desktop, tablet, and mobile screenshots for key docs routes
- Basic keyboard navigation smoke (`Tab` traversal + `Escape`)
- Reduced-motion screenshot capture

## Prerequisites

1. Build or run the docs site
2. Install Playwright for Python in the project environment

Example:

```bash
uv add --dev playwright
uv run playwright install chromium
```

## Usage

Start a local docs server (example):

```bash
pnpm --dir docs preview
```

Then run the harness:

```bash
uv run python tests/docs_ui/screenshot_smoke.py --base-url http://127.0.0.1:4321
```

Outputs are written to `artifacts/docs-ui-smoke/` by default.
