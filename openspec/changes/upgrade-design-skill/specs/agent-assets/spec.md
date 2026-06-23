# Agent Assets Delta

## MODIFIED Requirements

### Requirement: Asset Formats Stay Canonical

The repository SHALL keep skill, agent, MCP, instruction, hook, and bundle metadata formats documented in `AGENTS.md` and validated by `wagents` commands.

#### Scenario: Renaming the frontend design skill to design

- **WHEN** the repo-owned frontend design skill is renamed
- **THEN** `skills/design/SKILL.md` SHALL use frontmatter `name: design`
- **AND** no `skills/frontend-designer/` custom skill directory SHALL remain
- **AND** `uv run wagents validate --format json` SHALL validate the renamed skill before completion.

#### Scenario: Keeping the design skill compact

- **WHEN** the `design` skill incorporates frontend, UI, UX, motion, AI interface, accessibility, and taste guidance
- **THEN** `SKILL.md` SHALL remain a compact dispatch and workflow contract
- **AND** deep guidance SHALL live in conditional reference files under `skills/design/references/`.

#### Scenario: Inferring optional design modes

- **WHEN** `/design` receives non-empty natural-language arguments
- **THEN** the skill SHALL infer one primary mode by default instead of requiring a mode token
- **AND** an explicit first mode word SHALL be treated as the primary hint
- **AND** the skill SHALL attach relevant secondary modules for AI trust, accessibility, motion, 3D/canvas, shadcn/Radix, Tailwind, rendered proof, or parallel design-team work.

#### Scenario: Integrating Chrome DevTools proof without deleting operational skills

- **WHEN** Chrome DevTools-backed browser proof is part of the `design` skill
- **THEN** `skills/design/references/rendered-proof.md` SHALL document page proof, accessibility tree/focus proof, LCP/hero proof, memory/performance-smell checks, troubleshooting fallback, and CLI fallback
- **AND** repo-owned custom skill directories SHALL remain for `chrome-devtools`, `chrome-devtools-a11y-debugging`, `chrome-devtools-cli`, `chrome-devtools-debug-optimize-lcp`, `chrome-devtools-memory-leak-debugging`, and `chrome-devtools-troubleshooting`
- **AND** `/design` SHALL route non-design browser debugging, MCP setup repair, generic browser automation, deep LCP/performance profiling, CLI automation, and memory-leak investigations outside the design skill.
