---
name: chrome-devtools-debug-optimize-lcp
description: 'Use when auditing or optimizing Largest Contentful Paint with Chrome DevTools MCP: traces, element discovery, waterfalls, render blocking, and fix verification. NOT for non-LCP performance work, generic browser automation, or SEO copy advice.'
license: Apache-2.0
compatibility: 'Requires Chrome DevTools MCP 0.23.0 or compatible tools with performance trace and insight support.'
metadata:
  author: Google LLC
  version: 0.23.0
---

# Chrome DevTools LCP Debugging

Use Chrome DevTools MCP to find the actual LCP element, identify which LCP subpart is slow, and verify that fixes reduce the bottleneck.

## Dispatch

| $ARGUMENTS | Action |
| --- | --- |
| Empty | Ask for the target URL/page and whether reload is safe |
| Slow page load or Core Web Vitals | Record a trace, analyze LCP insights, then inspect element and network evidence |
| Hero image or main content slow | Identify LCP element, confirm resource discovery, priority, and load timing |
| TTFB concern | Analyze `DocumentLatency` and request timing before frontend changes |
| Render-blocking concern | Analyze `RenderBlocking`, scripts, CSS, and main-thread evidence |
| Fix verification | Re-run the trace under the same conditions and compare subpart timings |

## LCP Targets

- Good: 2.5 seconds or less.
- Needs improvement: 2.5 to 4.0 seconds.
- Poor: greater than 4.0 seconds.

## Debugging Workflow

1. Navigate to the page and ensure reload is acceptable.
2. Run `performance_start_trace` with `reload: true` and `autoStop: true`.
3. Record the available insight set IDs from the trace output.
4. Run `performance_analyze_insight` for `LCPBreakdown`, then `DocumentLatency`, `RenderBlocking`, or `LCPDiscovery` as indicated.
5. Use `evaluate_script` with `references/lcp-snippets.md` to identify the LCP element and common DOM issues.
6. Use `list_network_requests` and `get_network_request` to inspect the LCP resource timing and priority.
7. Recommend the smallest fix that targets the slowest subpart.
8. Re-run the same trace to verify improvement.

## Optimization Order

1. Eliminate resource load delay: make the LCP resource discoverable in initial HTML and avoid lazy-loading it.
2. Eliminate element render delay: reduce render-blocking CSS/JS and main-thread work.
3. Reduce resource load duration: optimize bytes, CDN, caching, and priority.
4. Reduce TTFB: remove redirects, cache HTML, and optimize server response time.

## Privacy Note

Chrome DevTools MCP performance tooling can use CrUX-related behavior depending on server flags. Respect repo MCP hardening and do not enable extra telemetry or CrUX submission without explicit user intent.

## Reference File Index

| File | Content | Read When |
| --- | --- | --- |
| `references/elements-and-size.md` | Which elements count for LCP and how size is determined | The LCP element is ambiguous |
| `references/lcp-breakdown.md` | Four LCP subparts and optimization implications | Interpreting trace insights |
| `references/lcp-snippets.md` | Scripts for LCP element discovery and DOM issue checks | Trace evidence needs DOM confirmation |
| `references/lcp-fixes.md` | Fixes by LCP subpart | Recommending changes |
| `references/provenance.md` | Upstream source, commit, license, and adaptation notes | Before modifying this skill or auditing provenance |

## Critical Rules

1. Identify the slow LCP subpart before recommending a fix.
2. Do not optimize bytes before checking resource load delay and render delay.
3. Keep trace files out of version control.
4. Use the same network and CPU conditions when comparing before and after traces.
5. Do not enable extra field-data or telemetry behavior beyond repo MCP policy.

## Canonical Vocabulary

| Term | Meaning |
| --- | --- |
| LCP | Largest Contentful Paint, the render time of the largest visible content element |
| LCP subpart | TTFB, resource load delay, resource load duration, or element render delay |
| Waterfall | Network request timing evidence for the LCP resource |
| Verification trace | A second trace captured under the same conditions after a fix |

## Validation Contract

Before declaring skill changes complete, run `uv run wagents validate`, `uv run python skills/skill-creator/scripts/audit.py skills/chrome-devtools-debug-optimize-lcp`, and `uv run wagents package chrome-devtools-debug-optimize-lcp --dry-run`.
