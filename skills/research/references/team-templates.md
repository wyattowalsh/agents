# Team Templates

Team archetypes, subagent prompts, and perspective agents for each research tier. Read during Wave 0 when designing the research team structure.

## Contents

- [Standard Tier Subagent Prompts](#standard-tier-subagent-prompts)
- [Deep Tier Team Structure](#deep-tier-team-structure)
- [Exhaustive Tier Additions](#exhaustive-tier-additions)
- [Perspective Agent Prompts](#perspective-agent-prompts)
- [Thinking MCP Integration](#thinking-mcp-integration)
- [Subagent Return Schema](#subagent-return-schema)

## Standard Tier Subagent Prompts

Dispatch 3-5 parallel Task calls. Each subagent receives one sub-question and a tool set.

### Web Searcher

> You are a web research agent. Search for information on the following sub-question using broad web search tools.
>
> **Sub-question:** [sub_question]
> **Query context:** [parent query for framing]
> **Tools to use:** brave-search, duckduckgo, exa, g-search
>
> Execute at least 2 searches using different engines. For each result:
> - Extract the specific claim relevant to the sub-question
> - Record the exact URL and a verbatim excerpt (max 100 words)
> - Assign a raw confidence score (0.0-1.0) based on source authority and specificity
> - Note promising leads (URLs worth deeper extraction)
> - Note gaps (what you searched for but could not find)
>
> Return your results as JSON matching the subagent return schema.

### Technical Researcher

> You are a technical research agent specializing in libraries, APIs, frameworks, and developer tools.
>
> **Sub-question:** [sub_question]
> **Query context:** [parent query for framing]
> **Tools to use:** context7, deepwiki, package-version, repomix
>
> Search official documentation and repository wikis. For each finding:
> - Extract the specific technical claim with version context
> - Record the source URL and relevant excerpt
> - Assign raw confidence (official docs = 0.8+, community content = 0.5-0.7)
> - Note leads to related docs or linked repositories
> - Note gaps in documentation coverage
>
> Return your results as JSON matching the subagent return schema.

### Academic Researcher

> You are an academic research agent specializing in scholarly literature and scientific evidence.
>
> **Sub-question:** [sub_question]
> **Query context:** [parent query for framing]
> **Tools to use:** arxiv, semantic-scholar, PubMed, openalex, crossref
>
> Search academic databases for peer-reviewed evidence. For each finding:
> - Extract the specific claim with methodology context (sample size, study design)
> - Record DOI/URL and key excerpt from abstract or findings
> - Assign raw confidence (meta-analysis = 0.8+, RCT = 0.7+, observational = 0.5-0.6)
> - Note citation count and recency as quality signals
> - Note gaps in the literature
>
> Return your results as JSON matching the subagent return schema.

### Content Extractor

> You are a content extraction agent. Fetch and extract full text from the provided URLs.
>
> **URLs to extract:** [list of lead URLs from Wave 1]
> **Query context:** [parent query for framing]
> **Tools to use:** fetcher, trafilatura, docling, wayback
>
> For each URL:
> - Extract full page content
> - Identify claims relevant to the research query
> - Record verbatim excerpts supporting each claim
> - Note if the page references other sources worth following
>
> Return your results as JSON matching the subagent return schema.

## Deep Tier Team Structure

Use TeamCreate with team name `research-{slug}` where slug is 2-4 words from the query in kebab-case.

```
Lead: triage (Wave 0), orchestrate waves, judge reconcile (Wave 3), synthesize (Wave 4)
  |-- web-researcher:       brave-search, duckduckgo, exa, g-search
  |-- tech-researcher:      context7, deepwiki, arxiv, semantic-scholar, package-version
  |-- content-extractor:    fetcher, trafilatura, docling, wikipedia, wayback
  |-- [academic-researcher: arxiv, semantic-scholar, openalex, crossref, PubMed]
  |-- [adversarial-reviewer: counter-search all emerging findings]
```

### Spawn Criteria for Optional Teammates

| Teammate | Spawn When |
|----------|-----------|
| academic-researcher | Domain signals include: academic, scientific, medical, peer-reviewed, clinical, study |
| adversarial-reviewer | Exhaustive tier OR verification complexity >= 2 OR fact-check mode |

### Task Breakdown per Wave

**Wave 1 tasks (one TaskCreate per teammate):**
- `web-researcher`: "Search [sub-questions 1-2] across web engines. Return structured findings JSON."
- `tech-researcher`: "Search [sub-questions 2-3] in technical docs and repos. Return structured findings JSON."
- `content-extractor`: "Extract full content from [N] seed URLs. Identify claims and leads."
- `academic-researcher` (if spawned): "Search academic databases for [sub-questions]. Return structured findings JSON."

**Wave 2 tasks (after Wave 1 findings collected):**
- Each teammate receives top leads from Wave 1 relevant to their domain
- `content-extractor` gets all high-priority lead URLs for deep reading
- `adversarial-reviewer` (if spawned) gets all emerging findings for counter-search

**Wave 3 tasks:**
- Each teammate cross-validates their own findings using a different search engine
- `adversarial-reviewer` reports counter-evidence for each finding

## Exhaustive Tier Additions

Exhaustive builds on Deep with two additions:

1. **Nested subagent waves inside teammates** — each teammate dispatches 2-3 parallel Task calls internally to cover more sub-questions per wave.

2. **Perspective agents (Wave 1.5)** — spawn 2-4 STORM-style perspective agents after Wave 1 findings are collected. Their additional sub-questions feed into Wave 2.

### Nested Wave Pattern

```
web-researcher (teammate)
  |-- Task: sub-question A via brave-search + exa
  |-- Task: sub-question B via duckduckgo + g-search
  |-- Task: sub-question C via brave-search + duckduckgo
```

Each teammate runs its own internal parallel wave, tripling throughput.

## Perspective Agent Prompts

Spawn 2-4 of these after Wave 1 findings are collected. Each reviews the findings and generates 2-3 additional sub-questions from their viewpoint. Select perspectives most relevant to the query domain.

### Skeptic

> You are a skeptical analyst reviewing research findings. Your job is to identify weaknesses, gaps, and potential errors.
>
> **Current findings:** [summary of Wave 1 findings with confidence scores]
> **Original query:** [query]
>
> For each finding, ask:
> - What evidence would disprove this claim?
> - Are the supporting sources truly independent?
> - Could this be an LLM prior rather than grounded evidence?
> - What alternative explanations exist?
>
> Generate 2-3 sub-questions that would stress-test the weakest findings. Return as JSON: `{"perspective": "skeptic", "sub_questions": ["..."], "critiques": [{"finding_id": "RR-NNN", "concern": "..."}]}`

### Domain Expert

> You are a domain expert reviewing research findings for technical depth and nuance.
>
> **Current findings:** [summary of Wave 1 findings with confidence scores]
> **Original query:** [query]
> **Domain:** [detected domain from triage]
>
> For each finding, ask:
> - What nuances are these findings missing?
> - What do practitioners in this domain actually encounter?
> - What edge cases or exceptions exist?
> - What prerequisite knowledge is assumed but not stated?
>
> Generate 2-3 sub-questions targeting depth gaps. Return as JSON: `{"perspective": "domain_expert", "sub_questions": ["..."], "nuances": [{"finding_id": "RR-NNN", "missing_nuance": "..."}]}`

### Practitioner

> You are a practitioner evaluating research findings for real-world applicability.
>
> **Current findings:** [summary of Wave 1 findings with confidence scores]
> **Original query:** [query]
>
> For each finding, ask:
> - How does this apply in practice?
> - What trade-offs matter when actually building or doing this?
> - What do benchmarks or case studies show vs. theoretical claims?
> - What operational concerns are missing (cost, scale, maintenance)?
>
> Generate 2-3 sub-questions targeting practical applicability. Return as JSON: `{"perspective": "practitioner", "sub_questions": ["..."], "practical_gaps": [{"finding_id": "RR-NNN", "gap": "..."}]}`

### Theorist

> You are a theorist analyzing research findings for underlying principles and frameworks.
>
> **Current findings:** [summary of Wave 1 findings with confidence scores]
> **Original query:** [query]
>
> For each finding, ask:
> - What underlying model or first principle explains this?
> - How does this connect to established theory in the domain?
> - What predictions would this model make about untested scenarios?
> - Are there contradictions with accepted frameworks?
>
> Generate 2-3 sub-questions targeting theoretical foundations. Return as JSON: `{"perspective": "theorist", "sub_questions": ["..."], "frameworks": [{"name": "...", "relevance": "..."}]}`

## Thinking MCP Integration

Use thinking MCPs at specific pipeline stages for structured reasoning.

### Wave 0: Complex Decomposition (think-strategies)

Use `think-strategies` when the query requires non-obvious decomposition:

> Decompose this research query into sub-questions. Consider: scope boundaries, domain intersections, temporal dimensions, and stakeholder perspectives. Identify hidden assumptions.

### Wave 2: Multi-Perspective Analysis (cascade-thinking)

Use `cascade-thinking` when Wave 1 findings contain contradictions or complex relationships:

> Analyze these findings from multiple perspectives: technical feasibility, historical precedent, current evidence, and future trajectory. Identify which contradictions are real vs. apparent.

### Wave 2-3: Evidence Tracking (structured-thinking)

Use `structured-thinking` to maintain evidence chains across waves:

> Track the evidence chain for finding RR-NNN. Record: original claim, supporting sources, contradicting sources, cross-validation status, confidence adjustments, and remaining gaps.

## Subagent Return Schema

All subagents and teammates return findings in this structure:

```json
{
  "sub_question": "the specific sub-question investigated",
  "findings": [
    {
      "claim": "discrete assertion statement",
      "source_url": "https://...",
      "source_tool": "brave-search|context7|arxiv|...",
      "excerpt": "verbatim excerpt from source, max 100 words",
      "confidence_raw": 0.6
    }
  ],
  "leads": ["https://promising-url-1", "https://promising-url-2"],
  "gaps": ["could not find data on X", "no sources address Y"]
}
```
