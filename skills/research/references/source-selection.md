# Source Selection

Complete tool-to-domain mapping for research tool selection. Read during Wave 0 to select the right tools for each sub-question.

## Tool Inventory

### Web Search

| Tool | MCP Name | Strengths | Latency |
|------|----------|-----------|---------|
| Brave Search | `brave-search` → `brave_web_search` | General web, news, local results | Fast |
| DuckDuckGo | `duckduckgo` → `search` | Privacy-respecting index, different ranking | Fast |
| Exa | `exa` → `search` | Semantic search, embeddings-based retrieval | Medium |
| G-Search | `g-search` → `search` | Google index via API | Fast |
| Tavily | `tavily` → `tavily_search`, `tavily_research` | AI-optimized snippets, deep research mode | Medium |

### Academic

| Tool | MCP Name | Strengths | Coverage |
|------|----------|-----------|----------|
| arXiv | `arxiv` → `search_papers`, `download_paper` | Preprints, CS/ML/physics/math | 2.4M+ papers |
| Semantic Scholar | `semantic-scholar` → `search`, `get_paper` | Citation graph, influence scores | 200M+ papers |
| PubMed | `PubMed` → `search_articles`, `get_full_text_article` | Biomedical, life sciences | 36M+ citations |
| OpenAlex | `openalex` → `search` | Open bibliometric data, all fields | 250M+ works |
| Crossref | `crossref` → `search` | DOI resolution, metadata, citation counts | 150M+ records |

### Knowledge

| Tool | MCP Name | Use For |
|------|----------|---------|
| Context7 | `context7` → `resolve-library-id`, `query-docs` | Library/framework docs, API signatures, deprecation info |
| DeepWiki | `deepwiki` → `ask_question`, `read_wiki_contents`, `read_wiki_structure` | GitHub repo architecture, design decisions |
| Wikipedia | `wikipedia` → `search`, `get_article` | General knowledge, definitions, historical context |
| Wikidata | `wikidata` → `query` | Structured factual claims, entity relationships |

### Content Extraction

| Tool | MCP Name | Use For |
|------|----------|---------|
| Fetcher | `fetcher` → `fetch_url`, `fetch_urls` | Raw page content, batch URL fetching |
| Trafilatura | `trafilatura` → `fetch_and_extract` | Clean article text extraction from HTML |
| Docling | `docling` → `convert_document_into_docling_document` | PDF/document parsing, table extraction |
| Fetch | `fetch` → `fetch_markdown`, `fetch_html` | Markdown/HTML conversion |

### Code and Packages

| Tool | MCP Name | Use For |
|------|----------|---------|
| Repomix | `repomix` → `pack_codebase`, `pack_remote_repository` | Full codebase analysis, remote repo packing |
| Package Version | `package-version` → `check_npm_versions`, `check_pyproject_versions`, `check_go_versions` | Dependency version checks, latest release info |

### Historical

| Tool | MCP Name | Use For |
|------|----------|---------|
| Wayback | `wayback` → `search`, `get_snapshot` | Historical web pages, deleted content, versioned snapshots |

### Thinking MCPs

| Tool | MCP Name | Use For |
|------|----------|---------|
| Think Strategies | `think-strategies` → `think-strategies` | Complex question decomposition, strategy selection |
| Cascade Thinking | `cascade-thinking` → `cascade_thinking` | Multi-perspective analysis of complex findings |
| Structured Thinking | `structured-thinking` → `capture_thought`, `revise_thought` | Evidence chain tracking, contradiction management |

## Domain-to-Tool Mapping

Select tools based on the domain signals detected in the query.

