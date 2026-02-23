# Modern CSS Reference (2024-2026)

Technical reference for modern CSS features. Each section includes syntax, use cases, browser support, and `@supports` guards where appropriate.

---

## Feature Support Matrix

| Feature | Chrome | Firefox | Safari | Status |
|---|---|---|---|---|
| Container size queries | 105+ | 110+ | 16+ | Baseline |
| Container style queries | 111+ | No | No | Partial — Chromium only |
| `:has()` selector | 105+ | 121+ | 15.4+ | Baseline |
| `@scope` | 118+ | 146+ | 17.4+ | Baseline Newly Available |
| View transitions (same-doc) | 111+ | 133+ | 18+ | Baseline Newly Available |
| View transitions (cross-doc) | 126+ | No | 18.2+ | Partial — Interop 2026 focus |
| Scroll-driven animations | 115+ | Flag only | 26+ | Partial — no Firefox default |
| Anchor positioning | 125+ | Flag only | 26+ | Partial — no Firefox default |
| `color-mix()` | 111+ | 113+ | 16.2+ | Baseline |
| `oklch()` | 111+ | 113+ | 15.4+ | Baseline |
| `contrast-color()` | No | 146+ | TP only | Experimental |
| `@layer` | 99+ | 97+ | 15.4+ | Baseline |
| `@starting-style` | 117+ | 129+ | 17.5+ | Baseline |

**Legend:** Baseline = all major engines ship it. Baseline Newly Available = shipped everywhere within the last 12 months. Partial = missing at least one engine. Experimental = spec in flux, limited implementations.

---

## 1. Container Queries

Container queries let components respond to their own container's size rather than the viewport. Use them for component-level responsive design; reserve `@media` for page layout and user preferences.

### Size Queries (Production-Ready)

```css
/* Define a containment context */
.card-grid {
  container-type: inline-size;
  container-name: card-grid;
}

/* Query the container's inline size */
@container card-grid (min-inline-size: 40rem) {
  .card {
    grid-template-columns: 1fr 1fr;
  }
}

/* Unnamed container — queries nearest ancestor with containment */
@container (max-inline-size: 20rem) {
  .card-title {
    font-size: var(--text-sm);
  }
}
```

### Style Queries (Chromium Only)

Query custom property values: `@container style(--variant: featured) { ... }`. Not yet supported in Firefox or Safari — use `@supports (container-type: inline-size)` for size queries only.

### Container Queries vs Media Queries

| Use case | Mechanism |
|---|---|
| Component adapts to its available space | `@container` (size) |
| Page layout changes at viewport breakpoints | `@media` (width/height) |
| User preferences (dark mode, reduced motion) | `@media` (prefers-*) |
| Input capability detection | `@media` (hover, pointer) |

### Tailwind v4 Integration

Tailwind v4 generates container query utilities automatically:

```html
<div class="@container">
  <div class="@sm:grid-cols-2 @lg:grid-cols-3">
    <!-- Responds to container size, not viewport -->
  </div>
</div>
```

Named containers use `@container/{name}`:

```html
<div class="@container/sidebar">
  <nav class="@sm/sidebar:flex-row">...</nav>
</div>
```

---

## 2. :has() Selector

The `:has()` relational pseudo-class selects an element based on its descendants or siblings. It enables parent selection, which CSS lacked for decades. Baseline across all major browsers.

### Parent Selection

```css
/* Card containing an error gets a red border */
.card:has(> .error) {
  border-color: var(--color-destructive);
}

/* Card containing an image gets no padding on top */
.card:has(> img:first-child) {
  padding-block-start: 0;
}
```

### Sibling Selection

```css
/* Style a label when its adjacent input is focused */
label:has(+ input:focus) {
  color: var(--color-primary);
}
```

### Form Validation States

```css
/* Entire form changes when it contains invalid fields */
form:has(:invalid) {
  --form-border: var(--color-destructive);
}

/* Submit button disabled appearance when form is invalid */
form:has(:invalid) button[type="submit"] {
  opacity: 0.5;
  pointer-events: none;
}

/* Fieldset highlighting when it contains a focused input */
fieldset:has(:focus-visible) {
  outline: 2px solid var(--color-ring);
}
```

---

## 3. @scope

`@scope` provides native CSS scoping with proximity-based specificity. It eliminates the need for BEM naming conventions or CSS Modules for style isolation. Baseline Newly Available as of Firefox 146 (late 2025).

### Basic Scoping

```css
@scope (.card) {
  h2 { font-size: var(--text-lg); }
  p  { color: var(--color-muted-foreground); }
}
```

