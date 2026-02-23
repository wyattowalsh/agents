# Advanced Patterns

Reference for evolving the docs site at `agents.w4w.dev` from good documentation
into a polished, interactive skill marketplace experience. The site runs
Astro + Starlight + starlight-theme-black.

Consult this file when proposing improvements in `improve` mode or when
evaluating site maturity gaps.

---

## 1. Interactive Skill Explorer (Astro Island)

The site currently serves fully static pages with zero `client:*` directives.
Adding a client-side skill explorer is the single highest-impact interactivity
upgrade.

### Architecture

```
Build time                          Runtime
-----------                         -------
SKILL.md files                      SkillExplorer.tsx (Preact island)
     |                                    |
     v                                    v
wagents docs generate        reads /api/catalog.json
     |                                    |
     v                                    v
catalog.json (public/)        renders card grid + filters
```

### Implementation approach

1. **Build-time data collection**: Extend `wagents docs generate` to emit a
   `docs/public/catalog.json` file containing an array of skill/agent/mcp
   objects with fields: `name`, `type`, `description`, `category`,
   `agentCompatibility[]`, `installCommand`, `href`.

2. **Preact island**: Create `docs/src/components/SkillExplorer.tsx` using
   Preact (Astro's lightest framework integration). Mount with `client:load`
   to hydrate immediately.

   ```astro
   ---
   import SkillExplorer from '../components/SkillExplorer';
   ---
   <SkillExplorer client:load />
   ```

3. **Filtering**: Client-side filtering by:
   - Asset type (skill, agent, mcp)
   - Agent compatibility (claude, gemini, codex, cursor, copilot)
   - Category (if categories are added to frontmatter)
   - Free-text search across name + description

4. **URL-reflected state**: Sync filter state to URL search params so links
   are shareable:
   ```
   /explore/?type=skill&agent=claude&q=review
   ```
   Use `URLSearchParams` on mount to restore state; push to `history.replaceState`
   on filter change.

5. **Keyboard-first search**: Bind `Cmd+K` / `Ctrl+K` to focus the search
   input. Starlight already has a search modal (Pagefind), so consider whether
   this replaces or supplements it. Recommendation: supplement. The explorer
   is for browsing/filtering the catalog; Pagefind is for full-text search
   across all docs content.

### Dependencies

| Package | Purpose | Install |
|---------|---------|---------|
| `@astrojs/preact` | Preact integration for Astro islands | `pnpm add @astrojs/preact` |
| `preact` | UI library for the island | installed as peer by above |

### Effort estimate

| Step | Effort |
|------|--------|
| JSON endpoint generation (CLI change) | ~1 hour |
| Preact island component | ~2 hours |
| URL state sync + keyboard shortcut | ~1 hour |
| Styling to match existing theme | ~1 hour |
| **Total** | **~5 hours** |

### Notes

- The island should read the JSON via `fetch('/catalog.json')` at runtime,
  not import it at build time, so the component stays a pure client component.
- Card rendering in the island should match the existing `.sl-link-card`
  visual style (glass morphism, type-coded borders, hover lift).
- Consider adding `client:visible` instead of `client:load` if the explorer
  is below the fold to defer hydration cost.

---

## 2. Marketplace UX Patterns

Patterns observed in Vercel Templates, Smithery.ai, and npm that translate
well to the skill catalog.

### Skill Card Anatomy

```
+---------------------------------------------------+
| [icon]  skill-name                     [claude] [gemini] |
|                                                   |
| Two-line description with CSS line-clamp          |
| applied to keep card heights uniform...           |
|                                                   |
| $ npx skills add w4w/agents --skill name  [copy]  |
+---------------------------------------------------+
```

| Element | Implementation |
|---------|---------------|
| Icon | Type-coded circle (violet/cyan/emerald) matching `--type-skill` etc. |
| Name | Mono font, linked to detail page |
| Description | 2-line `-webkit-line-clamp: 2` (currently 3 in CSS, consider reducing) |
| Agent badges | Small pills showing compatible agents, using existing `.hero-agent-badge` style |
| Install command | Mono text with copy-to-clipboard button |

### Sort Controls

Provide sort options above the card grid:

| Sort | Implementation |
|------|---------------|
| Relevance | Default when a search query is active; rank by fuzzy match score |
| Newest | Sort by `lastModifiedDate` descending (from catalog.json) |
| Alphabetical | Sort by `name` ascending |
| Most Popular | Defer until analytics are available; placeholder sort by type |

### Progressive Disclosure

Three levels of detail for each asset:

| Level | Where | Content |
|-------|-------|---------|
| Summary | Card in grid | Name, 2-line description, badges |
| Expanded | Click card or expand arrow | Full description, install command, compatibility, related assets |
| Full page | Navigate to `/skills/<name>/` | Complete documentation page |

The expanded level can be implemented as a card flip or a slide-down panel
within the grid. Start with direct navigation (summary -> full page) and add
the expanded level later if the catalog grows past ~30 items.

### Install Flow

One-click copy of the install command, with agent-specific variants:

```
Claude Code:   npx skills add w4w/agents --skill <name> -y -g -a claude-code
Gemini CLI:    npx skills add w4w/agents --skill <name> -y -g -a gemini-cli
All agents:    npx skills add w4w/agents --skill <name> -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot opencode
```

Use a `<Tabs>` component (or inline tab pills in the island) to switch
between agent targets.

### Existing Styles to Leverage

The site already has these marketplace-relevant styles:

- Glass morphism cards (`.sl-link-card` with `backdrop-filter: blur(8px)`)
- Type-coded left borders (`.catalog-skill`, `.catalog-agent`, `.catalog-mcp`)
- Hover lift animation (`transform: translateY(-2px)`)
- Agent badge pills (`.hero-agent-badge`)
- Stats bar (`.stats-bar` with `.stat-skill`, `.stat-agent`, `.stat-mcp`)

Build on these rather than creating parallel styles.

---

## 3. Design System Maturity Checklist

The site currently tokenizes type colors (`--type-skill`, `--type-agent`,
`--type-mcp`), fonts (`--sl-font`, `--sl-font-mono`), and content width
(`--sl-content-width`). Everything else uses inline values. This checklist
tracks progress toward a complete design token system.

### Spacing Scale

- [ ] Define and apply consistently

| Token | Value | Use |
|-------|-------|-----|
| `--space-1` | 4px | Tight gaps (badge padding, icon margins) |
| `--space-2` | 8px | Default inline gaps |
| `--space-3` | 12px | Card internal padding |
| `--space-4` | 16px | Section padding, card gaps |
| `--space-5` | 20px | Terminal body padding |
| `--space-6` | 24px | Major section spacing |
| `--space-7` | 28px | Dot grid background-size |
| `--space-8` | 32px | Large vertical rhythm |

### Shadow Hierarchy

- [ ] Define and apply consistently

| Token | Value | Use |
|-------|-------|-----|
| `--shadow-sm` | `0 2px 4px oklch(0 0 0 / 0.1)` | Subtle depth (badges, small elements) |
| `--shadow-md` | `0 4px 12px oklch(0 0 0 / 0.15)` | Cards, panels |
| `--shadow-lg` | `0 25px 50px -12px oklch(0 0 0 / 0.5)` | Terminal mockup, modals |
| `--shadow-glow` | `0 0 40px -10px oklch(0.5 0.2 285 / 0.2)` | Hover accent glow |

### Border Radius Scale

- [ ] Define and apply consistently

| Token | Value | Current usage |
|-------|-------|--------------|
| `--radius-sm` | 6px | Small elements, badges |
| `--radius-md` | 8px | Tables, callouts, asides (currently `8px`) |
| `--radius-lg` | 12px | Cards, terminal, quick-start (currently `12px`) |
| `--radius-full` | 99px | Pill badges, stat badges (currently `99px`) |

### Motion Duration Scale

- [ ] Define and apply consistently

| Token | Value | Use |
|-------|-------|-----|
| `--duration-fast` | 150ms | Micro-interactions (badge hover, focus ring) |
| `--duration-normal` | 300ms | Card transitions, content enter (currently `0.3s`) |
| `--duration-slow` | 500ms | Page transitions, complex animations |

### Z-Index Map

- [ ] Define and apply consistently

| Token | Value | Use |
|-------|-------|-----|
| `--z-dropdown` | 10 | Dropdown menus, autocomplete |
| `--z-sticky` | 20 | Sticky headers, scroll-to-top |
| `--z-fixed` | 30 | Fixed position elements |
| `--z-modal` | 40 | Modal overlays, lightbox |
| `--z-tooltip` | 50 | Tooltips, popovers |

### Typography Scale

- [ ] Define and apply consistently

| Token | Value | Use |
|-------|-------|-----|
| `--text-xs` | 0.7rem | Agent badge text (currently `0.7rem`) |
| `--text-sm` | 0.75rem | Terminal title, small labels (currently `0.75rem`) |
| `--text-base` | 0.875rem | Terminal body, code (currently `0.875rem`) |
| `--text-md` | 1rem | Stat text, quick-start headings (currently `1rem`) |
| `--text-lg` | 1.05rem | Body text, splash asides (currently `1.05rem`) |
| `--text-2xl` | 1.5rem | Section headings |

### Color Semantics

- [ ] Define and apply consistently

| Token | Proposed Value | Use |
|-------|---------------|-----|
| `--color-success` | `oklch(0.70 0.20 155)` (emerald, same as `--type-mcp`) | Success states |
| `--color-warning` | `oklch(0.75 0.15 65)` (amber, same as caution aside) | Warning states |
| `--color-error` | `oklch(0.65 0.20 25)` (red, same as terminal dot) | Error states |
| `--color-info` | `oklch(0.70 0.15 200)` (cyan, same as `--type-agent`) | Info states |

---

## 4. Starlight Plugin Upgrades

Plugins to evaluate for addition to `docs/astro.config.mjs`. The site
currently uses 4 plugins: `starlight-theme-black`, `starlight-links-validator`,
`starlight-llms-txt`, `starlight-site-graph`.

### starlight-showcases

Gallery/showcase layout for featured skills and agents.

| Attribute | Detail |
|-----------|--------|
| **What it does** | Provides `<ShowcaseCard>` and `<ShowcaseGrid>` components for visually rich gallery layouts with images, descriptions, and links |
| **Install** | `pnpm add starlight-showcases` |
| **Integration effort** | Low. Add to plugins array, use components in a new `/showcase/` page |
| **Expected impact** | High for discoverability. A curated "Featured Skills" page with screenshots or demo GIFs |
| **Best for** | A `/featured/` or `/showcase/` landing page highlighting top skills |

### starlight-image-zoom

Lightbox for images and diagrams.

| Attribute | Detail |
|-----------|--------|
| **What it does** | Adds click-to-zoom lightbox on all images in content pages. Uses medium-zoom under the hood |
| **Install** | `pnpm add starlight-image-zoom` |
| **Integration effort** | Minimal. Add to plugins array; works automatically on all `<img>` elements |
| **Expected impact** | Medium. Improves UX for architecture diagrams, screenshots, and flowcharts |
| **Best for** | Pages with diagrams (site graph screenshots, MCP architecture diagrams) |

### starlight-heading-badges

Visual markers on headings.

| Attribute | Detail |
|-----------|--------|
| **What it does** | Adds configurable badges (New, Deprecated, Beta, etc.) next to headings via frontmatter or inline syntax |
| **Install** | `pnpm add starlight-heading-badges` |
| **Integration effort** | Low. Add to plugins array, then annotate headings with badge syntax |
| **Expected impact** | Medium. Helps users scan pages for new features, deprecated APIs, and experimental sections |
| **Best for** | Changelog pages, skill pages with experimental features |

### starlight-scroll-to-top

Scroll-to-top button for long pages.

| Attribute | Detail |
|-----------|--------|
| **What it does** | Adds a floating button that appears after scrolling down, returns user to page top on click |
| **Install** | `pnpm add starlight-scroll-to-top` |
| **Integration effort** | Minimal. Add to plugins array; customize appearance via CSS variables |
| **Expected impact** | Low-medium. Quality of life for long skill pages (docs-steward, honest-review) |
| **Best for** | Any page exceeding 3 screen heights |

### Priority Order

1. **starlight-image-zoom** -- minimal effort, immediate UX win
2. **starlight-showcases** -- enables the featured skills page
3. **starlight-heading-badges** -- useful for changelog and evolving content
4. **starlight-scroll-to-top** -- nice to have, low priority

---

## 5. Content Collection Extensions

The site does not currently have a `src/content/config.ts` file (Starlight
manages its own content collection internally). Extensions require creating
this file with explicit schema definitions.

### Blog Collection for Changelog

Add a `blog` content collection alongside the Starlight `docs` collection
for release notes and changelog entries.

```ts
// docs/src/content/config.ts
import { defineCollection, z } from 'astro:content';
import { docsSchema } from '@astrojs/starlight/schema';

const docs = defineCollection({
  schema: docsSchema({
    extend: z.object({
      // Extended fields for skill/agent/mcp pages
      category: z.string().optional(),
      agentCompatibility: z.array(z.string()).optional(),
      installCommand: z.string().optional(),
    }),
  }),
});

const blog = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string(),
    date: z.date(),
    tags: z.array(z.string()).optional(),
    draft: z.boolean().default(false),
  }),
});

export const collections = { docs, blog };
```

### Computed Fields

These cannot be defined in the Zod schema directly but can be computed
during build via Astro's data pipeline or a remark plugin:

| Field | Source | Implementation |
|-------|--------|---------------|
| `readingTime` | Word count / 200 wpm | Remark plugin (`remark-reading-time`) |
| `wordCount` | Raw text length | Same remark plugin |
| `lastModifiedDate` | Git log | `lastUpdated: true` in Starlight config (already enabled) |

### Frontmatter Extensions

Extend the generated MDX frontmatter with fields that `wagents docs generate`
populates from SKILL.md / agent.md metadata:

| Field | Type | Source |
|-------|------|--------|
| `category` | `string` | Derived from skill directory or explicit frontmatter |
| `agentCompatibility` | `string[]` | Computed from which bridge files reference the asset |
| `installCommand` | `string` | Generated from `npx skills add` pattern + skill name |

These fields feed both the content collection schema validation and the
catalog.json endpoint for the skill explorer.

### Implementation Steps

1. Create `docs/src/content/config.ts` with extended docs schema
2. Update `wagents docs generate` to emit the new frontmatter fields
3. Add `remark-reading-time` plugin to `astro.config.mjs`
4. Create `docs/src/content/blog/` directory with first changelog entry
5. Add a `/changelog/` page that lists blog entries
6. Verify build passes with the new schema

---

## 6. Performance Optimization

### Image Optimization

The site uses `sharp` (already in dependencies) for image processing. Use
Astro's built-in image optimization:

```astro
---
import { Image } from 'astro:assets';
import diagram from '../assets/architecture.png';
---
<Image src={diagram} alt="Architecture diagram" widths={[400, 800]} formats={['webp', 'avif']} loading="lazy" />
```

| Technique | Status | Action |
|-----------|--------|--------|
| WebP/AVIF format | Available via `sharp` | Use `formats` prop on `<Image>` |
| Responsive `srcset` | Available via `widths` prop | Define 2-3 breakpoints |
| Lazy loading | Available via `loading="lazy"` | Apply to below-fold images |
| Explicit dimensions | Required for CLS prevention | Always set `width`/`height` or use imported images |

### Build-Time Data Precomputation

Generate static data files during the build step rather than computing them
at runtime:

| Data | File | Consumer |
|------|------|----------|
| Skill catalog | `public/catalog.json` | Skill explorer island |
| Search index | Built-in Pagefind (already configured) | Starlight search |
| Sidebar config | `src/generated-sidebar.mjs` (already generated) | Starlight sidebar |

The catalog.json generation should happen in `wagents docs generate` alongside
the MDX and sidebar generation. This keeps all generated artifacts in one
pipeline step.

### Component Lazy Loading

For heavy interactive islands (skill explorer, future diagram viewers):

| Directive | When to Use |
|-----------|-------------|
| `client:load` | Island is above the fold and needed immediately |
| `client:visible` | Island is below the fold; hydrate when scrolled into view |
| `client:idle` | Island is non-critical; hydrate when browser is idle |
| `client:media` | Island is only relevant at certain viewport sizes |

Recommendation: Use `client:visible` for the skill explorer if placed below
the hero section. Use `client:idle` for any analytics or non-interactive
widgets.

### Font Subsetting

The site loads Geist Sans (400, 500, 600, 700) and Geist Mono (400) via
`@fontsource` (~120 KB total woff2). Optimization options:

1. **Reduce weights**: Audit if 500 weight is used — CSS uses 400 default and 600 for emphasis
2. **Preload critical font**: Add `<link rel="preload">` for 400 weight in `Head.astro`
3. **Fontsource subsetting**: Already uses `unicode-range` — browser downloads only needed subsets

### Build Performance

| Technique | Impact | Implementation |
|-----------|--------|---------------|
| Parallel page generation | Medium | Already handled by Astro's build pipeline |
| Skip unchanged pages | Low | Astro does not support incremental builds natively; full rebuild is fast (~10s) |
| Minimize plugin count | Low | Current 4 plugins are reasonable; each adds ~1s to build |
| Tree-shake unused CSS | Medium | Starlight handles this; avoid importing large CSS libraries |
