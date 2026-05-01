# Dashboard App

The dashboard is a modern operational interface. The source design contract is React
with shadcn/ui component patterns, Tailwind CSS v4 tokens, and Recharts charts. The
packaged template remains self-contained so the skill works without installing Node or
loading network CDNs.

## Aesthetic Direction

- Dark-first Mac ops console with precise cards, dense tables, and restrained gradients.
- Distinctive typography: display headings use a geometric/square system; mono values use SF Mono or Monaspace when available.
- Use high-contrast semantic colors: reclaimable green, warning amber, critical red, cloud blue, review violet.
- Avoid generic SaaS dashboards: emphasize local bytes, risk, restore path, and approval state.

## Tailwind v4 Tokens

Use CSS-first tokens in source builds:

```css
@import "tailwindcss";

@theme {
  --color-background: oklch(13% 0.025 260);
  --color-card: oklch(18% 0.028 260);
  --color-border: oklch(28% 0.03 260);
  --color-primary: oklch(70% 0.16 245);
  --color-success: oklch(70% 0.17 150);
  --color-warning: oklch(78% 0.16 80);
  --color-danger: oklch(66% 0.2 28);
  --radius-xl: 1rem;
}

@custom-variant dark (&:where(.dark, .dark *));
```

## Component Contract

| Component | shadcn/ui primitives | Recharts usage |
|-----------|----------------------|----------------|
| `StorageCommandCenter` | Card, Tabs, ScrollArea | coordinates panels |
| `RunStatusHero` | Card, Badge, Progress, Alert | none |
| `SavingsFunnelChart` | Card, Tooltip | FunnelChart or BarChart fallback |
| `ReclaimableByCategory` | Card, Tabs | BarChart/PieChart |
| `RiskMatrix` | Card, Badge, Table | ScatterChart optional |
| `TreemapPanel` | Card, Tooltip | Treemap |
| `DuplicateClusterExplorer` | Accordion, Table, Badge | none |
| `RecommendationCards` | Card, Button, Badge, Separator | mini bars |
| `CacheImpactPanel` | Card, Table | BarChart |
| `CloudOffloadBoard` | Card, Badge, Alert | PieChart |
| `ProgressTimeline` | Card, Progress | none |
| `ManifestExplorer` | Table, Accordion | none |

## Data Inputs

Support both final report and live progress snapshots:

- Legacy: `files`, `duplicates`, `directories`, `operations`, `cloud`, `summary`, `generated`.
- v1.1: `schema_version`, `run_id`, `status`, `phase`, `counts`, `savings`, `categories`, `recommendations`, `events`, `manifest`.

## Packaged Template Requirements

- Self-contained HTML, CSS, and JavaScript.
- No network or CDN by default.
- Same panel names and visual hierarchy as the React source contract.
- Accessible chart fallbacks as tables or text summaries.
- Reduced-motion safe; no required animation for comprehension.

## Smoke Data

Use this minimal shape for renderer checks:

```json
{
  "schema_version": "1.1",
  "run_id": "smoke",
  "status": "completed",
  "savings": {"recommended_local_bytes": 1073741824},
  "categories": [{"name": "Duplicates", "bytes": 1073741824, "risk": "Low"}],
  "recommendations": [{"action": "dedupe", "path": "~/Downloads/a.zip", "local_bytes": 1073741824, "risk": "Low", "restore_path": "manifest undo"}]
}
```
