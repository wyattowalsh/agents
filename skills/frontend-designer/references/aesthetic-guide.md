# Aesthetic Guide

Design thinking framework and aesthetic direction catalog for distinctive, memorable interfaces.

---

## 1. Design Thinking Process

Run before writing any visual component code. Skip for utility components, forms, and data tables.

**Purpose** -- Define the problem space before choosing colors or fonts:
- **Who uses this?** Developer, consumer, enterprise buyer, child — the answer reshapes every decision.
- **What task?** Reading longform, scanning a dashboard, making a purchase, exploring art?
- **What emotion?** Trust, excitement, calm, urgency, delight, authority?
- **Competitive landscape?** If every competitor uses blue gradients and rounded cards, that is what you must NOT do.

**Tone** -- Commit to an extreme aesthetic direction and own it. Half-measures produce forgettable interfaces. A brutalist portfolio that commits fully is more memorable than a "clean modern" page that could belong to any SaaS product. Pick ONE direction from the catalog. Do not blend unless the blend itself is the concept.

**Constraints** -- Gather before designing:
- **Framework:** Vite+React (SPA), Next.js (SSR/SSG), Remix (progressive enhancement)
- **Performance:** LCP target, animation frame budget, bundle size ceiling
- **Accessibility:** WCAG AA minimum (non-negotiable), AAA for government/education
- **Brand:** Existing guidelines, color restrictions, required logos, tone of voice

**Differentiation** -- Answer: **What is the ONE thing someone remembers after closing the tab?** Not "clean design" — that is table stakes. Be specific: "typography shifts weight as you scroll," "the color palette shifts with time of day," "every section has a different background texture." If you cannot articulate the differentiator, the design is not ready.

---

## 2. Aesthetic Direction Catalog

| Direction | Key Traits | Best For |
|-----------|-----------|----------|
| **Brutalist** | Raw structure, monospace type, harsh B/W contrast, visible grids, unstyled forms | Dev tools, tech blogs, manifestos, galleries |
| **Maximalist** | Dense layers, 5+ color palettes, ornamental borders, mixed typefaces, pattern fills | Creative portfolios, entertainment, event sites |
| **Minimal** | Extreme restraint, whitespace, one typeface / two weights, monochrome, surgical alignment | Corporate, luxury, documentation, photography |
| **Editorial** | Magazine layouts, strong type hierarchy, multi-column grids, pull quotes, dropcaps | Media, publishing, longform, newsletters |
| **Retro-Futuristic** | CRT glow, neon on dark, scan lines, terminal monospace, glitch animations | Gaming, tech portfolios, cyberpunk |
| **Organic** | Flowing blobs, earth tones (sage, terracotta, cream), hand-drawn SVG, natural textures | Wellness, food, sustainability, outdoor |
| **Luxury** | Gold/metallic accents, serif display, generous letter-spacing, rich textures, deep blacks | Premium brands, fashion, fine dining |
| **Playful** | Bright saturated colors, rounded everything, bouncy spring animations, oversized type | Kids apps, social, casual gaming |
| **Art Deco** | Geometric patterns (chevrons, sunbursts), gold on black/navy, symmetry, decorative borders | Events, hospitality, theater, awards |
| **Industrial** | Metal textures, monochrome + safety-yellow, exposed grids, utilitarian sans-serif, data-dense | Manufacturing, engineering, analytics |
| **Soft Pastel** | Muted colors, gentle gradients, rounded forms, soft shadows, airy spacing | Health apps, education, lifestyle, meditation |

### Implementation Signals by Direction

Each direction implies specific CSS and component choices. Use these as starting points:

