# Debugging Docling Graph

Debug from source evidence to graph artifact. Do not start with the export layer unless the graph artifact is already proven correct.

## Triage Order

1. Confirm version, Python, provider credentials, CLI/API command, and source path.
2. Lint the template for root model, stable IDs, field descriptions, relationship typing, and contract fit.
3. Reproduce with one small source and debug dumping enabled.
4. Run `docling-graph inspect OUTPUT_DIR`.
5. Read `debug/trace_data.json` for stage inputs, structured-output failures, sparse-check findings, fallback parser output, and graph mapping errors.
6. Compare source evidence -> extraction JSON -> graph artifact -> export artifact.

## Common Failure Patterns

| Symptom | Likely cause | First check |
| --- | --- | --- |
| Missing required fields | Weak field descriptions, source evidence absent, sparse-check failure | Field descriptions and sparse-check output |
| Missing relationships | Relationship field typed too loosely, no stable IDs, wrong contract | Template relationship fields and graph ID fields |
| Duplicate entities | ID strategy unstable or resolver not configured | `graph_id_fields`, normalized IDs, delta resolver traces |
| Empty graph | Wrong root model, template import failure, source not parsed | CLI/API template path and inspect summary |
| Provider rejects schema | Schema too large or unsupported structured output | Contract choice and structured-output fallback |
| Export looks wrong | Graph artifact already wrong or export mapping drifted | Validate graph artifact before export |

## Trace Data

When available, `debug/trace_data.json` is the most useful artifact. Look for:

- Provider/model config actually used.
- Extraction contract and stage list.
- Prompt/schema payload sizes.
- Structured-output success or fallback.
- Sparse-check failures.
- Gleaning pass deltas.
- Graph mapping warnings.
- Resolver decisions for delta extraction.

Redact secrets before sharing traces.

## Inspect Report

Use:

```bash
docling-graph inspect OUTPUT_DIR
```

Review:

- Stage timeline and errors.
- Extracted object counts by model.
- Relationship counts and orphan nodes.
- Missing required fields.
- Duplicate IDs.
- Links from final graph fields back to extraction artifacts where available.

## Minimal Fix Ladder

Prefer the smallest change that addresses the observed artifact:

1. Improve field descriptions.
2. Add or correct `graph_id_fields`.
3. Tighten relationship types.
4. Switch direct -> staged for oversized/nested schemas.
5. Switch staged -> delta when entity resolution dominates.
6. Enable structured output or adjust fallback handling.
7. Add bounded gleaning for recall-sensitive fields.
8. Change provider/model only after schema and contract issues are ruled out.

## Debug Response Template

Return:

- Reproduction command/config.
- Artifact reviewed.
- First failing step in the source -> extraction -> graph -> export chain.
- Root cause with evidence.
- Minimal patch.
- Verification command and expected invariant.
