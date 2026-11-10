# Design: ChatGPT Exporter for Agents

## Architecture

The userscript is dependency-free at runtime and has four boundaries:

1. capture: same-origin API first, rendered DOM fallback;
2. normalization: active-branch messages, citations, attachments, provenance, and warnings;
3. serialization: human formats and schema-backed agent formats;
4. presentation: responsive Shadow DOM UI and userscript-manager configuration.

## Capture and network behavior

Requests are single-flight per conversation and cached for a configurable interval. A serialized request gate enforces a configurable minimum interval. Session tokens remain memory-only. Requests have timeouts and response-size limits. Transient errors use bounded exponential backoff with jitter. `Retry-After` is honored, and HTTP `429` is surfaced rather than automatically retried.

API capture traverses the active parent chain from the current node. It excludes analysis, hidden reasoning, recipient-specific tool transport, and visually hidden records. DOM capture is explicitly marked potentially partial. Optional deep scanning restores the original scroll position.

## Agent output

Agent JSONL uses manifest, chunk, and end records. Chunks include stable identifiers, content digests, message and chunk ordinals, source character offsets, overlap, role, author, timestamps, citations, attachment references, and approximate tokens. Chunking prefers semantic boundaries and preserves deterministic overlap.

## UI and performance

The interface is isolated in a Shadow DOM. The message selector is virtualized, so DOM node count remains bounded for long conversations. Layouts cover large desktop, tablet, portrait mobile, 320-pixel width, and landscape mobile. Controls honor safe areas, reduced motion, keyboard navigation, focus trapping, and touch target sizing.

## Distribution

The stable installer and metadata endpoints are served from `chatgpt-export-local.vercel.app`. The exact validated source is retained as a checksum-verified split archive under the repository package path. A portable materializer supports GNU/Linux and BSD/macOS command variants.

## Security

There are no runtime dependencies, telemetry calls, or remote export processors. Exported HTML has no scripts, uses a restrictive Content Security Policy, and filters URL protocols. CSV serialization neutralizes formula prefixes. Credentials and private attachment bytes are excluded.