- **Brutalist:** `font-family: monospace`, `border: 2px solid black`, no `border-radius`, raw `<fieldset>` and `<legend>`, visible `outline` on focus, `background: white` or `background: black` only.
- **Maximalist:** Multiple `background-image` layers, `mix-blend-mode`, CSS `columns` for magazine flow, `@font-face` with 3+ families, gradient borders via `border-image`.
- **Minimal:** Single `font-family`, two `font-weight` values, `letter-spacing: 0.02em` on headings, `max-width: 65ch` for readability, color palette of 3 values max.
- **Editorial:** CSS `columns` or `column-count`, `::first-letter` for dropcaps, `float` for pull quotes, `font-size` contrast ratio of 4:1+ between display and body.
- **Retro-Futuristic:** `text-shadow` for glow, `box-shadow: 0 0 20px` for neon, `background: repeating-linear-gradient` for scan lines, `animation` with `steps()` for flicker.
- **Organic:** `border-radius: 40% 60% 50% 70%` for blob shapes, CSS `filter: blur()` on background elements, muted oklch chroma (0.04-0.08), `clip-path: polygon()` for irregular edges.
- **Luxury:** `font-variant: small-caps`, `letter-spacing: 0.15em` on labels, `background-image` with marble/texture, `color: oklch(0.8 0.08 85)` for gold, generous `padding-block: 6rem`.
- **Playful:** `border-radius: 9999px` on buttons, `animation: bounce` with spring easing, `rotate: -2deg` on cards, saturated oklch chroma (0.25+), emoji in UI labels.
- **Art Deco:** Repeating geometric `background-image`, `border: 3px double`, symmetrical `grid` layouts, `clip-path` for fan/chevron shapes, gold `oklch(0.8 0.12 85)` on dark `oklch(0.15 0.03 260)`.
- **Industrial:** Monochrome with `oklch(0.85 0.2 90)` safety-yellow accent, `font-weight: 700` utilitarian headings, `gap: 1px` dense grids, `border: 1px solid` everywhere, no `border-radius`.
- **Soft Pastel:** oklch chroma 0.04-0.08, `box-shadow: 0 4px 20px oklch(0 0 0 / 0.05)`, `border-radius: 1rem`, pastel gradient backgrounds, `font-weight: 300` body text.

---

## 3. Color Theory

**Commitment over balance.** One dominant color (60% surface), 1-2 sharp accents (10%), neutrals (30%). Evenly-distributed palettes are forgettable.

```css
@theme {
  --color-primary: oklch(0.45 0.2 260);       /* dominant */
  --color-accent: oklch(0.75 0.18 65);         /* accent — high contrast against primary */
  --color-surface: oklch(0.97 0.005 260);      /* neutral background */
}
```

**oklch for perceptual uniformity.** Unlike hex/hsl, `oklch(lightness chroma hue)` produces consistent perceived brightness across hues. Generate tint/shade scales by adjusting lightness only, keeping chroma and hue fixed.

**Color harmony** -- choose deliberately:

| Model | Rule | Effect |
|-------|------|--------|
| Complementary | Hue +/-180 | Maximum contrast, energetic |
| Split-complementary | Opposite +/-30 | High contrast with nuance |
| Analogous | Adjacent hues (+/-30) | Harmonious, calm |
| Triadic | 120 degrees apart | Vibrant, balanced |

**Dark theme is NOT inverted light mode.** Rethink the hierarchy:
- Surface layers: lightness steps (0.12 -> 0.16 -> 0.20) for elevation, not borders
- Body text: oklch lightness 0.85-0.90 (pure white is harsh)
- Accents: increase chroma slightly — colors that pop on white look muddy on dark
- Shadows: replace drop-shadows with subtle glows or eliminate entirely

---

## 4. Motion Design

**CSS-first.** CSS animations run on the compositor thread. Reach for CSS before any JS library.

**Orchestrated entrance** -- one choreographed page load beats fifty scattered micro-interactions. Stagger `animation-delay` in 80-120ms increments, total under 800ms:

```css
.hero-title    { animation: fade-up 0.6s ease-out both; }
.hero-subtitle { animation: fade-up 0.6s ease-out 0.1s both; }
.hero-cta      { animation: fade-up 0.6s ease-out 0.2s both; }
@keyframes fade-up { from { opacity: 0; translate: 0 1.5rem; } }
```

**Scroll-driven** -- replace JS scroll handlers with native CSS:

