---
name: chrome-devtools-memory-leak-debugging
description: 'Use when auditing JavaScript, browser, or Node.js memory leaks with Chrome DevTools MCP heap snapshots, repeated interactions, memlab, and retainer traces. NOT for generic profiling, CPU regressions, or reading raw heap snapshots.'
license: Apache-2.0
compatibility: 'Requires Chrome DevTools MCP 0.23.0 or compatible `take_memory_snapshot` support; memlab is optional and must be invoked with user-approved commands.'
metadata:
  author: Google LLC
  version: 0.23.0
---

# Chrome DevTools Memory Leak Debugging

Use Chrome DevTools MCP to reproduce memory growth, capture heap snapshots, and analyze leaks without loading raw heap artifacts into the conversation.

## Dispatch

| $ARGUMENTS | Action |
| --- | --- |
| Empty | Ask for the leak symptom, target URL/app, and reproduction steps |
| Browser memory leak | Capture baseline, target, and final snapshots around repeated interactions |
| Node.js memory leak | Prefer runtime-native heap snapshots or memlab-compatible artifacts, then analyze summaries |
| Raw `.heapsnapshot` request | Refuse to read it directly; use memlab or a bounded analyzer command |
| Detached DOM nodes | Treat as suspect, not automatically wrong; ask before changing intentional caches |
| Fix verification | Repeat the same interaction loop and compare snapshots or memlab output |

## Core Principles

- Never read raw `.heapsnapshot` files directly; they are too large for context and easy to mishandle.
- Isolate whether the leak is client-side browser state, server-side Node.js, or test harness state.
- Amplify suspected leaks by repeating the same user interaction loop.
- Use bounded analysis output, not raw snapshot contents.

## Browser Workflow

1. Navigate to the target page and reach a stable baseline state.
2. Capture a baseline heap snapshot with `take_memory_snapshot` to a file path outside version control.
3. Perform the suspected interaction repeatedly, usually 10 times.
4. Capture the target heap snapshot.
5. Revert the interaction if possible, such as closing a modal or navigating away.
6. Capture the final heap snapshot.
7. Analyze snapshots with memlab or another bounded tool.
8. Map retainer traces back to source code and propose the smallest fix.
9. Verify by repeating the same workflow after the fix.

## Common Leak Patterns

- Event listeners not removed from long-lived objects.
- Detached DOM nodes retained by variables, caches, closures, or listeners.
- Accidental globals or `window` attachments.
- Closures retaining large objects after they are no longer needed.
- Unbounded arrays, maps, or application caches.

## Reference File Index

| File | Content | Read When |
| --- | --- | --- |
| `references/common-leaks.md` | Common browser and JavaScript leak patterns | Mapping retainer traces to likely fixes |
| `references/memlab.md` | Bounded heap snapshot analysis commands | Snapshot files are available |
| `references/provenance.md` | Upstream source, commit, license, and adaptation notes | Before modifying this skill or auditing provenance |

## Critical Rules

1. Never read raw `.heapsnapshot` files into context.
2. Capture baseline, target, and final snapshots when possible.
3. Repeat suspected interactions to amplify leaks before analysis.
4. Treat detached DOM nodes as suspect until the user confirms they are not intentional caches.
5. Verify fixes by repeating the same snapshot workflow.

## Canonical Vocabulary

| Term | Meaning |
| --- | --- |
| Heap snapshot | Browser or Node.js memory graph saved as an external artifact |
| Baseline snapshot | Snapshot before the suspected leak action |
| Target snapshot | Snapshot after repeating the suspected leak action |
| Final snapshot | Snapshot after reverting the action when possible |
| Retainer trace | Analysis output showing why an object remains reachable |

## Validation Contract

Before declaring skill changes complete, run `uv run wagents validate`, `uv run python skills/skill-creator/scripts/audit.py skills/chrome-devtools-memory-leak-debugging`, and `uv run wagents package chrome-devtools-memory-leak-debugging --dry-run`.
