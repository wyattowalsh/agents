# Site Architecture Reference

Comprehensive map of the docs site for `improve` mode decisions.
Source of truth: `docs/` directory in the agents repository.

---

## Stack

| Layer | Technology | Version constraint |
|-------|------------|--------------------|
| Framework | Astro | ^5.5 |
| Docs toolkit | @astrojs/starlight | ^0.37 |
| Theme | starlight-theme-black | ^0.6.0 |
| View transitions | astro-vtbot | ^2.1.11 |
| OG images | astro-og-canvas | ^0.10.1 |
| Image processing | sharp | ^0.33 |
| Package manager | pnpm | workspace root |

Site URL: `https://agents.w4w.dev`

---

## Design System Tokens

### Defined tokens (`docs/src/styles/custom.css`)

| Token | Value | Usage |
|-------|-------|-------|
| `--type-skill` | `oklch(0.65 0.25 285)` | Violet -- skill cards, sidebar, badges |
| `--type-agent` | `oklch(0.70 0.15 200)` | Cyan -- agent cards, external links |
| `--type-mcp` | `oklch(0.70 0.20 155)` | Emerald -- MCP cards, tip callouts |
| `--primary` (dark) | `oklch(0.65 0.25 285)` | Global accent, active states, hover |
| `--primary` (light) | `oklch(0.5 0.25 285)` | Light mode accent |
| `--primary-foreground` | `oklch(0.98 0 0)` | Text on primary backgrounds |
| `--ring` | `oklch(0.55 0.2 285)` | Focus ring color |
| `--sl-content-width` | `52rem` | Main content column max-width |
| `--sl-font` | `'Geist Sans', system-ui, sans-serif` | Body text |
| `--sl-font-mono` | `'Geist Mono', ui-monospace, monospace` | Code, terminal, stats |
| `--slsg-node-color` | `oklch(0.65 0.25 285)` | Site graph node fill |
| `--slsg-link-color` | `oklch(0.4 0.1 285)` | Site graph link stroke |

### Missing token opportunities

These values are used inline throughout `custom.css` but lack named tokens.
When proposing CSS improvements, extract these into custom properties first.

| Category | Inline values found | Suggested token pattern |
|----------|-------------------|------------------------|
| Spacing scale | gap: 6px/8px/1rem/1.5rem/2rem | `--space-1` through `--space-8` |
| Shadow hierarchy | `box-shadow` with 4+ unique values | `--shadow-sm`, `--shadow-md`, `--shadow-lg`, `--shadow-glow` |
| Border radius | 4px, 6px, 8px, 12px, 50%, 99px | `--radius-sm`, `--radius-md`, `--radius-lg`, `--radius-pill` |
| Motion duration | 0.2s, 0.3s, 0.5s, 0.6s, 1s, 2s | `--duration-fast`, `--duration-normal`, `--duration-slow` |
| Z-index | None defined | `--z-overlay`, `--z-modal`, `--z-toast` |
| Typography scale | 0.7rem, 0.75rem, 0.85rem, 0.875rem, 1rem, 1.05rem | `--text-xs` through `--text-lg` |

---

## CSS Architecture

File: `docs/src/styles/custom.css` (565 lines)

Sections in source order:

| Section | Lines (approx) | Purpose |
|---------|----------------|---------|
| TOKENS | 1--28 | Type colors, primary accent, fonts, content width |
| HERO | 30--148 | Dot grid, gradient text, terminal mockup, agent badges, splash width |
| STATS BAR | 149--169 | Type-coded count pills on splash page |
| CARD EFFECTS | 171--202 | Glass morphism, hover lift, type-coded left borders |
| QUICK START BOX | 204--226 | Gradient background, rainbow top border |
| INSTALL SECTION | 228--235 | Bordered box for install command |
| SIDEBAR ENHANCEMENTS | 237--254 | Type-coded group labels (nth-child), active item glow |
| CODE BLOCKS | 256--263 | Violet top border, gradient border-image |
| TABLES | 265--285 | Rounded corners, striped rows, separated borders |
| TYPOGRAPHY | 287--307 | Letter-spacing, content enter animation, reduced motion |
| ASIDE/CALLOUT | 309--321 | Rounded corners, type-coded left borders |
| BADGE ENHANCEMENTS | 322--495 | Badge row spacing, variant backgrounds, installed indicator |
| PAGE TITLE TYPE ICONS | 330--345 | Circular icon background per asset type |
| VIEW TRANSITIONS | 347--354 | Violet flash on navigation |
| LIGHT MODE | 356--459 | Full overrides for every dark-mode component |
| SPLASH PAGE | 503--565 | Section dividers, steps accent, aside prominence, card grid |
| EXTERNAL LINK CARDS | 543--550 | Cyan accent for `href^="http"` links |
| CONVENTION SKILLS | 552--559 | Blockquote styling after catalog-skill divs |

