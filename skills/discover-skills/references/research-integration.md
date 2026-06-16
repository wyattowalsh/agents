# Research Integration

Web-researcher scouts use bounded research patterns without invoking full `/research` promotion flows.

## When to Use

- Wave 2 `web-researcher` tasks for high-priority gap domains
- GitHub, community, and doc searches from `references/research-queries.md`

## When to Redirect

- Open-ended investigation → `/research`
- Instruction or repo policy changes → `/learn`

## Boundaries

- Read-only: no Edit/Write; discover PreToolUse hooks remain active
- Evidence is input to merge/ideation only; do not promote findings into instructions
- Optional evidence ledger under harness research paths is separate from discover journals

## Scout Prompt Essentials

1. Load only queries for the assigned `domain_id`
2. Return `scout-artifact` JSON to the manifest artifact path
3. Tag provenance: `brave-search`, `github`, `community`
4. Deduplicate against `gap-report.json` existing skills