### Scoping with Lower Boundary

The `to` clause defines where the scope stops, preventing styles from leaking into nested components:

```css
/* Styles apply inside .card but stop before .card-body */
@scope (.card) to (.card-body) {
  p {
    color: var(--color-muted-foreground);
    font-size: var(--text-sm);
  }
}
```

This is useful for wrapper components that should not style their slotted children.

### Specificity Behavior

- `@scope` does not increase specificity of selectors inside it.
- When two scoped rules match, the one from the **closer** ancestor scope wins (proximity).
- This proximity resolution is a new cascade mechanism distinct from specificity.

### @supports Guard

```css
@supports at-rule(@scope) {
  @scope (.widget) to (.widget__slot) {
    p { margin: 0; }
  }
}
```

---

## 4. View Transitions

View transitions animate between DOM states with CSS-controlled crossfade effects.

### Same-Document Transitions (Baseline Newly Available)

Supported in Chrome 111+, Firefox 133+, Safari 18+.

```js
document.startViewTransition(() => {
  // Update the DOM — framework setState, DOM mutation, etc.
  updateContent();
});
```

Default behavior: full-page crossfade. Customize with `view-transition-name`:

```css
.hero-image {
  view-transition-name: hero;
}

/* Customize the transition for this named element */
::view-transition-old(hero) {
  animation: fade-out 0.3s ease-out;
}
::view-transition-new(hero) {
  animation: fade-in 0.3s ease-in;
}
```

### Cross-Document Transitions (Partial)

Supported in Chrome 126+ and Safari 18.2+. Not yet in Firefox — an Interop 2026 focus area.

```css
/* Enable on both pages via CSS */
@view-transition {
  navigation: auto;
}
```

Elements with matching `view-transition-name` values across pages animate between positions automatically.

Customize with `::view-transition-group(*) { animation-duration: 0.25s; }`. Always add `@media (prefers-reduced-motion: reduce)` with `animation-duration: 0s`.

---

## 5. Scroll-Driven Animations

Replace JavaScript scroll libraries with pure CSS scroll-linked animations. Supported in Chrome 115+ and Safari 26+. Firefox support is behind a flag only — provide fallbacks.

### Scroll Progress Timeline

Animate based on scroll position of a container:

```css
.progress-bar {
  animation: grow-width linear;
  animation-timeline: scroll(root block);
}

@keyframes grow-width {
  from { width: 0%; }
  to   { width: 100%; }
}
```

### View Progress Timeline

Animate based on an element's visibility within the scrollport:

```css
.reveal {
  animation: fade-in linear both;
  animation-timeline: view();
  animation-range: entry 0% entry 100%;
}

@keyframes fade-in {
  from { opacity: 0; translate: 0 2rem; }
  to   { opacity: 1; translate: 0 0; }
}
```

### Animation Range

Control when animation starts/ends: `animation-range: entry 0% entry 100%;`. Range keywords: `entry`, `exit`, `cover`, `contain`.

### @supports Guard

Always guard with `@supports (animation-timeline: view()) { ... }` and set fallback `opacity: 1` outside the guard.

---

## 6. CSS Anchor Positioning

Position elements relative to an "anchor" element without JavaScript. Replaces JS-based tooltip, popover, and dropdown positioning. Supported in Chrome 125+ and Safari 26+. Firefox 145+ has it behind a flag only.

### Basic Anchor Positioning

```css
.trigger {
  anchor-name: --trigger;
}

.tooltip {
  position: fixed;
  position-anchor: --trigger;
  top: anchor(bottom);
  left: anchor(center);
  translate: -50% 0.5rem;
}
```

### position-area Shorthand

`position-area: bottom span-right;` places anchored element on a 3x3 grid. Areas: `top`, `bottom`, `left`, `right`, `center`, `span-left`, `span-right`, `span-top`, `span-bottom`, `span-all`.

### @supports Guard

Guard with `@supports (anchor-name: --x) { ... }`. Provide fixed-position fallback outside the guard.

---

## 7. Color Functions

### color-mix() (Baseline)

Mix two colors in any color space. Use `oklch` for perceptually uniform results:

```css
:root {
  --color-primary: oklch(0.6 0.2 260);
  --color-primary-light: color-mix(in oklch, var(--color-primary) 60%, white);
  --color-primary-dark: color-mix(in oklch, var(--color-primary) 60%, black);
  --color-primary-muted: color-mix(in oklch, var(--color-primary) 40%, transparent);
}
```

### oklch() Color Space (Baseline)

