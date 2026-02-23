# Frontend Anti-Patterns

Detection criteria and fixes for common frontend anti-patterns. Used by **Audit** (Mode E) and **Refactor** (Mode D) modes.

Severity levels:
- **Critical** — Blocks production readiness or causes runtime breakage
- **Warning** — Degrades quality, performance, or maintainability
- **Suggestion** — Improvement opportunity; not urgent

---

### Tailwind v3 JS Config in v4 Project

**Detect:** `tailwind.config.js` or `tailwind.config.ts` exists in the project root while `package.json` lists `tailwindcss` >= 4.0.
**Problem:** Tailwind v4 uses CSS-first configuration via `@import "tailwindcss"` and `@theme {}`. A JS/TS config file signals an incomplete migration and may cause the Oxide engine to fall back to legacy behavior or ignore CSS-first directives entirely.
**Fix:**
1. Move all theme values from `tailwind.config.js` into `@theme {}` blocks in your main CSS file.
2. Move plugin imports to `@plugin` directives.
3. Move content paths to `@source` directives (if needed; v4 auto-detects by default).
4. Delete `tailwind.config.js` / `tailwind.config.ts`.
**Severity:** Critical

---

### Unnecessary "use client" Directives

**Detect:** Grep for `"use client"` in `.tsx` / `.jsx` files. Cross-reference each file for hooks (`useState`, `useEffect`, `useRef`, `useReducer`, `useCallback`, `useMemo`), event handlers (`onClick`, `onChange`, `onSubmit`, `onKeyDown`), or browser APIs (`window`, `document`, `navigator`, `localStorage`). Files with the directive but none of these signals are candidates.
**Problem:** Every `"use client"` boundary pushes the component and its entire import subtree into the client bundle. Unnecessary directives inflate bundle size and forfeit server-side rendering benefits. Applies to Next.js App Router and Remix only; Vite+React projects do not use this directive.
**Fix:**
1. Remove `"use client"` from components that only render markup, fetch data, or compose other server components.
2. Extract interactive parts into small client leaf components; keep parent as server component.
3. Re-verify: the component must build and render without the directive.
**Severity:** Warning

---

### Inline Styles Where Tailwind Suffices

**Detect:** Grep for `style={{` or `style={` in `.tsx` / `.jsx` files. Flag instances where the style sets properties that have direct Tailwind utility equivalents (color, margin, padding, font-size, display, etc.).
**Problem:** Inline styles bypass Tailwind's design token system, skip responsive/dark-mode variants, cannot be purged, and create visual inconsistency. They also make refactoring harder since values are scattered across component files.
**Fix:**
1. Replace `style={{ color: 'red' }}` with `className="text-red-500"` (or a design token: `text-(--color-error)`).
2. For truly dynamic values (e.g., user-provided positioning), use CSS custom properties set via inline style and consumed by a utility class.
3. Acceptable exceptions: values computed at runtime (transforms, positions from drag state).
**Severity:** Warning

---

### !important Overuse

**Detect:** Grep for `!important` in `.css`, `.scss`, `.tsx`, `.jsx` files. Count occurrences; more than 3-5 across the project is a red flag. In Tailwind, grep for the `!` prefix on utility classes (e.g., `!text-red-500`).
**Problem:** `!important` is a specificity escape hatch that makes styles unpredictable and difficult to override. It creates an escalation arms race where future developers add more `!important` to compete.
**Fix:**
1. Diagnose the specificity conflict causing the need for `!important`.
2. Use `@layer` to control cascade order.
3. In Tailwind v4, use `@utility` for custom utilities that participate in the correct layer.
4. Reserve `!important` for genuinely external styles you cannot control (third-party widgets).
**Severity:** Warning

---

### Media Queries for Component Responsiveness

**Detect:** Grep for `@media` inside component-scoped CSS files or CSS modules. Compare count against `@container` usage. Flag `@media (min-width` / `@media (max-width` rules that control component-internal layout (not page-level breakpoints).
**Problem:** Media queries respond to the viewport, not the component's container. A sidebar component styled with `@media` breaks when placed in a narrower context. Container queries make components truly portable.
**Fix:**
1. Add `@container` naming to the parent wrapper element (Tailwind: `@container` or `@container/{name}`).
2. Replace `@media (min-width: ...)` with `@container (min-width: ...)` for component-internal layout shifts.
3. Keep `@media` for page-level layout and user preference queries (`prefers-color-scheme`, `prefers-reduced-motion`).
**Severity:** Warning

