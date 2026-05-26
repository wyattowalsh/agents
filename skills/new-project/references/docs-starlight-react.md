# Starlight And React Docs

Astro Starlight is the lightweight docs default.

## Profiles

| Profile            | Include                                                | Exclude by default          |
| ------------------ | ------------------------------------------------------ | --------------------------- |
| `docs-lite`        | Astro, Starlight, Markdown/MDX                         | Tailwind, shadcn, Fumadocs  |
| `docs-themed`      | Starlight plus custom CSS or Tailwind v4 compatibility | full component library      |
| `docs-interactive` | Starlight plus React islands                           | full React app architecture |

Use React islands only for concrete interactivity. Use Astro client directives for hydrated components. Prefer Starlight built-ins for cards, asides, tabs, steps, and code blocks before adding shadcn/ui.

Validation:

```bash
pnpm --dir <docs-root> astro check
pnpm --dir <docs-root> astro build
```