| Domain Signal | Primary Tools | Secondary Tools | Notes |
|--------------|---------------|-----------------|-------|
| Library/API docs | context7, deepwiki, package-version | brave-search, fetch | Always resolve library ID first via context7 |
| Academic/scientific | arxiv, semantic-scholar, PubMed | openalex, crossref, brave-search | Use PubMed only for biomedical; crossref for DOI resolution |
| Current events/trends | brave-search, exa, tavily | duckduckgo, g-search, fetcher | Use 2+ engines; exa for semantic relevance |
| GitHub repos/OSS | deepwiki, repomix | brave-search, package-version | deepwiki for architecture; repomix for code-level analysis |
| General knowledge | wikipedia, wikidata, brave-search | fetcher, trafilatura | Wikidata for structured facts; wikipedia for narrative context |
| Historical content | wayback, brave-search | fetcher, trafilatura | Wayback for deleted/changed pages |
| Fact-checking | 3+ search engines mandatory | wikidata for structured claims | Use brave-search + duckduckgo + exa minimum |
| PDF/document analysis | docling, trafilatura | fetcher, fetch | Docling for tables/structured data; trafilatura for article text |
| Market/competitive | brave-search, exa, tavily | fetcher, trafilatura | Combine web search with content extraction for depth |
| Technical comparison | context7, brave-search, deepwiki | package-version, exa | Ground comparisons in official docs |

## Multi-Engine Search Protocol

For any claim requiring verification, use a minimum of 2 different search engines. Different engines maintain different indices, apply different ranking algorithms, and surface different results.

1. **Minimum 2 engines** for any cross-validation search
2. **Minimum 3 engines** for fact-checking mode
3. **Rotate engine pairs** across sub-questions to maximize index diversity
4. **Treat agreement across engines as confidence signal** — if brave-search and duckduckgo return the same claim from different source URLs, that is stronger than two results from the same engine
5. **Treat disagreement as investigation trigger** — if engines disagree, do not average; investigate why

Recommended pairings for maximum index diversity:

| Pair | Index Diversity | Best For |
|------|----------------|----------|
| brave-search + duckduckgo | High (different indices) | General verification |
| brave-search + exa | High (keyword vs semantic) | Technical topics |
| exa + tavily | Medium (both AI-optimized) | Deep research queries |
| g-search + duckduckgo | High (Google vs Bing-based) | Broad coverage |

## Degraded Mode Fallback Table

When tools are unavailable, apply confidence ceilings and use fallbacks. Check availability during Wave 0 by probing each tool with a trivial query.

| Tool Unavailable | Confidence Ceiling | Fallback | Notes |
|-----------------|-------------------|----------|-------|
| context7 | 0.6 max | brave-search for library docs; cite general URLs | Cannot verify exact API signatures |
| deepwiki | 0.6 max | repomix for code-level analysis; brave-search for repo info | Loses architectural context |
| brave-search | 0.5 max | duckduckgo or exa for web search | Reduced index coverage |
| All web search (brave + duckduckgo + exa + g-search + tavily) | 0.4 max | context7/deepwiki for library-specific only | Cannot verify current events |
| arxiv + semantic-scholar | 0.5 max | brave-search for academic topics; PubMed if biomedical | Loses citation graph analysis |
| PubMed | 0.6 max | semantic-scholar + brave-search for biomedical | Loses full-text access |
| fetcher + trafilatura | 0.5 max | brave-search snippets only; skip deep reads | Cannot extract full page content |
| docling | 0.5 max | trafilatura for HTML; skip PDF analysis | Cannot parse PDFs or tables |
| package-version | 0.6 max | brave-search + fetcher for registry lookups | Manual version checking |
| wayback | 0.6 max | brave-search cache; note historical data unavailable | Cannot access deleted content |
| All research tools | 0.4 max | LLM knowledge only; label ALL findings "unverified" | Report degraded mode in header |

## Thinking MCP Integration

Use thinking MCPs at specific pipeline stages for structured reasoning.

| Thinking Tool | Wave | Use When |
|--------------|------|----------|
| think-strategies | Wave 0 | Complex question decomposition; selecting research strategy for ambiguous queries |
| cascade-thinking | Wave 2 | Multi-perspective analysis of complex or contradictory findings from Wave 1 |
| structured-thinking | Waves 2-3 | Tracking evidence chains across sources; managing contradictions; revising prior conclusions |

**Selection heuristic:**
- Query has 3+ valid decomposition paths → think-strategies
- Findings from Wave 1 conflict or require nuanced interpretation → cascade-thinking
- Evidence chain spans 4+ sources with dependencies → structured-thinking
- Multiple tools applicable → prefer structured-thinking for its revision capability