---

### Inaccessible Custom Interactive Components

**Detect:** Search for custom implementations of dropdowns, modals, tooltips, popovers, tabs, accordions, or menus that do not import from Radix UI / shadcn/ui. Grep for `role=` and `aria-` attributes in those files; absence confirms the issue.
**Problem:** Custom interactive components built from `<div>` and click handlers are invisible to screen readers, unreachable by keyboard, and violate WCAG 2.1 Level A. This is a legal and ethical liability.
**Fix:**
1. Replace custom implementations with Radix UI primitives via shadcn/ui. Run `npx shadcn@latest add <component>`.
2. If a custom build is truly necessary, follow WAI-ARIA Authoring Practices: add `role`, `aria-expanded`, `aria-controls`, `aria-haspopup`, `aria-labelledby`, keyboard handlers (Enter, Escape, Arrow keys), and focus trapping for modals.
3. Test with a screen reader (VoiceOver, NVDA) and keyboard-only navigation.
**Severity:** Critical

---

### Hardcoded Color Values

**Detect:** Grep for hex (`#[0-9a-fA-F]{3,8}`), `rgb(`, `rgba(`, `hsl(`, `hsla(`, and `oklch(` in `.tsx`, `.jsx`, `.css` files outside of `@theme {}` blocks and CSS custom property definitions.
**Problem:** Hardcoded colors defeat dark mode, theming, and brand consistency. Changing a brand color requires a find-and-replace across dozens of files instead of updating one token.
**Fix:**
1. Extract every unique color into a design token in `@theme {}` using `oklch` for perceptual uniformity.
2. Organize tokens: primitive (raw values) -> semantic (purpose: `--color-error`, `--color-surface`) -> component (scoped overrides).
3. Replace hardcoded values with CSS custom property references or Tailwind utilities that reference tokens.
**Severity:** Warning

---

### Missing Dark Mode Support

**Detect:** Check for absence of `.dark` class selectors, `@custom-variant dark`, `prefers-color-scheme` media queries, and `dark:` Tailwind variants across all CSS and component files. If none found in a user-facing application, flag it.
**Problem:** Users expect dark mode. Without it, the app causes eye strain in low-light environments, drains battery on OLED displays, and feels unfinished compared to modern apps.
**Fix:**
1. Define a dark mode strategy: class-based (`.dark` on `<html>`) for user toggle, or `prefers-color-scheme` for system sync.
2. In Tailwind v4, add `@custom-variant dark (&:where(.dark, .dark *));` to support class-based toggling.
3. Override surface, text, and accent tokens under `.dark {}`.
4. Test every component in both modes; check contrast ratios remain WCAG AA compliant.
**Severity:** Suggestion

---

### Non-RTL-Ready Directional Classes

**Detect:** Grep for physical directional classes and properties: `ml-`, `mr-`, `pl-`, `pr-`, `text-left`, `text-right`, `float-left`, `float-right`, `left-`, `right-`, `border-l-`, `border-r-`, `rounded-l-`, `rounded-r-`, `margin-left`, `margin-right`, `padding-left`, `padding-right`.
**Problem:** Physical directional properties break layout in right-to-left languages (Arabic, Hebrew, Persian). Logical properties adapt automatically based on text direction.
**Fix:**
1. Replace physical utilities with logical equivalents:
   - `ml-4` -> `ms-4` (margin-inline-start)
   - `mr-4` -> `me-4` (margin-inline-end)
   - `pl-4` -> `ps-4` (padding-inline-start)
   - `text-left` -> `text-start`
   - `float-right` -> `float-end`
2. In custom CSS, use `margin-inline-start`, `padding-inline-end`, `inset-inline-start`, etc.
3. Acceptable exceptions: physical positioning for decorative elements or canvas-like layouts.
**Severity:** Suggestion

---

### Deprecated React Patterns

