# Motion Language

Motion is interaction design. Use it to explain change, guide attention, or
confirm feedback.

## Motion Gate

Before adding animation, answer:

1. What state changed?
2. Where did the element come from or go?
3. How often will this animation run?
4. Can the user interrupt it?
5. What happens under `prefers-reduced-motion: reduce`?
6. Does it run on compositor-friendly properties?

## Timing Defaults

| Context | Guidance |
| --- | --- |
| Hover/focus feedback | Fast, subtle, under 200ms |
| Small state change | 150-250ms |
| Modal/sheet entrance | 180-300ms with clear origin |
| Page/section entrance | Use sparingly; avoid blocking content |
| Repeated dashboard interactions | Prefer no animation or feedback-only |

## Static Review Signals

- Flag `transition: all`; transition named properties.
- Flag infinite animation near controls or dense workflows.
- Flag layout-property animations; prefer transform/opacity.
- Flag `will-change` used broadly or permanently.
- Require reduced-motion alternatives for keyframes, view transitions, and long
  transitions.
- Use tabular numbers for changing numeric values.

## Decision Matrix

| Context | Keep Motion When | Delete Or Reduce When |
| --- | --- | --- |
| Navigation and panels | It explains origin, destination, or hierarchy. | It delays repeated work or enters from a misleading origin. |
| Data updates | It helps users notice what changed. | It makes numbers harder to compare or causes layout shift. |
| Empty/loading/error states | It communicates progress or completion. | It loops without new information. |
| Brand/marketing | It supports the product story. | It becomes the only differentiator or hurts readability. |
| AI/tool progress | It clarifies state and interruptibility. | It hides tool state behind decorative loading. |

## Reduced Motion Proof

- Search for `prefers-reduced-motion`, `motion-reduce`, or library-specific
  reduced-motion hooks when motion exists.
- In rendered proof, emulate reduced motion when tooling supports it and confirm
  essential content still appears.
- Replace large transitions with static equivalents, shorter durations, or
  opacity-free state changes for reduced-motion users.
- Do not remove feedback entirely when it is needed for state comprehension;
  provide a non-motion cue.

## Failure Modes

- Animating layout properties causes jank and text overlap.
- Long entrances make dashboards feel slower than the data pipeline.
- Hover-only motion hides affordances from touch and keyboard users.
- Repeated shimmer or pulse animations compete with task content.
- Motion continues after navigation, modal close, or component unmount.

## Audit Output

Use a compact table:

| Element | Current Motion | Issue | Recommendation |
| --- | --- | --- | --- |
| Sheet | slides from wrong edge | origin conflicts with trigger | enter from trigger side |
