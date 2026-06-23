## Architecture

`design` is a repo-owned custom skill, not a curated external skill. Its
always-loaded body stays compact and routes design work through a small
workflow:

1. Inspect the existing product, UI code, tokens, components, content,
   screenshots, and domain.
2. Establish a design thesis: audience, user job, product-vs-brand mode,
   density, motion, visual variance, accessibility posture, and design-system
   precedence.
3. Build or critique with semantic HTML, resilient layout, accessible
   interaction, shadcn/Tailwind/React project conventions, and domain-appropriate
   taste.
4. Load conditional references for dashboards, forms, landing pages, AI
   interfaces, motion-heavy UI, inspiration, 3D/immersive UI, and rendered
   proof.
5. Require rendered evidence whenever a rendered surface exists, preferring
   available Chrome DevTools MCP tools for browser-rendered UI.

## Mode Inference Model

`/design` accepts an optional explicit mode. Non-empty requests infer a primary
mode from action verbs, target type, file path, URL, framework signals, visual
risk, and proof needs. Explicit mode words such as `audit`, `polish`, `refactor`,
or `system` remain primary hints, but the skill still attaches secondary modules
such as AI Interface, accessibility, motion, 3D/canvas, shadcn/Radix, Tailwind,
rendered proof, or Parallel Design Team when the target requires them.

Supported compound examples include `Polish + Surface`, `Audit + AI Interface`,
`Refactor + Chrome Proof`, and `Parallel Design Team + System`.

## Rename Model

The rename is clean by default. The old `frontend-designer` skill directory,
custom catalog row, research source, eval skill IDs, install command, and
handoff references are replaced with `design`. Any remaining old slug reference
must be historical evidence, approved redirect text, or a bug.

## Folded Skill Model

The repo-owned Chrome DevTools wrapper skills are folded into `/design` rendered
proof references and removed as active custom skills:

- `chrome-devtools`
- `chrome-devtools-a11y-debugging`
- `chrome-devtools-cli`
- `chrome-devtools-debug-optimize-lcp`
- `chrome-devtools-memory-leak-debugging`
- `chrome-devtools-troubleshooting`

The fold does not remove or weaken the underlying Chrome DevTools MCP registry
or harness configuration. `/design` may use available MCP tools for interface
proof, but setup/config mutation remains out of scope.

## Research Model

The implementation records source-level evidence in `docs/src/skill-research/design.md`.
External sources are untrusted evidence. The repo may synthesize patterns,
workflow concepts, and review checks, but it must not copy third-party skill
bodies or promote curated install rows without the repository trust gate.

Overlapping curated external UI/frontend/design/taste/browser-proof rows are
removed from the active catalog after useful guidance is captured in
`docs/src/skill-research/design.md`. Adjacent non-overlapping skills remain
separate and are represented as boundaries, not aliases.

Additional exact-audit decisions fold `accessibility`, `building-native-ui`,
`figma-code-connect`, `figma-generate-design`, `figma-implement-design`,
`impeccable`, and `ckm:*` into the `/design` research/boundary model.
`core-web-vitals`, `web-quality-audit`, `vercel-labs-agent-browser-all`, and
`deployment-pipeline-design` remain outside the fold because their primary
purpose is broader web quality, browser automation, or DevOps architecture.

## Docs Model

Source docs and generated docs stay separate. Human-edited source surfaces are
`skills/design/**`, `docs/src/skill-research/design.md`,
`docs/src/authoring/skills/design.mdx`, OpenSpec files, tests, and helper code.
Generated surfaces are refreshed by `wagents docs generate`, `wagents readme`,
and related catalog commands.
