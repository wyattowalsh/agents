# TailwindCSS v4 Reference

## 1. CSS-First Configuration

Tailwind v4 eliminates `tailwind.config.js`. Configure everything in CSS.

```css
@import "tailwindcss";          /* Single entry point — replaces @tailwind base/components/utilities */

@theme {
  --color-brand: oklch(0.72 0.11 178);       /* → bg-brand, text-brand, border-brand, etc. */
  --font-display: "Satoshi", sans-serif;     /* → font-display */
  --breakpoint-3xl: 120rem;                  /* → 3xl: variant */
}
```

Tokens in `@theme` become CSS custom properties AND generate utility classes. Use `:root {}` for values that should NOT generate utilities.

## 2. @theme Directive Deep Dive

### Namespace → Utility Mapping

| Namespace | Utilities Generated | Example |
|-----------|-------------------|---------|
| `--color-*` | `bg-*`, `text-*`, `border-*`, `fill-*`, `ring-*` | `--color-primary: oklch(...)` |
| `--font-*` | `font-*` (family) | `--font-display: "Satoshi", sans-serif` |
| `--font-weight-*` | `font-*` (weight) | `--font-weight-bold: 700` |
| `--text-*` | `text-*` (size) | `--text-hero: 4rem` |
| `--tracking-*` / `--leading-*` | `tracking-*` / `leading-*` | `--tracking-wide: 0.025em` |
| `--spacing` | All spacing/sizing: `p-*`, `m-*`, `gap-*`, `w-*`, `h-*` | `--spacing: 0.25rem` |
| `--breakpoint-*` | Responsive variants: `sm:`, `md:`, `lg:` | `--breakpoint-3xl: 120rem` |
| `--radius-*` | `rounded-*` | `--radius-pill: 9999px` |
| `--shadow-*` / `--ease-*` / `--animate-*` | `shadow-*` / `ease-*` / `animate-*` | `--ease-snappy: cubic-bezier(0.2, 0, 0, 1)` |
| `--container-*` | Container query variants: `@sm:`, `@md:` | `--container-card: 20rem` |

### Extending vs Overriding

```css
@theme {
  --color-brand: oklch(0.72 0.11 178);   /* EXTEND — adds to defaults */

  --color-*: initial;                     /* OVERRIDE namespace — wipe all default colors */
  --color-white: #fff;
  --color-brand: oklch(0.72 0.11 178);

  --*: initial;                           /* OVERRIDE everything — blank slate */
}
```

### Referencing Tokens

```css
.hero { color: var(--color-brand); }                /* In CSS */
```
```html
<h1 class="text-brand">...</h1>                     <!-- Generated utility -->
<div class="bg-[var(--color-brand)]">...</div>       <!-- Arbitrary value -->
```

### @theme inline / @theme static

```css
@theme inline {                          /* Resolve variable references at usage site, not definition */
  --font-sans: var(--font-inter);
}

@theme static {                          /* Force CSS variable output even if no utility references it */
  --color-primary: var(--color-blue-500);
}
```

### Keyframes Inside @theme

```css
@theme {
  --animate-fade-in: fade-in 0.3s ease-out;
  @keyframes fade-in {
    from { opacity: 0; transform: scale(0.95); }
    to   { opacity: 1; transform: scale(1); }
  }
}
```

## 3. Dark Mode

**Default:** uses `prefers-color-scheme` media query — no config needed.

```css
/* Class-based (manual toggle) */
@custom-variant dark (&:where(.dark, .dark *));

/* Data attribute */
@custom-variant dark (&:where([data-theme=dark], [data-theme=dark] *));
```

### Token Override Pattern (avoids `dark:` on every element)

```css
@theme {
  --color-surface: #ffffff;
  --color-on-surface: #1a1a1a;
}
.dark {
  --color-surface: #0f172a;
  --color-on-surface: #f1f5f9;
}
```
```html
<body class="bg-surface text-on-surface"><!-- adapts when .dark toggled --></body>
```

### Three-Way Toggle (light / dark / system)

```javascript
document.documentElement.classList.toggle("dark",
  localStorage.theme === "dark" ||
  (!("theme" in localStorage) && window.matchMedia("(prefers-color-scheme: dark)").matches));
```

## 4. Container Queries

Built into v4 — no plugin required (replaces `@tailwindcss/container-queries`).

```html
<!-- Basic -->
<div class="@container">
  <div class="flex flex-col @md:flex-row @lg:gap-8">...</div>
</div>

<!-- Named containers -->
<div class="@container/main">
  <div class="@container/sidebar">
    <p class="@md/main:text-lg @sm/sidebar:p-4">Targets specific ancestors</p>
  </div>
</div>

<!-- Max-width / range -->
<div class="@container">
  <div class="@max-md:flex-col">Stacks on small containers</div>
  <div class="@min-md:@max-xl:hidden">Hidden between md–xl</div>
  <div class="@[500px]:grid-cols-2">Arbitrary breakpoint</div>
</div>
```

