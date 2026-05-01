# Elements and Size for LCP

## Elements Considered

- `<img>` elements.
- `<image>` elements inside SVG.
- `<video>` poster images or first frames.
- Elements with CSS background images.
- Block-level elements containing text nodes or inline text children.

## Common Exclusions

- Elements with opacity 0.
- Elements covering the full viewport when treated as background.
- Placeholder or low-entropy images.

## Size Rules

- Visible area within the viewport is what usually counts.
- Image elements use the smaller of visible size and intrinsic size.
- Text uses the smallest rectangle containing all text nodes.
- Margin, padding, and borders are excluded.
