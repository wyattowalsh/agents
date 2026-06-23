# Rendered Proof

Rendered UI work is not complete until it has been seen or the blocker is
reported.

## Proof Ladder

Use the strongest available proof:

1. Chrome DevTools MCP against the real browser-rendered UI.
2. Browser with local dev server and screenshots.
3. Storybook or component preview.
4. Framework preview/build output plus static screenshots.
5. Unit/component tests with DOM assertions.
6. Static scanner only, with explicit note that visual proof is missing.

Do not edit MCP registry, harness config, browser launch config, or global tool
installs from this skill. Use the Chrome DevTools MCP tools already available in
the active harness. If they are unavailable, state that blocker and fall back to
the next proof tier.

## Chrome DevTools MCP Workflow

For browser-rendered UI, default to this sequence:

1. Start or identify the local app, Storybook, preview, or target URL.
2. Use `list_pages`, then `select_page` when a suitable page already exists, or
   `new_page` / `navigate_page` when navigation is needed.
3. Wait for a stable marker with `wait_for` when a known heading, label, route,
   or loaded state exists.
4. Capture structure with `take_snapshot` before interacting. Use snapshot
   `uid`s for `click`, `fill`, `hover`, `press_key`, `upload_file`, or `drag`.
5. Inspect `list_console_messages` for errors and issues.
6. Inspect `list_network_requests` for failed or suspicious UI-critical
   requests, then inspect individual requests only when needed.
7. Exercise the key interaction path. Take a fresh snapshot after state changes.
8. Capture `take_screenshot` for visual proof when layout, contrast, media,
   canvas, responsive behavior, or animation framing matters.

Keep dependent actions ordered: navigate, wait, snapshot, interact, verify.
Save large screenshots, traces, network bodies, heap snapshots, and Lighthouse
reports to explicit file paths outside version control.

## Accessibility Tree And Focus Proof

Use Chrome DevTools snapshots as primary evidence for semantics and focus:

- Check landmarks, headings, roles, names, button/link labels, form labels, and
  exposed state in `take_snapshot`.
- Verify keyboard paths with `press_key` and fresh snapshots after each major
  movement.
- For dialogs, popovers, menus, drawers, and command palettes, confirm focus
  enters the surface, the expected controls are reachable, escape/close works,
  and focus returns to a sensible trigger.
- Use screenshots as supporting evidence for visible focus, contrast, target
  size, and overlap. Do not treat screenshots as a substitute for the exposed
  accessibility tree.
- If a Lighthouse accessibility report exists, extract failed audits instead of
  reading the entire report into context.

## LCP And Hero Proof

Use LCP checks only when the request involves perceived load, a hero surface,
the largest above-the-fold element, or Core Web Vitals evidence.

- Identify the actual visible hero/LCP candidate before recommending fixes.
- If trace tools are available, capture a bounded performance trace with reload
  only when a reload is safe, then inspect LCP breakdown, document latency,
  render-blocking, discovery, and network timing evidence as available.
- Check whether the hero/LCP resource is discoverable in initial HTML, has sane
  priority, avoids accidental lazy loading, and is not delayed by blocking CSS,
  scripts, or main-thread work.
- Recommend the smallest change that targets the slowest observed subpart:
  TTFB, resource load delay, resource load duration, or element render delay.
- Verify under comparable network and CPU conditions after a fix.

## Memory And Performance Smells

`/design` is not a full memory-profiler replacement. For UI work, use browser
memory or performance evidence only to catch visible interaction regressions and
obvious leak smells:

- Repeatedly open/close high-risk UI such as modals, menus, drawers, previews,
  canvases, or long virtualized lists when the change touches lifecycle code.
- Watch for detached DOM nodes, unremoved event listeners, unbounded arrays or
  maps, accidental globals, retained media/canvas resources, and animation loops
  that continue after a surface is hidden.
- If heap snapshots are needed, save them to explicit paths outside version
  control and analyze bounded summaries. Never read raw `.heapsnapshot` files
  into the conversation.
- Route deep non-UI profiling to `performance-profiler`.

## Troubleshooting Fallback

If Chrome DevTools MCP proof cannot run:

- Record the exact missing tool, connection error, page-selection issue,
  navigation failure, or timeout.
- Do not mutate MCP config from `/design`. For repo-managed harnesses, preserve
  the shared attached-browser contract and route setup/config repair outside
  this skill.
- Fall back to manual browser screenshots, Playwright, Storybook screenshots,
  framework preview output, component tests, or static scanner evidence.
- In the final proof section, name both the attempted Chrome DevTools step and
  the fallback proof used.

## CLI Fallback

Use the `chrome-devtools` CLI only when the user asks for shell commands or the
current harness lacks MCP tool calls but the CLI is available.

- Prefer direct MCP tools over CLI when possible.
- Run `chrome-devtools <tool> --help` before unfamiliar flags.
- Use JSON output for scripts that need stable parsing.
- Do not install or update global npm packages unless the user explicitly asks.
- Keep trace, screenshot, heap, and snapshot artifacts out of version control.

## Required Checks

- Desktop and mobile viewport.
- Loading, empty, error, and long-content states when applicable.
- Keyboard focus and tab order for interactive surfaces.
- Contrast over images, gradients, and disabled states.
- No clipped text, overlapping controls, blank media, broken images, or layout
  shift from dynamic content.
- Reduced-motion behavior for animated surfaces.
- Console and network health for UI-critical failures when a browser is open.

## 3D / Canvas

For canvas or WebGL:

- Confirm the canvas is nonblank with a screenshot or pixel check.
- Verify camera framing at desktop and mobile sizes.
- Cap pixel ratio when performance matters.
- Check resize handling.
- Confirm controls or animation are intentional and not disorienting.

## Reporting Template

```text
Rendered proof:
- Command:
- URL or preview:
- Viewports:
- Screenshots or observations:
- Blockers:
```