**Detect:** Grep for `class .* extends (React\.)?Component`, `componentDidMount`, `componentWillUnmount`, `componentDidUpdate`, `this.setState`. Also flag `useEffect` calls that fetch data in Next.js/Remix App Router projects (where server components or `loader`/`action` should handle data).
**Problem:** Class components miss hooks, Suspense, and Server Component patterns. `useEffect` for data fetching in server component frameworks causes waterfalls, layout shifts, and duplicated logic that belongs on the server.
**Fix:**
1. Convert class components to function components with hooks.
2. Replace `componentDidMount` data fetching with `async` server components (Next.js), `loader` functions (Remix), or TanStack Query (Vite SPA).
3. Replace `useEffect` data fetching with the `use()` hook + Suspense for client-side async, or move the fetch to a server component.
**Severity:** Warning

---

### Missing Error Boundaries

**Detect:** Grep for `ErrorBoundary` or `error.tsx` / `error.js` (Next.js convention) across the project. Check whether async server components, `<Suspense>` boundaries, and data-dependent UI sections have corresponding error boundaries.
**Problem:** Without error boundaries, a single failed component crashes the entire page. Users see a white screen instead of a graceful fallback, and error context is lost.
**Fix:**
1. In Next.js App Router: add `error.tsx` files at each route segment that fetches data.
2. For standalone React: wrap data-dependent subtrees with `<ErrorBoundary fallback={<ErrorFallback />}>`.
3. Use `react-error-boundary` package or a custom class component (one of the few valid class component uses).
4. Log errors to an observability service in the `onError` callback.
**Severity:** Critical

---

### Missing @supports Guards

**Detect:** Grep for experimental CSS features used without `@supports` wrappers: `anchor(`, `view-transition`, `animation-timeline`, `@scope`, `contrast-color(`, `text-wrap: pretty`, `field-sizing`. Cross-reference with `@supports` blocks in the same files.
**Problem:** Experimental CSS features silently fail in unsupported browsers, causing invisible layout bugs, missing interactions, or broken visuals that only surface in production.
**Fix:**
1. Wrap experimental features in `@supports`:
   ```css
   @supports (animation-timeline: scroll()) {
     .hero { animation-timeline: scroll(); }
   }
   ```
2. Provide a reasonable fallback outside the `@supports` block.
3. Features safe to use without `@supports`: container queries, `:has()`, `oklch()`, `color-mix()` (baseline 2023-2024).
**Severity:** Warning

---

### Font Loading Anti-Patterns

**Detect:** Check `@font-face` declarations for missing `font-display` property. Grep for `.ttf` or `.otf` imports without `.woff2` equivalents. Count font weight imports per family; more than 3-4 per family is excessive.
**Problem:** Missing `font-display` causes invisible text (FOIT) during load. Non-WOFF2 formats are 30-50% larger. Loading too many weights bloats initial page load and delays First Contentful Paint.
**Fix:**
1. Add `font-display: swap` (or `optional` for non-critical fonts) to every `@font-face`.
2. Convert all fonts to WOFF2 format; drop TTF/OTF/WOFF1.
3. Limit to 2-3 weights per family (e.g., regular, medium, bold). Use variable fonts when available.
4. Preload critical fonts: `<link rel="preload" href="font.woff2" as="font" type="font/woff2" crossorigin>`.
**Severity:** Warning

---

### Missing Accessibility Attributes

**Detect:** Grep for interactive elements without accessible names: `<button>` and `<a>` containing only icons (no text content, no `aria-label`). Check `<img>` tags for missing `alt`. Verify heading hierarchy (`<h1>` through `<h6>`) does not skip levels. Grep for `outline: none` or `outline: 0` without a replacement focus indicator.
**Problem:** Screen reader users cannot identify unlabeled controls. Missing alt text hides image content. Broken heading hierarchy confuses navigation. Removed focus indicators make keyboard navigation impossible for sighted users.
**Fix:**
1. Add `aria-label` to icon-only buttons and links: `<button aria-label="Close dialog">`.
2. Add meaningful `alt` text to informational images; use `alt=""` for decorative images.
3. Maintain sequential heading hierarchy: never skip from `<h1>` to `<h3>`.
4. Replace `outline: none` with a visible custom focus indicator: `outline: 2px solid var(--color-focus); outline-offset: 2px;`.
5. Test with axe DevTools or Lighthouse accessibility audit.
**Severity:** Critical

