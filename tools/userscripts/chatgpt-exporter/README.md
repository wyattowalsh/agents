# ChatGPT Exporter for Agents

A privacy-first, rate-limit-aware userscript for exporting the active ChatGPT conversation branch for people and downstream agents.

## Install or update

Install the current production build from:

<https://chatgpt-export-local.vercel.app/chatgpt-exporter.user.js>

The installed userscript checks:

<https://chatgpt-export-local.vercel.app/chatgpt-exporter.meta.js>

The production alias is stable. Future releases update in place after the userscript metadata version is incremented.

## Capabilities

- Same-origin ChatGPT API capture with a rendered-DOM fallback.
- Single-flight capture caching, serialized requests, configurable request spacing, timeouts, response-size limits, and bounded transient retries.
- Explicit handling of `Retry-After`; HTTP `429` is not automatically retried.
- Active-branch traversal that excludes hidden reasoning, analysis, and tool-transport messages.
- Responsive Shadow DOM interface for desktop, tablet, mobile, 320-pixel-wide, and landscape layouts.
- Virtualized message selection, filtering, search, range selection, and role correction.
- Agent JSONL with manifest/chunk/end records, stable chunk identifiers, content hashes, source offsets, message provenance, citations, and attachment references.
- Markdown, agent Markdown, JSON, JSONL, gzip JSONL, CSV, text, standalone HTML, clipboard, and browser print/PDF exports.
- ScriptCat `UserConfig`, userscript-manager menu commands, local settings fallback, SPA navigation handling, reduced-motion support, and keyboard/focus accessibility.
- No runtime JavaScript dependencies, telemetry, or third-party export service.

## Verified source bundle

The complete reviewed source tree is stored reproducibly under [`source/`](./source/) as split base64 for an XZ-compressed tar archive. This preserves the exact validated bytes while remaining compatible with GitHub's text-oriented APIs.

Materialize the source into a checkout of this repository:

```bash
./tools/userscripts/chatgpt-exporter/materialize.sh
```

The script:

1. concatenates the ordered payload parts;
2. decodes the tar archive with GNU or BSD/macOS `base64`;
3. verifies SHA-256 `d2a48597e564e3f118d6a74fb088788246531893299da38b5db0dcc84fe5b1fc`;
4. extracts into a temporary directory;
5. copies the full source, schemas, tests, generated userscript, documentation, and OpenSpec records into the checkout.

The source manifest is [`source/manifest.json`](./source/manifest.json).

## Validation evidence

The exact bundled source passed:

- deterministic build check;
- Node syntax checks for source and generated userscript;
- 20 of 20 unit tests;
- the official ScriptCat static checker with zero warnings and zero failures;
- targeted secret scanning with zero findings;
- Chromium integration testing at 1440×960, 820×1180, 390×844, 320×568, and 844×390;
- 750-message virtual-list behavior;
- API capture, DOM fallback, route changes, capture caching, token reuse, selection, JSONL, local gzip, and rate-limit behavior;
- viewport overflow, console-error, and page-error assertions.

## Privacy and security

Exports are generated locally. Credentials remain in memory and are excluded from exports and debug output. HTML output uses a restrictive Content Security Policy and protocol-filtered links. CSV output neutralizes formula injection. Private attachment bytes are not fetched or embedded.

## Release discipline

A release must update the userscript version, rebuild deterministic artifacts, rerun validation, update the source bundle and checksum, and redeploy the stable production alias.

This project is independent and is not affiliated with OpenAI or the commercial Chrome Web Store extension with a similar purpose.
