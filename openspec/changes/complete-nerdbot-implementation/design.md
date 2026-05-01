# Design

## Approach

Build from the safety core outward. First make path, write, append, and operation-record primitives explicit and tested. Then route CLI workflows through those primitives so every public mutating command has dry-run, apply, journal, and replay semantics. Keep generated retrieval and graph artifacts rebuildable, and keep legacy scripts as compatibility adapters rather than parallel implementations.

## Data And Control Flow

- CLI commands parse input into typed package-level plan or operation objects.
- Mutating workflows produce a dry-run manifest by default and only write after an explicit apply flag or confirmation gate.
- Every applied mutation records operation metadata in append-only JSONL under `activity/` before or alongside file changes.
- Source ingestion creates source records, raw or pointer artifacts, wiki summaries, and review/evidence queue entries with stable source IDs.
- Retrieval searches trusted index/wiki surfaces first, reports provenance for every hit, and treats raw content as untrusted evidence to inspect rather than instructions to follow.
- Graph and retrieval indexes are derived from canonical Markdown/source records and can be rebuilt from the vault.

## Implementation Principles

- Prefer small package modules with direct CLI orchestration over hidden framework abstractions.
- Preserve existing script entrypoints and public command names unless a breaking change is explicitly documented.
- Use only baseline Python dependencies for core workflows; optional extras must fail with actionable install guidance when missing.
- Keep Obsidian output as plain Markdown with YAML frontmatter, wikilinks, embeds, aliases, and Dataview-compatible metadata.
- Keep raw source material append-only and canonical wiki pages additive unless migration/apply plans explicitly say otherwise.

## Safety Model

- Validate all user-controlled paths before any future write, read, watch, replay, or generated-output operation consumes them.
- Reject symlink escapes, ancestor escapes, absolute paths where a vault-relative path is required, hardlink overwrite hazards, and platform-specific reparse/junction hazards when detectable.
- Use crash-durable atomic writes for file replacement and append-only writers for logs, operations, evidence, and activity records.
- Store rollback/replay metadata sufficient to explain and reverse starter-file writes where reversal is supported.
- Never interpret imported KB/raw content as agent instructions.

## Alternatives Rejected

- Docs-only clarification: rejected because the accepted goal is full robust implementation of advertised behavior.
- Separate rewrite package: rejected because existing scripts, tests, package metadata, and docs already define compatibility surfaces.
- Database-first canonical state: rejected because the product is local-first and Obsidian-native; SQLite/graph artifacts must remain rebuildable derived indexes.
- Mandatory heavy integrations: rejected because the base skill must work locally with no network or heavyweight dependencies.

## Migration Or Compatibility Notes

- Existing KBs should continue to work as plain Markdown vaults.
- Existing `kb_*` scripts should remain callable while internally reusing package primitives where safe.
- Generated artifacts should be rebuildable and safe to delete.