```css
.reveal {
  animation: reveal linear both;
  animation-timeline: view();
  animation-range: entry 10% entry 90%;
}
@keyframes reveal { from { opacity: 0; scale: 0.95; } }
```

Guard with `@supports (animation-timeline: scroll())` and provide a static fallback.

**Hover states that surprise** -- go beyond opacity. Combine `scale`, `box-shadow`, color shifts, `clip-path` reveals, and `filter` changes in multi-property transitions.

**Motion library (React)** -- use **Motion** (formerly Framer Motion) when CSS cannot express it: layout animations, shared element transitions, gesture-driven physics.

```tsx
import { motion } from "motion/react";
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ type: "spring", stiffness: 300, damping: 24 }}
/>
```

**Restraint.** Every animation must guide attention, show state change, or provide feedback. "Looks cool" is not a reason. Respect `prefers-reduced-motion: reduce` with a global override that zeroes durations.

---

## 5. Spatial Composition

**Break the grid deliberately.** Establish a grid, then break it with ONE element — the break creates hierarchy because it defies the learned pattern. Use `margin-inline: -2rem` for bleeds, `grid-column: 1 / -1` for full-width breaks.

**Asymmetry and tension.** Centered, symmetrical layouts feel safe and forgettable. Offset with unequal grid columns (`2fr 1fr`), bottom-alignment for diagonal eye flow, rotated elements.

**Overlap and depth.** Layer elements for dimension. Flat layouts feel like spreadsheets:

```css
.card {
  position: relative;
}
.card::before {
  content: "";
  position: absolute;
  inset: -0.5rem;
  background: oklch(0.6 0.15 260 / 0.1);
  border-radius: inherit;
  z-index: -1;
  rotate: 2deg; /* offset background creates depth */
}
```

**Negative space as feature.** Whitespace is compositional, not empty. Generous padding signals confidence. Cramped layouts signal desperation.

**Controlled density.** Maximalist layouts with intentional density are equally valid. Dense because content demands it, not because layout was not designed.

---

## 6. Backgrounds and Visual Details

**Gradient meshes** -- stack multiple `radial-gradient()` layers at different positions with varying oklch hues and opacities for atmospheric depth.

```css
.hero-bg {
  background:
    radial-gradient(ellipse at 20% 50%, oklch(0.6 0.15 260 / 0.4), transparent 50%),
    radial-gradient(ellipse at 80% 20%, oklch(0.7 0.12 330 / 0.3), transparent 50%),
    oklch(0.12 0.02 260);
}
```

**Noise and grain** -- subtle grain overlay (`::after` with inline SVG noise, `opacity: 0.04`, `mix-blend-mode: overlay`) breaks sterile digital flatness.

**Decorative borders** -- move beyond `1px solid`. Use `double`, `dashed`, `dotted`, or custom SVG borders. Match border style to aesthetic direction (sharp for brutalist, rounded for playful).

**Dramatic shadows** -- large diffused multi-layer `box-shadow` for floating elevation. Two layers: tight subtle + wide diffused.

**Custom cursors** -- context-specific cursor changes reinforce the aesthetic (crosshair for precision tools, pointer with custom SVG for creative sites).

---

## 7. Anti-Slop Rules

Non-negotiable. Violating any rule produces generic, forgettable output.

1. **NEVER use Inter, Roboto, Arial, or system fonts as primary.** Defaults are not decisions. Select a font that reinforces the aesthetic direction.
2. **NEVER use purple-to-blue gradients on white backgrounds.** The single most cliched AI-generated design pattern.
3. **NEVER produce cookie-cutter layouts recognizable as AI-generated.** If the layout swaps between three products unnoticed, it has no identity.
4. **NEVER reuse the same aesthetic direction across projects.** Each project gets its own visual identity from its unique purpose and audience.
5. **NEVER use generic stock imagery or placeholder icons without context.** Every visual element earns its place through content relevance.
6. **Match complexity to vision.** Maximalism needs elaborate layered code. Minimalism needs surgical precision. Both demand equal effort.
7. **Every decision must be INTENTIONAL.** Default choices are anti-design. If you cannot explain why a value exists, remove it.
