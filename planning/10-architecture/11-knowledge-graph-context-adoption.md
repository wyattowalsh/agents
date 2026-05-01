# Knowledge Graph And Context Adoption

## Scope

This lane evaluates graph, memory, context, and knowledge-base candidates from the external intake queue. It defines adoption recommendations without installing external repos or changing MCP/skill implementations.

## Candidate Fit

| Candidate Class | Default Fit | Rationale |
| --- | --- | --- |
| Static graph generation | Skill or CLI | Deterministic output, easier fixture coverage, no live process required. |
| Repo indexing and summaries | Skill or CLI | Can run on checked-out files with stable JSON/Markdown output. |
| Persistent query state | MCP only when justified | MCP is appropriate when long-lived live state or interactive querying is required. |
| Personal memory or profile state | Quarantine review first | Can contain sensitive user data and retention concerns. |

## Review Targets

Initial candidate records should include graph/context external repos from C10, including `EXT-003`, `EXT-028`, `EXT-033`, `EXT-036`, `EXT-042`, and `EXT-055`, plus any later queue records routed to this lane. Queue/backlog mismatches must be recorded instead of silently normalized.

## Fixture Gates

Before adoption, each candidate needs:

- Minimal corpus fixture.
- Deterministic graph or context output.
- Incremental update behavior.
- Redaction policy for paths, notes, and personal data.
- Export/import or rollback story.
- Clear skill-first vs MCP rationale.

## Adoption Recommendations

1. Promote deterministic graph/context generation as skills or CLIs first.
2. Use MCP only for live, persistent, user-queryable state.
3. Require C15 review for memory systems that store personal or credential-adjacent context.
4. Keep external repos as discovery sources until source, license, security, and fixture gates pass.
