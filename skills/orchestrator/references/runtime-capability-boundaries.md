# Runtime Capability Boundaries

Use this reference when tier choice depends on the active runtime or tool surface.

## Tier Selection Reminder

- Highest applicable tier wins.
- Do not choose a lower tier just to reduce cost or perceived overhead.
- Exactly one action stays single-session.

## Typical Boundaries

### Single Session

Use when:

- there is exactly one action
- the work is tightly serialized
- same-file overlap prevents safe parallelism

### Subagent Wave

Use when:

- there are 2+ independent actions
- the work stays in one domain
- the agents do not need to coordinate with one another
- context pressure is low

### Team + Nested Waves

Use when:

- the work spans multiple ownership lanes
- coordination is needed across domains
- verbose work should be delegated inside each ownership lane
- context pressure makes a flat wave fragile

## Capability Constraints to Name Explicitly

- same-file edit overlap
- missing team support in the runtime
- read-only plan mode limits
- inability to resume certain agent types
- environment-specific model or permission limits

These constraints can change the mechanism, but they do not justify ignoring the decomposition step.

## Near-Miss Examples

- Two independent read-only audits -> subagent wave is enough.
- Backend, frontend, and tests with shared checkpoints -> team + nested waves.
- One big refactor in a single file -> single session despite multiple conceptual steps.
- Explore, then implement, then verify -> multi-wave pipeline, often with nested waves inside implementation.

## Reporting Expectations

When tier choice is discussed:

- name the candidate tiers
- explain why the chosen tier is the highest applicable one
- mention the boundary that rules out the lower or higher alternatives
