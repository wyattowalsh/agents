# Export and Graph Management

## Contents

1. Output Targets
2. Format Selection
3. NetworkX Access
4. CSV Checks
5. Cypher Checks
6. JSON and HTML
7. Validation Checklist

## Output Targets

Use this reference in **Export** mode.

Docling Graph can produce files for analysis, graph databases, application code, and human inspection. Choose the export by downstream use, not by habit.

## Format Selection

| Target | Format | Notes |
|---|---|---|
| Spreadsheet, pandas, SQL, analyst review | CSV | Separate nodes and edges are easy to inspect |
| Neo4j import or graph database loading | Cypher | Check labels and relationship names before import |
| Application code or API response | JSON or NetworkX | Preserve graph structure for programmatic use |
| Human review and debugging | HTML report or Markdown report | Useful before trusting extraction quality |

If multiple audiences exist, export more than one format from the same run directory.

## NetworkX Access

In API mode, the graph is available in memory:

```python
context = run_pipeline(config)
graph = context.knowledge_graph

node_count = graph.number_of_nodes()
edge_count = graph.number_of_edges()
labels = {
    data.get("label")
    for _, data in graph.nodes(data=True)
}
```

Use NetworkX access when the user needs custom validation, transformation, metrics, or integration with another Python system.

## CSV Checks

CSV export usually includes node and edge files. Validate:

1. `nodes.csv` exists and has rows.
2. `edges.csv` exists and has rows when relationships are expected.
3. Required labels/classes appear.
4. Stable ID columns are populated.
5. Edge labels match template relationship names.

For analyst handoff, include column descriptions and known extraction caveats.

## Cypher Checks

Before importing into Neo4j:

1. Review generated labels and relationship types.
2. Confirm IDs are stable and unique.
3. Run against a scratch database first.
4. Add uniqueness constraints manually if the generated import does not create them.
5. Keep the original output directory with metadata for traceability.

Graph database administration is out of scope for this skill after import artifacts are produced.

## JSON and HTML

Use JSON when a service, notebook, or downstream script needs structured graph data.

Use HTML/report output when humans need to inspect the graph. For first runs, always inspect the visualization or summary report before claiming success.

## Validation Checklist

Report these checks after any export plan:

| Check | Pass signal |
|---|---|
| Node count | Greater than zero and plausible for document |
| Edge count | Greater than zero when relationships are expected |
| Labels | Expected domain node types appear |
| IDs | No obvious volatile IDs or duplicates |
| Edges | Relationship labels match domain semantics |
| Coverage | Key facts from source appear in graph |
| Traceability | Output dir, command/config, provider/model, template version recorded |

For batch outputs, aggregate counts per document and flag outliers for manual review.