---

## Starlight Component Overrides

### Currently used (4 slots)

| Slot | File | Purpose |
|------|------|---------|
| Head | `docs/src/components/starlight/Head.astro` | Injects astro-vtbot view transitions, OG image meta, og:type |
| Hero | `docs/src/components/starlight/Hero.astro` | Wraps default; adds typewriter animation, terminal entrance, cursor blink, badge fade-up |
| PageTitle | `docs/src/components/starlight/PageTitle.astro` | Prepends type-coded icon (skill=sparkle, agent=hexagon, mcp=diamond) based on slug prefix |
| Footer | `docs/src/components/starlight/Footer.astro` | In-category prev/next navigation, skill install command footer |

### High-value unused slots

These Starlight slots accept component overrides but are not currently customized.
Listed in estimated impact order for `improve` mode.

| Slot | Opportunity |
|------|-------------|
| SiteTitle | Animated logo, type-coded accent on hover |
| Sidebar | Custom group headers, asset count badges, search within category |
| TableOfContents | Progress indicator, active heading highlight, collapse toggle |
| Search | Custom result ranking, type-coded result icons |
| Pagination | Already partially replaced by Footer; could unify |
| ThemeSelect | Branded toggle animation |
| MobileMenuToggle | Badge count on mobile, type-coded icon |
| ContentPanel | Wrapper for reading-time, breadcrumbs, share buttons |
| PageSidebar | Related assets panel, "installed?" indicator |
| TwoColumnContent | Custom layout for comparison pages |
| Banner | Announcement bar for new skills or releases |
| EditLink | Styled edit-on-GitHub link |
| LastUpdated | Relative time display, commit link |
| Prev/Next | Native Starlight pagination (currently bypassed by Footer) |

---

## Plugin Configuration

Source: `docs/astro.config.mjs`

| Plugin | Import | Key config |
|--------|--------|------------|
| starlight-theme-black | `starlightThemeBlack` | `navLinks` from generated sidebar |
| starlight-links-validator | `starlightLinksValidator` | Default -- validates internal links at build |
| starlight-llms-txt | `starlightLlmsTxt` | Default -- generates `llms.txt` for AI consumption |
| starlight-site-graph | `starlightSiteGraph` | depth=2, zoom/pan/drag/hover enabled, actions: fullscreen/depth/reset-zoom, no external links in sitemap |

---

## Content Architecture

### Collections

| Collection | Path | Status |
|------------|------|--------|
| `docs` | `docs/src/content/docs/` | Active -- all pages |
| `blog` | -- | Not created (potential changelog/release notes) |
| `examples` | -- | Not created (potential usage examples) |

No `content/config.ts` file exists. Starlight manages the `docs` collection schema internally.

### Page inventory

| Path prefix | Pages | Template |
|-------------|-------|----------|
| `/` (index) | 1 | `splash` (hero + no sidebar) |
| `/skills/` | 13 (1 overview + 12 skill pages) | `doc` (default) |
| `/guides/` | 1 | `doc` |
| `/cli/` | 1 | `doc` |
| `/agents/` | 0 | -- (no content yet) |
| `/mcp/` | 0 | -- (no content yet) |

### Sidebar structure

Generated by `wagents docs generate` into `docs/src/generated-sidebar.mjs`.

```
/ (home)
Skills [badge: 12]
  Overview
  Custom (12)
    add-badges, agent-conventions, continuous-improvement,
    honest-review, host-panel, javascript-conventions,
    mcp-creator, orchestrator, prompt-engineer,
    python-conventions, skill-creator, wargame
Guides [badge: 1]
  wargame
CLI Reference
```

Nav links (theme-black top bar): Skills, Guides, CLI.

---

## Font Loading

Geist fonts are loaded via `@fontsource` packages (self-hosted, no external requests):

