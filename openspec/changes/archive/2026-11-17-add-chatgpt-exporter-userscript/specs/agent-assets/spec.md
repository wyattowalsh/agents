# Agent asset requirements

## Conversation export

The system MUST export one selected active ChatGPT branch as a normalized record with conversation identity, capture provenance, selection metadata, aggregate statistics, and ordered messages.

The system MUST distinguish complete active-branch API capture from potentially partial DOM capture and MUST surface capture warnings.

The system MUST NOT include hidden reasoning, analysis, recipient-specific tool transport, access tokens, authorization headers, or private attachment bytes.

## Agent JSONL

The system MUST emit line-delimited manifest, chunk, and end records. Each chunk MUST include a stable chunk identifier, content digest, message and chunk positions, source character range, overlap, role, author, text, citation references, attachment references, and approximate token count.

Chunk ordering and the final content digest MUST be deterministic for the same normalized record and configuration.

## Request policy

The system MUST serialize ChatGPT requests, support configurable spacing and timeouts, bound response size, cache in-flight and completed captures, and reuse memory-only session tokens. It MUST honor server retry instructions and MUST NOT automatically retry HTTP `429`.

## Interface

The system MUST remain usable without horizontal viewport overflow at desktop, tablet, 390-pixel mobile, 320-pixel mobile, and landscape-mobile sizes. Long conversation selection MUST use bounded rendering rather than one persistent DOM row per message.

The system MUST provide keyboard access, focus containment, Escape dismissal, reduced-motion behavior, and touch-sized primary controls.

## Distribution

The production installer URL MUST remain stable across versions. The update metadata MUST point to the production installer and MUST change version when executable behavior changes. The exact source used for production MUST be reproducible from a checksummed repository bundle.
