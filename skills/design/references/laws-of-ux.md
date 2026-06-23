# UX Heuristics

Use these as practical checks. They are heuristics, not proof.

## Checks

| Heuristic | Interface Check |
| --- | --- |
| Fitts | Primary targets are easy to acquire; touch targets are large enough |
| Hick | Choices are reduced or grouped when decision cost is high |
| Jakob | Familiar controls are used for common tasks |
| Miller / chunking | Long content is grouped into readable chunks |
| Proximity | Related labels, inputs, actions, and errors are visually grouped |
| Common region | Cards/sections group only genuinely related content |
| Similarity | Repeated controls behave consistently |
| Postel | Inputs tolerate common formatting and recover cleanly |
| Doherty | Slow operations show useful progress or skeleton state |
| Peak-end | Completion and error moments are clear and calm |

## Common Fixes

- Move destructive actions away from primary flows and require confirmation when
  data loss is possible.
- Place errors next to controls, not only at page top.
- Use progressive disclosure for advanced settings.
- Keep repeated lists comparable: same columns, same units, same sorting, same
  empty state pattern.
- Use loading states that preserve layout rather than shifting content.

## Review Actions

| Symptom | Heuristic Lens | Action |
| --- | --- | --- |
| Users compare many unlike options | Hick/Fitts/Miller | Group, filter, rank, or defer advanced choices. |
| Related labels, controls, and results are far apart | Proximity/Common region | Move them into one local region or strengthen grouping. |
| A workflow feels slow despite acceptable runtime | Doherty/feedback | Add immediate acknowledgement, stable skeletons, and clear pending state. |
| Users miss a destructive or high-risk state | Salience/Tesler | Increase hierarchy and copy clarity, not decoration alone. |
| Expert controls crowd first-use tasks | Progressive disclosure | Hide advanced controls behind tabs, details, or mode switches with remembered state. |
| Long text breaks tiles, buttons, tables, or badge rows | Content resilience | Add wrapping, min/max constraints, overflow affordances, or responsive reflow. |

## Proof Expectations

- Verify target size and spacing at mobile and desktop viewports for primary
  controls.
- Check grouped controls through keyboard traversal, not just visual proximity.
- Test long labels, translated strings, empty states, and dense data.
- For badge/status rows, confirm wrapping and meaning do not rely only on color.

## Anti-Patterns

- More than one primary CTA in the same local decision area.
- Dense controls without grouping or labels.
- Icon-only actions without tooltips and accessible names.
- Toast-only confirmation for critical state changes.
- Infinite animation on controls used repeatedly or under time pressure.