| Import | Weight | Used for |
|--------|--------|----------|
| `@fontsource/geist-sans/400.css` | Regular | Body text |
| `@fontsource/geist-sans/500.css` | Medium | Nav, footer labels |
| `@fontsource/geist-sans/600.css` | Semibold | Headings, stat pills, table headers |
| `@fontsource/geist-sans/700.css` | Bold | Hero title |
| `@fontsource/geist-mono/400.css` | Regular | Code blocks, terminal, badges |

---

## Astro Features -- Usage Status

### Currently used

| Feature | Where |
|---------|-------|
| View transitions | `astro-vtbot` via Head.astro override; violet-flash keyframe in CSS |
| Starlight components | Card, CardGrid, LinkCard, Aside, Steps, Badge (imported in MDX) |
| Component overrides | 4 slots (Head, Hero, PageTitle, Footer) |
| `template: splash` | Index page (hero, no sidebar) |

### Unused with high potential

| Feature | Current state | Opportunity |
|---------|--------------|-------------|
| Astro Islands (`client:*`) | Zero directives in any MDX | Interactive skill explorer, copy-to-clipboard buttons, search filters, live code previews |
| `astro:assets` image optimization | Not used | WebP/AVIF generation, responsive srcset, lazy loading for screenshots |
| Named view transitions | Only generic root transition | Sidebar morph, content crossfade, card expand animations |
| Content collections (additional) | Only `docs` exists | `blog` for changelog, `examples` for usage patterns |
| Middleware | None | Reading time calculation, breadcrumb generation, analytics |
| API routes / endpoints | None | Dynamic OG images, search index JSON, skill metadata API |

---

## Type Color System

The three-color type system is the primary visual language across the site.
Every improvement should reinforce this system, never introduce competing colors.

| Type | Token | oklch | Hex (approx) | Icon | CSS class prefix |
|------|-------|-------|--------------|------|-----------------|
| Skill | `--type-skill` | `0.65 0.25 285` | #8B5CF6 | Sparkle (U+2726) | `.catalog-skill`, `.stat-skill`, `.page-title-icon--skill` |
| Agent | `--type-agent` | `0.70 0.15 200` | #22D3EE | Hexagon (U+2B21) | `.catalog-agent`, `.stat-agent`, `.page-title-icon--agent` |
| MCP | `--type-mcp` | `0.70 0.20 155` | #34D399 | Diamond (U+25C8) | `.catalog-mcp`, `.stat-mcp`, `.page-title-icon--mcp` |
| Installed | (no token) | `0.70 0.15 45` | #FB923C | -- | `.catalog-installed`, `.stat-installed` |

---

## Animation Inventory

All animations defined in the codebase, for consistency when adding new ones.

| Name | Duration | Easing | Trigger | Defined in |
|------|----------|--------|---------|------------|
| `content-enter` | 0.3s | ease-out | Page load | custom.css |
| `violet-flash` | 0.3s | ease-out | View transition | custom.css |
| `typewriter` | 2s | steps(42) | Hero load (0.5s delay) | Hero.astro |
| `cursor-appear` | 0.01s | -- | After typing (2.5s delay) | Hero.astro |
| `cursor-blink` | 1s | step-end | After typing (2.5s delay) | Hero.astro |
| `fade-up` | 0.5s | ease | After typing (2.8s delay) | Hero.astro |
| `terminal-entrance` | 0.6s | ease | Hero load (0.2s delay) | Hero.astro |

Reduced motion: `prefers-reduced-motion: reduce` disables `content-enter` and `violet-flash`.
The Hero.astro animations do not currently respect `prefers-reduced-motion`.

---

## Key File Paths

| Purpose | Path |
|---------|------|
| Astro config | `docs/astro.config.mjs` |
| Custom CSS | `docs/src/styles/custom.css` |
| Splash page | `docs/src/content/docs/index.mdx` |
| Skills overview | `docs/src/content/docs/skills/index.mdx` |
| Generated sidebar | `docs/src/generated-sidebar.mjs` |
| Head override | `docs/src/components/starlight/Head.astro` |
| Hero override | `docs/src/components/starlight/Hero.astro` |
| PageTitle override | `docs/src/components/starlight/PageTitle.astro` |
| Footer override | `docs/src/components/starlight/Footer.astro` |
| Package manifest | `docs/package.json` |
| Docs generator | `wagents/commands/docs.py` |
