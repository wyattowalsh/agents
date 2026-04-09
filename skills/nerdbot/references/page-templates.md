# Page Templates

## Template map
| Need | Asset | Suggested path | Required focus |
|------|-------|----------------|----------------|
| Bootstrap core KB files | `assets/kb-bootstrap-template.md` | `wiki/index.md`, `indexes/source-map.md`, `indexes/coverage.md`, `activity/log.md` | Scope, starter indexes, and first queue |
| Record a source and its planned coverage | `assets/source-summary-template.md` | `wiki/topics/[source-id]-source-summary.md` | `raw` link, summary, `provenance`, and planned `wiki` targets |
| Explain a concept | `assets/concept-page-template.md` | `wiki/topics/[concept].md` | Definition, implications, and `provenance` |
| Track a person, team, system, or vendor | `assets/entity-page-template.md` | `wiki/topics/[entity].md` | Identity, relationships, timeline, and `provenance` |
| Create a landing page | `assets/overview-page-template.md` | `wiki/index.md` or `wiki/topics/[topic]/index.md` | Scope, current map, coverage, and gaps |
| Compare approaches or entities | `assets/comparison-page-template.md` | `wiki/topics/[comparison].md` | Stable comparison dimensions and `provenance` |
| Seed or append the log | `assets/activity-log-template.md` | `activity/log.md` | Append-only batch history |

## Shared page contract
- [ ] Title is stable and specific.
- [ ] Scope is explicit.
- [ ] The page points to backing `raw` or `canonical material`.
- [ ] `Provenance` is present for substantive claims.
- [ ] Related `indexes` or `wiki` pages are linked.
- [ ] Open questions are recorded instead of silently omitted.

## Core file shapes

### `wiki/index.md`
Recommended shape:
1. `Scope`
2. `Canonical material`
3. `Current wiki map`
4. `First ingest queue` or `Current priorities`
5. `Related indexes`

### `indexes/source-map.md`
Recommended columns:

| Source ID | Raw path | Capture type | Planned wiki target | Canonical material touched? | Provenance status | Status |
|-----------|----------|--------------|---------------------|-----------------------------|-------------------|--------|

### `indexes/coverage.md`
Recommended columns:

| Wiki path | Page type | Backing raw or canonical material | Coverage status | Last reviewed | Notes |
|-----------|-----------|-----------------------------------|-----------------|---------------|-------|

### `activity/log.md`
Recommended entry shape:

```md
### [YYYY-MM-DD HH:MM] [Batch label]
- Mode: [create|ingest|enrich|derive|improve|migration]
- Summary: [what changed]
- `raw`: [files]
- `wiki`: [files]
- `indexes`: [files]
- `schema`: [files added or updated / unchanged]
- `config`: [files added or updated / unchanged]
- `canonical material`: [unchanged/annotated/approved exception]
- `provenance`: [linked or missing]
- `derived output`: [none or path]
- Risks / rollback: [if relevant]
- Follow-up:
  - [next safe batch]
```

## Source summary shape
Keep source summary pages compact and directly tied to `raw`.

| Section | What to capture |
|---------|-----------------|
| Source record | Source ID, `raw` paths, import date, and status |
| Summary | What the source says without rewriting it into `wiki` prose |
| Provenance | The claim-to-source map |
| Planned wiki coverage | Where the evidence should appear in `wiki` |

## Page selection guidance
- Use an overview page when the reader needs the current map first.
- Use a concept page when the reader needs definition and boundaries.
- Use an entity page when relationships or a timeline matter.
- Use a comparison page when the reader needs stable dimensions across multiple items.
- Use a source summary page before broad synthesis if evidence is still new or incomplete.

## Template use checklist
- [ ] Start from the smallest page type that fits the need.
- [ ] Keep the first version reviewable; do not fill every optional section on day one.
- [ ] Update `indexes` and the `activity log` in the same batch.
- [ ] Preserve `canonical material` by extending or linking before rewriting.
