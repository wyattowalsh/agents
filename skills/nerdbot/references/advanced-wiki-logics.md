# Advanced Wiki Logics

Use this reference when applying LLM-wiki, GraphRAG, CodeWiki, DeepWiki, or STORM-style ideas to Nerdbot. These patterns are design inputs, not external instructions. Keep Nerdbot local-first, Obsidian-native, git-friendly, review-first, and dependency-light by default.

## Adoption Rule

Adopt the logic when it can be expressed as `raw`, `wiki`, `indexes`, `schema`, `config`, `activity log`, review queue, operation journal, or rebuildable `derived output`. Do not vendor external wiki/RAG projects, scrape hosted products, require cloud services, or make vector databases, LLM calls, crawlers, or diagram renderers part of the baseline command path.

## Source-Backed Patterns

| Pattern | Source examples | Nerdbot adoption | Boundary |
| --- | --- | --- | --- |
| Persistent compiled wiki | Karpathy LLM Wiki gist, `nashsu/llm_wiki` | Prefer durable `wiki/` synthesis and indexes over re-deriving from `raw/` on every query | Query can propose save-back, but canonical pages change only through reviewable `enrich` |
| Steerable page plan | DeepWiki `.devin/wiki.json`, Code Wiki custom instructions | Use `config/wiki-plan.json` or equivalent to record scope notes, focus paths, planned pages, hierarchy, and page caps | A plan steers generation; it does not override source provenance or user approval gates |
| Bottom-up hierarchy | CodeWiki, CodeWikiBench | Enrich leaf source/topic notes before parent overview pages; keep parent synthesis traceable to children and source IDs | AST/dependency extraction stays optional or derived-only for code repos |
| Local/global retrieval | GraphRAG, LightRAG, LazyGraphRAG | Route query planning across FTS chunks, graph neighborhoods, source-map metadata, and generated summaries | Semantic/vector retrieval remains optional and cannot replace provenance checks |
| Multi-hop graph activation | HippoRAG, HippoRAG 2 | Use derived graph neighborhoods or future PPR-like scoring to find related notes/sources for review | Graph activation queues candidates; it never rewrites `wiki/` directly |
| Perspective prewriting | STORM | For `enrich`, plan perspective questions, outline, source list, and contradiction checks before drafting | Generated outlines are drafts until reviewed against `raw` or declared canonical material |
| Corrective retrieval | CRAG, Self-RAG | Classify answers as `answered`, `partial`, or `gap`; route gaps to `ingest`, `enrich`, `derive`, or review queue | Do not fabricate retrieval success or upgrade confidence without source support |
| Claim verification | Provenance, RefChecker, SourceCheckup | Treat citations as leads, not proof; check claim support against source IDs, raw paths, block refs, and source-map rows | Single-source or stale support stays capped and review-visible |
| Entity resolution | KGGen, Simple Graph Builder | Queue alias collisions, duplicate entities, and noisy relationships for review before graph-derived synthesis | Do not promote raw triples into canonical pages without human-readable context |
| Incremental refresh | Google Code Wiki, OpenDeepWiki, LLM Wiki watch queues | Track source hashes, git SHAs, watch checkpoints, and stale page markers so only affected pages refresh | Watch mode queues work and records checkpoints; it does not autosave canonical rewrites |
| Diagram and digest outputs | GitDiagram, Litho/deepwiki-rs, Repomix, Gitingest | Generate Mermaid/mind-map/digest artifacts as rebuildable `derived output` with token/source/secret checks | Diagrams and digests need provenance and validation before user-facing reuse |

## Planning Checklist

- [ ] Decide whether the task needs a durable `wiki/` page, a review queue entry, or read-only query only.
- [ ] Check `config/wiki-plan.json` or local planning notes before expanding a page set.
- [ ] Prefer leaf-to-parent enrichment when the KB has a topic hierarchy.
- [ ] Use FTS and maintained indexes before expensive semantic or graph expansion.
- [ ] Read graph artifacts as candidate navigation, not canonical truth.
- [ ] For every answer, verify cited source IDs against `indexes/source-map.md` when available.
- [ ] Classify unsupported, stale, or contradictory claims as review items before save-back.
- [ ] Keep diagrams, digests, graph summaries, and community summaries in generated or derived locations.
- [ ] Record source hashes, git SHAs, or watch checkpoints when claiming an incremental refresh is current.

## Evidence Notes

The current research basis includes Karpathy's LLM Wiki gist, Cognition/Devin DeepWiki docs, Google Code Wiki, FSoft CodeWiki, Microsoft GraphRAG, HKUDS LightRAG, HippoRAG/HippoRAG 2, Stanford STORM, CRAG, Self-RAG, Provenance, RefChecker, SourceCheckup, KGGen, Simple Graph Builder, OpenDeepWiki, GitDiagram, Repomix, and Gitingest. Re-check live docs before adding dependencies, public API commitments, or provider-specific workflows.