---

### Excessive Client-Side JavaScript

**Detect:** Check bundle size with `npx vite-bundle-visualizer` or Next.js `@next/bundle-analyzer`. Grep `package.json` dependencies for heavy libraries (`moment`, `lodash` full import, `jquery`, `animate.css`). Check for absence of dynamic imports (`React.lazy`, `next/dynamic`, `import()`).
**Problem:** Large JavaScript bundles delay Time to Interactive, increase parse/compile cost on mobile devices, and waste bandwidth. Every kilobyte of JS is 2-3x more expensive than the same kilobyte of HTML/CSS.
**Fix:**
1. Replace heavy libraries: `moment` -> `date-fns` or `Intl.DateTimeFormat`; `lodash` -> individual imports or native methods.
2. Add code splitting: `React.lazy()` + `<Suspense>` for route-level and heavy component splitting.
3. Use `next/dynamic` with `ssr: false` for client-only components in Next.js.
4. Move logic to server components where possible (Next.js/Remix) to eliminate client JS entirely.
5. Set a performance budget: < 200 KB JS (compressed) for initial load.
**Severity:** Warning

---

### No Design Token System

**Detect:** Grep for raw color values, font stacks, spacing values, and border radii scattered across multiple component files without corresponding CSS custom property definitions. Check for absence of `@theme {}` (Tailwind v4), `:root {}` custom property blocks, or any `tokens`/`theme` configuration file.
**Problem:** Without centralized design tokens, visual consistency is maintained by copy-paste — which guarantees drift. Brand updates, dark mode, and theming become project-wide search-and-replace operations. New developers have no single source of truth for design decisions.
**Fix:**
1. Create a `@theme {}` block (Tailwind v4) or `:root {}` block defining all design decisions as CSS custom properties.
2. Organize into layers: primitive tokens (raw values), semantic tokens (purpose-named), component tokens (scoped overrides).
3. Replace all hardcoded values in component files with token references.
4. Document the token taxonomy so new team members know where to find and add values.
**Severity:** Warning

---

## Detection Cheat Sheet

Quick-scan grep patterns for audit and refactor pre-scans.

| Anti-Pattern | Grep Pattern | Target Files |
|---|---|---|
| v3 config in v4 project | `tailwind.config` | Root directory |
| Unnecessary "use client" | `"use client"` | `*.tsx`, `*.jsx` |
| Inline styles | `style=\{\{` | `*.tsx`, `*.jsx` |
| !important overuse | `!important` | `*.css`, `*.tsx`, `*.jsx` |
| @media in components | `@media \(m` | `*.css`, `*.module.css` |
| Missing ARIA / a11y | `<button>.*<svg` (no aria-label) | `*.tsx`, `*.jsx` |
| Hardcoded colors | `#[0-9a-fA-F]{3,8}` | `*.tsx`, `*.jsx`, `*.css` |
| Missing dark mode | `dark:` (absence of matches) | `*.tsx`, `*.jsx`, `*.css` |
| Physical directional classes | `\b(ml\|mr\|pl\|pr)-` | `*.tsx`, `*.jsx` |
| Class components | `extends (React\.)?Component` | `*.tsx`, `*.jsx` |
| useEffect data fetching | `useEffect.*fetch\|useEffect.*axios` | `*.tsx`, `*.jsx` |
| Missing error boundaries | `ErrorBoundary` (absence) | `*.tsx`, `*.jsx` |
| Experimental CSS no guard | `animation-timeline\|anchor\(\|@scope\|contrast-color` | `*.css` |
| Font loading issues | `@font-face` without `font-display` | `*.css` |
| No WOFF2 | `\.ttf\|\.otf\|\.woff[^2]` | `*.css` |
| Missing alt text | `<img(?![^>]*alt)` | `*.tsx`, `*.jsx` |
| Removed focus outline | `outline:\s*(none\|0)` | `*.css` |
| Heavy dependencies | `"moment"\|"lodash"\|"jquery"` | `package.json` |
| No code splitting | `React\.lazy\|next/dynamic` (absence) | `*.tsx`, `*.jsx` |
| No design tokens | `@theme\|--color-\|--font-\|--spacing-` (absence) | `*.css` |
