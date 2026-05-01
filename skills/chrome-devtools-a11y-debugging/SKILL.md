---
name: chrome-devtools-a11y-debugging
description: 'Use when auditing web accessibility through Chrome DevTools MCP: semantic HTML, ARIA labels, focus order, keyboard navigation, tap targets, contrast, and Lighthouse failures. NOT for generic page debugging, non-browser policy writing, or performance optimization.'
license: Apache-2.0
compatibility: 'Requires Chrome DevTools MCP 0.23.0 or compatible tools with `lighthouse_audit`, `take_snapshot`, `press_key`, `evaluate_script`, and console issue access.'
metadata:
  author: Google LLC
  version: 0.23.0
---

# Chrome DevTools Accessibility Debugging

Use Chrome DevTools MCP to validate what assistive technologies can see and how keyboard users move through the page. The accessibility tree is the primary source of truth; screenshots are supporting evidence.

## Dispatch

| $ARGUMENTS | Action |
| --- | --- |
| Empty | Ask for the URL/page and target accessibility concern |
| Accessibility audit | Run Lighthouse accessibility, inspect failures, then validate with snapshot and focused checks |
| Missing label or form issue | Use snapshot names first; use the orphan-input snippet for DOM confirmation |
| Keyboard/focus issue | Step through with `press_key`, taking snapshots after each movement |
| Tap target or contrast issue | Use snippets from `references/a11y-snippets.md` and confirm visually when needed |
| Modal/menu/dialog issue | Verify focus enters, remains trapped where expected, and returns after close |

## Core Concepts

- The accessibility tree differs from the DOM. Elements hidden visually may still be exposed, and visible elements may be hidden from assistive tech.
- `take_snapshot` shows roles, names, heading levels, and focused elements.
- Lighthouse finds broad classes of failures; snapshots and focused checks confirm user impact.

## Workflow

1. Navigate to the target page and wait for the relevant UI state.
2. Run `lighthouse_audit` in `navigation` mode for a baseline when page reload is safe.
3. Inspect browser issues with `list_console_messages` using `types: ["issue"]` and preserved messages.
4. Capture `take_snapshot` and check headings, landmarks, names, and order.
5. Test keyboard navigation with `press_key` and fresh snapshots.
6. Use snippets only for data missing from the accessibility tree, such as tap target dimensions or manual contrast estimates.
7. Report failures with selector or `uid`, observed behavior, expected behavior, and remediation.

## Large Report Handling

If Lighthouse writes a report, do not load the entire JSON into context. Extract failed audits with a targeted parser, for example:

```bash
node -e "const r=require('./report.json'); Object.values(r.audits).filter(a=>a.score!==null && a.score<1).forEach(a=>console.log(JSON.stringify({id:a.id,title:a.title,items:a.details?.items})))"
```

## Reference File Index

| File | Content | Read When |
| --- | --- | --- |
| `references/a11y-snippets.md` | DOM snippets for labels, tap targets, contrast, and page-level checks | Snapshot and Lighthouse evidence are insufficient |
| `references/provenance.md` | Upstream source, commit, license, and adaptation notes | Before modifying this skill or auditing provenance |

## Critical Rules

1. Treat the accessibility tree as primary evidence for semantics and focus.
2. Use screenshots only as supporting visual evidence.
3. Do not load entire Lighthouse reports into context; extract failed audits.
4. Verify keyboard navigation with repeated key movement and fresh snapshots.
5. Report accessibility findings with observed behavior, expected behavior, and remediation.

## Canonical Vocabulary

| Term | Meaning |
| --- | --- |
| Accessibility tree | Snapshot representation exposed to assistive technologies |
| Accessible name | Text label announced for an interactive or semantic element |
| Focus order | Keyboard traversal order observed through repeated snapshots |
| Lighthouse failure | Accessibility audit item with a failing score and remediation guidance |

## Validation Contract

Before declaring skill changes complete, run `uv run wagents validate`, `uv run python skills/skill-creator/scripts/audit.py skills/chrome-devtools-a11y-debugging`, and `uv run wagents package chrome-devtools-a11y-debugging --dry-run`.
