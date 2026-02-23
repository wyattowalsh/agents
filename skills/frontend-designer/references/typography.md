# Typography Reference

Deep technical reference for font selection, @font-face setup, fluid type scales, and variable font optimization.

---

## 1. Monaspace Superfamily

Monaspace is a monospaced type superfamily from [GitHub Next](https://github.com/githubnext/monaspace), designed for code. Five metrics-compatible families share the same character widths, allowing seamless mixing within a single editor or interface.

| Font | Classification | Voice | Use for |
|------|---------------|-------|---------|
| **Monaspace Neon** | Neo-grotesque sans | Clean, neutral, versatile | General-purpose code, default mono |
| **Monaspace Argon** | Humanist sans | Warmer, organic, friendly | Prose-heavy code, documentation |
| **Monaspace Krypton** | Mechanical sans | Structured, technical, rigid | Data-dense output, config files |
| **Monaspace Radon** | Handwriting | Casual, creative, personal | Comments, annotations, git messages |
| **Monaspace Xenon** | Slab serif | Bold, authoritative, editorial | Headings in terminals, display mono |

### Texture Healing

Monaspace introduces **texture healing** — a contextual alternate (`calt`) technique that balances visual density without breaking the monospace grid. Narrow glyphs (like `i`, `l`) donate excess space to wide glyphs (like `m`, `w`) through alternate drawings that shift within fixed-width bounds. The glyph body size never changes, preserving monospace alignment.

Enable via the `calt` OpenType feature in your editor or CSS:

```css
.code {
  font-feature-settings: "calt" 1;
}
```

### Variable Font Axes

Each Monaspace family supports three axes:

| Axis | Tag | Range | Named stops |
|------|-----|-------|-------------|
| Weight | `wght` | 200 -- 800 | Light, Regular, Medium, SemiBold, Bold, ExtraBold |
| Width | `wdth` | 100 -- 125 | Normal (100), SemiWide, Wide (125) |
| Slant | `slnt` | -11 -- 0 | Upright (0), Italic (-11) |

At approximately -11 degrees slant, certain glyphs swap to true italic forms rather than merely oblique.

---

## 2. @font-face Setup

### Monaspace Variable (Recommended)

```css
@font-face {
  font-family: "Monaspace Neon";
  src: url("/fonts/MonaspaceNeonVarVF[wght,wdth,slnt].woff2") format("woff2");
  font-weight: 200 800;
  font-display: swap;
}

@font-face {
  font-family: "Monaspace Radon";
  src: url("/fonts/MonaspaceRadonVarVF[wght,wdth,slnt].woff2") format("woff2");
  font-weight: 200 800;
  font-display: swap;
}
```

### Key Decisions

| Decision | Recommendation | Why |
|----------|---------------|-----|
| Format | WOFF2 only | Best compression (30% smaller than WOFF), universal browser support |
| Hosting | Self-host | Eliminates third-party DNS lookup, full cache control, no CORS issues |
| `font-display` | `swap` | Text renders immediately in fallback font, swaps when loaded |
| Variable vs static | Variable | Single file replaces 6-8 static weight files; smaller total payload |

### Preloading Critical Fonts

```html
<link rel="preload" href="/fonts/MonaspaceNeonVarVF[wght,wdth,slnt].woff2"
      as="font" type="font/woff2" crossorigin>
```

Add `crossorigin` even for same-origin fonts — browsers require it for font preloads.

---

## 3. Font Pairing Guidelines

Build a **Display + Body + Mono** triad. Contrast between classifications prevents visual confusion while creating hierarchy.

### Pairing Principles

- Pair fonts from **different** classifications (serif display + sans body, or vice versa)
- Never pair two fonts from the same classification (two sans, two serifs)
- Match x-height and visual weight between display and body fonts
- Limit to 3 families maximum per project

### Recommended Pairings

| Display | Body | Mono | Aesthetic |
|---------|------|------|-----------|
| Fraunces | Source Sans 3 | Monaspace Neon | Editorial, warm |
| Playfair Display | Inter (body only) | Monaspace Krypton | Classic, structured |
| Space Grotesk | DM Sans | Monaspace Argon | Technical, clean |
| Syne | Outfit | Monaspace Radon | Playful, creative |
| Instrument Serif | Geist Sans | Monaspace Xenon | Modern editorial |
| Cabinet Grotesk | Literata | Monaspace Neon | Bold, literary |

### Tailwind v4 Font Stack

```css
@theme {
  --font-display: "Fraunces", "Georgia", serif;
  --font-body: "Source Sans 3", "Helvetica Neue", sans-serif;
  --font-mono: "Monaspace Neon", "Courier New", monospace;
}
```

---

## 4. Fluid Type Scale

Use `clamp(min, preferred, max)` for type that scales smoothly between viewport sizes without breakpoints.

```css
@theme {
  --text-xs:  clamp(0.75rem,  0.25vw + 0.7rem,   0.875rem);
  --text-sm:  clamp(0.875rem, 0.35vw + 0.8rem,    1rem);
  --text-base: clamp(1rem,    0.5vw  + 0.875rem,  1.125rem);
  --text-lg:  clamp(1.125rem, 0.75vw + 1rem,      1.25rem);
  --text-xl:  clamp(1.25rem,  1vw    + 1.125rem,  1.5rem);
  --text-2xl: clamp(1.5rem,   1.5vw  + 1.25rem,   2rem);
  --text-3xl: clamp(2rem,     2vw    + 1.5rem,     2.5rem);
  --text-4xl: clamp(2.5rem,   3vw    + 2rem,       3.5rem);
}
```

### Formula Breakdown

```
clamp(MINIMUM, PREFERRED, MAXIMUM)
       |        |          |
       |        |          +-- Cap: largest the text ever gets
       |        +------------- Growth: viewport-relative value + base offset
       +---------------------- Floor: smallest the text ever gets
```

- **Minimum** — readable at 320px viewport
- **Preferred** — `[rate]vw + [base]rem` where rate controls growth speed
- **Maximum** — comfortable at 1440px+ viewport
- Higher `vw` coefficient = more dramatic scaling between mobile and desktop

---

## 5. Variable Font Performance

### Size Comparison

| Approach | Files | Total size (typical) |
|----------|-------|---------------------|
| 6 static WOFF2 weights | 6 | ~180 KB |
| 1 variable WOFF2 | 1 | ~110 KB |

Variable fonts reduce HTTP requests AND total bytes.

### Subsetting with `unicode-range`

Serve only the glyphs needed per language block:

```css
/* Latin subset */
@font-face {
  font-family: "Monaspace Neon";
  src: url("/fonts/MonaspaceNeon-latin.woff2") format("woff2");
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+2000-206F;
  font-display: swap;
}
```

The browser downloads only the subsets containing glyphs present on the page.

### Fallback Font Metric Matching

Prevent layout shift (CLS) by aligning fallback metrics to the web font:

```css
@font-face {
  font-family: "Monaspace Neon Fallback";
  src: local("Courier New");
  size-adjust: 105%;
  ascent-override: 95%;
  descent-override: 22%;
  line-gap-override: 0%;
}

@theme {
  --font-mono: "Monaspace Neon", "Monaspace Neon Fallback", monospace;
}
```

Tune `size-adjust`, `ascent-override`, `descent-override` until the fallback closely matches the web font dimensions.

---

## 6. Anti-Patterns

| Anti-pattern | Problem | Fix |
|-------------|---------|-----|
| Inter / Roboto / Arial as primary font | Generic, forgettable, zero personality | Select a distinctive display + body pairing |
| Loading 6+ static font weights | Bloated payload, slow LCP | Use a single variable font file |
| Missing `font-display` declaration | Invisible text during font load (FOIT) | Add `font-display: swap` to every `@font-face` |
| Serving TTF/OTF on the web | 2--3x larger than WOFF2 | Convert to WOFF2, drop legacy formats |
| No fallback metric matching | Layout shift when web font loads (CLS) | Use `size-adjust` and `ascent-override` on fallback |
| Hardcoded `px` type sizes | No fluid scaling, poor accessibility | Use `clamp()` with `rem` units |
| Skipping `crossorigin` on font preload | Browser ignores the preload, double-fetches | Always add `crossorigin` attribute |
| Using `@import url()` for Google Fonts | Render-blocking, extra DNS lookup | Self-host with `@font-face` and WOFF2 |