Define custom container sizes: `--container-card: 20rem` in `@theme` generates `@card:` variant.

## 5. Custom Utilities and Variants

### @utility — Static and Functional

```css
@utility tab-4 { tab-size: 4; }                     /* Static: class="tab-4" */

@utility tab-* { tab-size: --value(integer); }       /* Functional: class="tab-2", "tab-8" */

@utility tab-* { tab-size: --value(--tab-size-*); }  /* Theme-keyed: class="tab-github" */

@utility bg-brand-* {                                /* With --modifier() */
  background-color: oklch(0.72 0.11 178 / --modifier(percentage));
}                                                    /* class="bg-brand/50" */
```

### @variant — Apply Variants in CSS

```css
.card {
  background: white;
  @variant hover { background: var(--color-gray-50); }
  @variant dark  { background: var(--color-gray-900); }
}
```

### @custom-variant — Create New Variants

```css
@custom-variant theme-midnight (&:where([data-theme="midnight"] *));    /* Shorthand */

@custom-variant theme-midnight {         /* Block syntax */
  &:where([data-theme="midnight"] *) { @slot; }
}
```

## 6. v3 to v4 Migration Checklist

### Build Setup

| v3 | v4 |
|----|-----|
| `tailwindcss` as PostCSS plugin | `@tailwindcss/postcss` |
| `npx tailwindcss -i ...` | `npx @tailwindcss/cli -i ...` |
| — | `@tailwindcss/vite` (recommended for Vite) |

### Renamed Utilities

| v3 | v4 | v3 | v4 |
|----|-----|----|----|
| `shadow-sm` | `shadow-xs` | `rounded-sm` | `rounded-xs` |
| `shadow` | `shadow-sm` | `rounded` | `rounded-sm` |
| `blur-sm` | `blur-xs` | `outline-none` | `outline-hidden` |
| `blur` | `blur-sm` | `ring` | `ring-3` |
| `drop-shadow-sm` | `drop-shadow-xs` | `drop-shadow` | `drop-shadow-sm` |

### Removed Utilities

| Removed | Replacement |
|---------|-------------|
| `bg-opacity-50` | `bg-black/50` |
| `text-opacity-75` | `text-red-500/75` |
| `border-opacity-*` | `border-black/50` |
| `flex-shrink-*` / `flex-grow-*` | `shrink-*` / `grow-*` |
| `overflow-ellipsis` | `text-ellipsis` |

### Syntax Changes

```
Important modifier:     !flex → flex!            (trailing, not leading)
Variant stacking:       first:*:pt-0 → *:first:pt-0  (left-to-right)
CSS var arbitrary:      bg-[--brand] → bg-(--brand)   (parens, not brackets)
Grid template:          grid-cols-[1fr,auto] → grid-cols-[1fr_auto]  (underscores)
Custom utilities:       @layer utilities { ... } → @utility name { ... }
```

### Default Behavior Changes

| Behavior | v3 | v4 |
|----------|----|----|
| Border color | `gray-200` | `currentColor` |
| Ring width / color | `3px` / `blue-500` | `1px` / `currentColor` |
| Placeholder color | `gray-400` | Current text at 50% opacity |
| Button cursor | `pointer` | `default` |
| Hover | Always applies | Only on `(hover: hover)` devices |

### @config Bridge

```css
@import "tailwindcss";
@config "../../tailwind.config.js";       /* Gradual migration — loads JS config */
```

Unsupported in v4: `corePlugins`, `safelist` (use `@source inline()`), `separator`.

Run `npx @tailwindcss/upgrade` to automate. Review on a branch.

## 7. Common Gotchas

| Gotcha | Detail |
|--------|--------|
| **Sass/Less/Stylus** | Incompatible. Use plain CSS or PostCSS. |
| **Autoprefixer / postcss-import** | Redundant — Lightning CSS handles both. Remove them. |
| **resolveConfig()** | Removed. Read CSS variables via `getComputedStyle()`. |
| **JS config auto-detection** | Gone. Use `@config` directive explicitly. |
| **@apply in Vue/Svelte/CSS Modules** | Prefix with `@reference "../../app.css"` or `@reference "tailwindcss"`. |
| **`hidden` attribute** | Takes priority over display utilities. Remove attribute to show element. |
| **space-* selector** | Changed to `:not(:last-child)`. Prefer `gap-*`. |
| **Browser support** | Safari 16.4+, Chrome 111+, Firefox 128+. |
| **Individual transforms** | `rotate`/`scale`/`translate` are individual properties. Use `scale-none` not `transform-none`. |
| **Transition includes outline** | `transition` now includes `outline-color`. Set outline color explicitly. |
| **Plugin compat** | v3 JS plugins work via `@plugin` but may need updates. |
