# Graph

## Edge Sources

Current edge extraction reads:

- Obsidian `[[wikilinks]]`
- Embeds `![[...]]`
- Markdown links
- Aliases, source ID citations, heading links, and block references through the derived graph builder

The package exposes `nerdbot.graph.extract_edges()` for the stable baseline link surface and `nerdbot.graph.build_graph()` for rebuildable derived analytics. Relative Markdown links are normalized against the source page for broken-link checks, and bare wikilinks can satisfy orphan detection through basename matching. `nerdbot derive --artifact graph --apply` writes `indexes/generated/graph-edges.jsonl` and `indexes/generated/graph-report.md`.

## Analytics

Graph analytics include node count, edge count by type, orphan wiki pages, broken local targets, alias collisions, embed count, heading/block-reference link count, top in-degree/out-degree lists, and source citation coverage.

Every edge includes `source`, `target`, `edge_type`, `evidence_path`, and `confidence`. Supported edge types are `links_to`, `embeds`, `aliases`, `cites`, `derives_from`, `updates`, `contradicts`, and `mentions`.

## Safety

Graph commands are read-only unless the user explicitly asks to enqueue review items or approve a migration batch. Generated Markdown reports render untrusted targets and metrics as code spans so malicious note/link text is displayed as data rather than interpreted as report structure.
