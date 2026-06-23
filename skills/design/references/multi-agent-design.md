# Multi-Agent Design

Use this reference when the UI request is too broad for one linear pass: whole
apps, many screens, design-system upgrades, multi-surface audits, migrations,
AI workflow suites, 3D/canvas experiences, or any prompt that asks for many
subagents.

## Principles

- Maximize read-only fanout before editing. Exploration, inventory, screenshots,
  source reading, heuristic review, and proof planning are naturally parallel.
- Split by ownership boundary. One subagent owns one route, component family,
  concern, or proof target.
- Keep same-file writes sequential. Shared tokens, theme files, root layout,
  package manifests, generated docs, and central primitives need one writer or a
  merge captain.
- Prefer small, typed deliverables over broad commentary. Every lane reports
  evidence, files, risks, recommended edits, and validation commands.
- Merge through one captain. The captain preserves the design thesis, prevents
  duplicate fixes, resolves contradictory taste calls, and owns final proof.

## Team Topology

Start with these lanes, then add one subagent per significant surface or concern:

| Lane | Mission | Write Policy |
| --- | --- | --- |
| Merge Captain | Scope, thesis, file locks, synthesis, final proof | Main thread only |
| Repo Cartographer | Routes, component tree, tokens, dependencies, generated surfaces | Read-only |
| Product/UX | Audience, jobs, flows, IA, density, hierarchy | Read-only or copy-only |
| Design System | Tokens, typography, icons, primitives, shadcn/Radix use | Shared-file lock |
| Surface Scouts | One route/screen per subagent; capture state and issues | Read-only first |
| Component Scouts | One component family per subagent | Read-only first |
| Accessibility | Labels, focus, keyboard, contrast, semantics, reduced motion | Review or scoped fixes |
| Responsive/Text | Mobile, safe areas, long content, localization, overflow | Review or scoped fixes |
| Motion | Purpose, duration, origin, interruptibility, performance | Review or scoped fixes |
| AI UX | Wayfinding, inputs, tuners, governors, provenance, recovery | Review or scoped fixes |
| 3D/Canvas | Scene setup, framing, pixel ratio, resize, nonblank proof | Review or scoped fixes |
| Visual QA | Screenshots, viewport matrix, overlap, clipping, blank states | Read-only proof |
| Implementation | One locked file group per subagent after merge plan | Writes only assigned files |
| Verification | Tests, scanner, build, browser checks, screenshot evidence | Mostly read-only |
| Docs/Handoff | README/catalog/research/handoff updates when public surfaces change | Sequential after source |

For very large work, multiply Surface Scouts and Implementation lanes by route
or feature area. A dozen narrow scouts is better than two broad generalists.

## Wave Plan

| Wave | Goal | Parallelization |
| --- | --- | --- |
| 0. Preflight | Branch, dirty state, instructions, collision checks, app commands | One captain |
| 1. Inventory | Routes, components, tokens, dependencies, screenshots, current bugs | Maximum read-only fanout |
| 2. Diagnosis | UX, accessibility, motion, responsive, AI trust, content, performance | One subagent per concern |
| 3. Synthesis | Thesis, target state, file locks, task graph, stop rules | Captain plus lane leads |
| 4. Edits | Implement by locked file group or route | Parallel only when files do not overlap |
| 5. Proof | Build, tests, scanner, screenshots, viewport matrix, reduced motion | Parallel proof lanes |
| 6. Handoff | Docs, generated surfaces, final stale-reference checks | Sequential |

## Hyperfine Task Graph Template

Use short task ids and explicit dependencies. Adapt the scale to the repo.

| ID | Owner | Type | Depends | Output |
| --- | --- | --- | --- | --- |
| D00 | Captain | Verify | none | Branch, dirty state, instructions, stop rules |
| D01 | Cartographer | Read | D00 | Route and component map |
| D02 | Cartographer | Read | D00 | Token/theme/design-system map |
| D03 | Surface Scout N | Read | D00 | Screen inventory and screenshot/proof needs |
| D04 | UX | Read | D00 | Audience, job, flow, IA, density notes |
| D05 | Accessibility | Read | D00 | Focus, semantics, labels, contrast risks |
| D06 | Responsive/Text | Read | D00 | Overflow, long content, viewport risks |
| D07 | Motion | Read | D00 | Animation inventory and reduced-motion gaps |
| D08 | AI UX | Read | D00 | Trust, provenance, tuners, governor gaps |
| D09 | 3D/Canvas | Read | D00 | Scene/canvas proof risks |
| D10 | Captain | Merge | D01-D09 | Design thesis and locked edit graph |
| D11 | Impl A | Write | D10 | Route or component group A |
| D12 | Impl B | Write | D10 | Route or component group B |
| D13 | Impl C | Write | D10 | Token or primitive changes under lock |
| D14 | Visual QA | Verify | D11-D13 | Screenshot and viewport matrix |
| D15 | Accessibility | Verify | D11-D13 | Keyboard/focus/label verification |
| D16 | Captain | Merge | D14-D15 | Final polish decisions |
| D17 | Verification | Verify | D16 | Tests, build, scanner, stale checks |
| D18 | Docs | Write | D17 | Handoff docs and generated surfaces |

## Subagent Prompt Contract

Give each subagent this shape:

```text
Mission:
Scope:
Owned files or read-only paths:
Do not edit:
Evidence to collect:
Output format:
- Findings with file/path anchors
- Proposed edits and affected files
- Validation/proof needed
- Blockers and uncertainty
```

## Merge Rules

- The captain owns final decisions when lanes disagree.
- Preserve local design-system conventions unless multiple lanes produce
  evidence that they block the product goal.
- If two lanes want the same file, stop parallel writes and create one merged
  patch plan.
- Do not accept visual polish that breaks accessibility, content resilience, or
  rendered proof.
- Do not call the work complete until the proof lanes cover desktop, mobile,
  important UI states, and any canvas/motion-specific checks.

## Stop Rules

- Stop before live installs, registry writes, Figma/Stitch/MCP writes, or
  credentialed tools unless the user explicitly authorizes them.
- Stop before adding compatibility aliases or redirects unless public-consumer
  evidence and maintainer approval exist.
- Stop if file locks conflict, if rendered proof cannot be obtained for a
  high-risk visual change, or if subagents return contradictory source evidence
  that the captain cannot resolve.
