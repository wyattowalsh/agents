# Three.js And Immersive Interfaces

Use this only when the request explicitly needs 3D, WebGL, immersive canvas, or
interactive visual simulation.

## First Principles

- Use current official Three.js docs for API details before relying on bundled
  snippets.
- Keep the 3D scene full-bleed or meaningfully integrated; do not hide it in a
  decorative card unless the product layout requires a framed viewport.
- Provide non-3D fallback content when the canvas carries essential information.
- Respect performance, reduced motion, keyboard access, and touch behavior.

## Implementation Checklist

- Renderer size follows the container and updates on resize.
- Pixel ratio is capped.
- Camera framing works on desktop and mobile.
- Materials and lights are visible against the background.
- Assets have loading and error states.
- Animation loop stops or throttles when not needed.
- Interaction is discoverable without instructional text in the canvas.

## Verification

- Screenshot desktop and mobile.
- Run a nonblank canvas/pixel check when possible.
- Confirm there are no overlapping overlays or invisible controls.
- Note FPS or obvious jank if the scene is animation-heavy.

## Framing And Camera Checks

- The primary object should be identifiable in the first viewport, not hidden by
  UI chrome or clipped by the camera.
- Use aspect-ratio-aware camera framing and resize handling; do not tune the
  camera only for the developer viewport.
- Keep controls discoverable and bounded. Avoid scroll hijacking unless the
  scene is the primary experience and the interaction is reversible.
- Treat loading, WebGL unsupported, and texture/model failure as designed
  states with readable fallback content.

## Performance Smells

- Unbounded pixel ratio on high-DPI displays.
- Permanent animation loops when the scene is offscreen or static.
- Large textures or models loaded before first meaningful UI.
- Missing disposal for geometries, materials, render targets, textures, and
  controls when scenes unmount.
- Canvas overlays that block forms, focus, or links.

## Handoffs

`/design` owns scene framing, interaction, accessibility, visual fit, and proof.
Route deep shader optimization, engine architecture, asset-pipeline work, or
non-UI WebGL profiling to a dedicated performance/graphics workflow.
