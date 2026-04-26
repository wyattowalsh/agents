# Export and Graph Management

Exports are downstream products of the Docling Graph artifact. Validate the graph before loading or analyzing it elsewhere.

## Export Targets

| Target | Use for | Checks |
| --- | --- | --- |
| JSON | Canonical handoff, regression fixtures, API payloads | Schema version, required fields, stable IDs |
| CSV | Analyst review, staging tables, spreadsheet QA | One entity/relationship type per table, normalized IDs |
| Cypher/Neo4j | Graph database loading | Uniqueness constraints, relationship direction, idempotent merge |
| NetworkX | Algorithms and graph QA | Connected components, orphan nodes, centrality sanity |

## Pre-Export Gate

Before export, verify:

- Inspect report has no unexplained extraction failures.
- Root model count matches expected document-level graph count.
- Entity IDs are stable and unique.
- Relationship directions match the template semantics.
- Required fields are populated or explicitly nullable.
- Duplicate entities and orphan relationships are understood.

## Neo4j Pattern

Use stable IDs as uniqueness constraints before loading:

```cypher
CREATE CONSTRAINT organization_id IF NOT EXISTS
FOR (n:Organization)
REQUIRE n.id IS UNIQUE;
```

Use idempotent merge semantics for nodes and relationships. Do not create relationships from display names when stable IDs are available.

## NetworkX QA

NetworkX is useful for checks that are awkward in raw JSON:

- Count connected components.
- Find isolated nodes.
- Check relationship direction around key entity types.
- Compare expected vs actual degree for root entities.
- Sample shortest paths between known linked entities.

## Export Handoff

Include:

- Source run command or redacted API config.
- Template version or git SHA.
- Extraction contract.
- Inspect report path.
- Graph artifact path.
- Export command/config.
- Integrity counts: nodes, relationships, duplicate IDs, orphan nodes, missing required fields.