`oklch(lightness chroma hue)` provides perceptual uniformity — equal lightness steps look equally bright to human eyes, unlike `hsl`.

```css
:root {
  /* Palette with consistent perceived brightness */
  --color-blue:   oklch(0.6 0.2 260);
  --color-green:  oklch(0.6 0.2 145);
  --color-red:    oklch(0.6 0.2 25);
  --color-purple: oklch(0.6 0.2 305);
}
```

### contrast-color() (Experimental)

Returns black or white based on which provides sufficient contrast against the given background. Supported in Firefox 146+ and Safari 26.2+ only. No Chrome or Edge support.

**Always provide a fallback:**

```css
.badge {
  background: var(--color-primary);
  /* Fallback: manually chosen contrast color */
  color: oklch(1 0 0);
}

@supports (color: contrast-color(red)) {
  .badge {
    color: contrast-color(var(--color-primary));
  }
}
```

**Limitation:** `contrast-color()` resolves to either black or white only. It does not pick arbitrary colors from a palette.

---

## 8. @layer (Baseline)

Cascade layers give explicit control over style priority, independent of specificity or source order.

### Declaring Layer Order

```css
/* Order declaration — later layers win */
@layer base, components, utilities;

@layer base {
  * { box-sizing: border-box; margin: 0; }
  body { font-family: var(--font-body); }
}

@layer components {
  .card { border-radius: var(--radius); }
  .btn  { padding-inline: 1rem; padding-block: 0.5rem; }
}

@layer utilities {
  .sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0,0,0,0); }
}
```

**Resolution:** Unlayered > last-declared layer > earlier layers. Within a layer, normal specificity applies.

### Tailwind v4 Integration

Tailwind v4 uses `@layer` internally. Its generated utilities sit in the `utilities` layer by default. Custom component styles should go in the `components` layer to avoid specificity conflicts:

```css
@import "tailwindcss";

@layer components {
  .custom-card {
    @apply rounded-lg border bg-card p-6;
  }
}
```

---

## 9. @starting-style (Baseline)

Define initial styles for entry animations when elements first render or transition from `display: none`. Supported in Chrome 117+, Firefox 129+, Safari 17.5+.

### Entry Animation Pattern

```css
dialog[open] {
  opacity: 1;
  scale: 1;
  transition: opacity 0.3s ease, scale 0.3s ease,
              display 0.3s allow-discrete;

  @starting-style {
    opacity: 0;
    scale: 0.95;
  }
}
```

### Combined with display Transition

The `allow-discrete` keyword lets `display` participate in the transition, enabling smooth appear/disappear for `display: none` elements:

```css
.notification {
  display: block;
  opacity: 1;
  translate: 0 0;
  transition: opacity 0.3s, translate 0.3s, display 0.3s allow-discrete;

  @starting-style {
    opacity: 0;
    translate: 0 -1rem;
  }
}

.notification[hidden] {
  display: none;
  opacity: 0;
  translate: 0 -1rem;
}
```

For popovers, add `overlay 0.2s allow-discrete` to the transition and use the same `@starting-style` pattern.

---

## 10. Progressive Enhancement Pattern

Every experimental or partially-supported feature must use `@supports` guards with a working fallback.

### Standard Pattern

```css
/* 1. Fallback that works everywhere */
.tooltip {
  position: fixed;
  top: 10px;
  left: 10px;
}

/* 2. Enhancement for supporting browsers */
@supports (anchor-name: --x) {
  .tooltip {
    position-anchor: --trigger;
    top: anchor(bottom);
    left: anchor(center);
  }
}
```

### Guard Reference by Feature

| Feature | `@supports` condition |
|---|---|
| Container size queries | `(container-type: inline-size)` |
| `:has()` | `selector(:has(*))` |
| `@scope` | `at-rule(@scope)` |
| Scroll-driven animations | `(animation-timeline: view())` |
| Anchor positioning | `(anchor-name: --x)` |
| `contrast-color()` | `(color: contrast-color(red))` |
| `@starting-style` | `at-rule(@starting-style)` |
| `color-mix()` | `(color: color-mix(in oklch, red, blue))` |

### Layered Enhancement

Stack `@supports` blocks from Baseline → Partial → Experimental. Each layer adds behavior without breaking the fallback chain: base styles → `@starting-style` (Baseline) → anchor positioning (Partial) → scroll-driven animations (Partial).

### Mandatory Guards

Features in the **Partial** or **Experimental** columns of the support matrix must always ship behind `@supports`. Features at **Baseline** status may be used without guards in projects targeting modern browsers only.
