# Design Briefs

Use this when a request needs direction before UI code. Keep the brief short
enough to guide decisions, not large enough to become a design doc.

## Design Read

Record these facts before choosing styling:

| Field | What To Capture |
| --- | --- |
| User | Role, context, frequency, expertise, accessibility needs |
| Job | The task the interface must make easier |
| Surface | Product tool, dashboard, form, marketing, editorial, AI, game, 3D |
| Register | Restrained, technical, expressive, playful, premium, civic, clinical |
| Density | Sparse, normal, dense, data-first |
| Motion | None, feedback-only, guided, expressive |
| System | Existing components, tokens, typography, icon set, content conventions |

## Domain Defaults

- Operational tools: dense but calm; prioritize scan speed, comparison, stable
  controls, keyboard access, and predictable navigation.
- Dashboards: put the decision metric first; keep labels short; use tabular
  numbers; explain filters, empty states, and freshness.
- Forms: group by user mental model; minimize choice; label every field; make
  errors recoverable near the control.
- Landing pages: one clear offer, one primary action per section, real proof,
  strong first-viewport product/brand signal.
- Editorial pages: use type hierarchy, measure, rhythm, and image captions as
  the main experience.
- AI interfaces: expose state, control, provenance, uncertainty, and undo paths.

## Thesis Template

```text
This is a [surface] for [user] trying to [job].
The design should feel [register] because [reason].
Use [existing system] as the base.
Set density to [level], motion to [level], and visual variance to [level].
The signature design move is [one memorable but useful choice].
Rendered proof must cover [viewports/states].
```

## Do Not

- Start from a favorite aesthetic before reading the product.
- Treat marketing, dashboards, and AI workflows as the same layout problem.
- Replace a working local design system with a new one because the prompt is
  visually ambitious.
- Use placeholder copy to hide weak hierarchy. Real content changes layout.
