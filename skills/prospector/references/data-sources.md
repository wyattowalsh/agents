# Data Sources

Tool mapping per source category, query templates, community-specific patterns, fallback chains, rate limiting, and source authority tiers.

## Contents

- [Tool Mapping](#tool-mapping)
- [Fallback Chains](#fallback-chains)
- [Query Templates](#query-templates)
- [Community-Specific Patterns](#community-specific-patterns)
- [Rate Limiting](#rate-limiting)
- [Source Authority Tiers](#source-authority-tiers)
- [Degraded Mode Table](#degraded-mode-table)
- [Tool Availability Probing](#tool-availability-probing)

---

## Tool Mapping

Map each source category to primary and fallback tools. Use MCP tool names as they appear in the tool registry.

### Search Tools

| Category | Primary Search | Fallback 1 | Fallback 2 | Fallback 3 |
|----------|---------------|------------|------------|------------|
| Community | `brave_web_search` | `tavily_search` | `search` (duckduckgo) | `WebSearch` |
| Market | `brave_web_search` | `tavily_search` | `search` (duckduckgo) | `WebSearch` |
| Technical | `brave_web_search` | `tavily_search` | `search` (duckduckgo) | `WebSearch` |
| SEO | `brave_web_search` | `tavily_search` | `search` (duckduckgo) | `WebSearch` |
| Competitor | `brave_web_search` | `tavily_search` | `search` (duckduckgo) | `WebSearch` |

### Deep-Read Tools

| Category | Primary Read | Fallback 1 | Fallback 2 | Fallback 3 |
|----------|-------------|------------|------------|------------|
| Community | `fetch_markdown` (fetcher) | `fetch_and_extract` (trafilatura) | `fetch_markdown` (fetch) | `WebFetch` |
| Market | `fetch_markdown` (fetcher) | `fetch_and_extract` (trafilatura) | `fetch_markdown` (fetch) | `WebFetch` |
| Technical | `ask_question` (deepwiki) | `query-docs` (context7) | `fetch_markdown` (fetcher) | `fetch_and_extract` (trafilatura) |
| SEO | `fetch_markdown` (fetcher) | `fetch_and_extract` (trafilatura) | `fetch_markdown` (fetch) | `WebFetch` |
| Competitor | `fetch_and_extract` (trafilatura) | `fetch_markdown` (fetcher) | `fetch_markdown` (fetch) | `WebFetch` |

### Knowledge Tools (Supplementary)

| Category | Tool | Use For |
|----------|------|---------|
| Technical | `resolve-library-id` + `query-docs` (context7) | Library documentation, API signatures |
| Technical | `read_wiki_structure` + `ask_question` (deepwiki) | GitHub repository architecture, design decisions |
| Technical | `check_npm_versions` / `check_pyproject_versions` (package-version) | Dependency freshness, download counts |

---

## Fallback Chains

### Search Fallback Chain

```
brave_web_search → tavily_search → search (duckduckgo) → WebSearch
```

Apply in order. If primary tool returns an error or is unavailable, try the next. Stop at the first tool that returns results.

### Deep-Read Fallback Chain

```
fetch_markdown (fetcher) → fetch_and_extract (trafilatura) → fetch_markdown (fetch) → WebFetch → search snippets only
```

If all deep-read tools fail for a URL:
- Use search result snippets as evidence
- Mark the signal as `"snippet_only": true`
- Do not assign `strong` intensity to snippet-only signals

### Technical Knowledge Fallback

```
context7 (query-docs) → deepwiki (ask_question) → brave_web_search for "[library] docs"
```

Use context7 first for library-specific questions. Fall to deepwiki for repository-level architecture. Fall to web search for general technical information.

---

## Query Templates

Organized by source category. Replace `[niche]` with the seed query or decomposed search angle.

### Community (6 templates)

```
1. "[niche] frustration OR complaint" site:reddit.com
2. "[niche] wish there was a tool" site:reddit.com OR site:news.ycombinator.com
3. "[niche] looking for" OR "need tool for [niche]" site:reddit.com
4. "[niche] manual process" OR "[niche] spreadsheet" site:indiehackers.com
5. "[niche] I built" OR "[niche] internal tool" site:indiehackers.com OR site:reddit.com
6. "[niche]" site:twitter.com OR site:x.com "looking for" OR "anyone know"
```

### Market (4 templates)

```
7.  "[niche] market size" OR "[niche] TAM" 2025 OR 2026
8.  "[niche] software pricing" OR "[niche] tool plans" site:g2.com OR site:capterra.com
9.  "[niche] trends" OR "[niche] growth rate" 2026
10. "[niche] industry report" OR "[niche] market analysis"
```

### Technical (4 templates)

```
11. "[niche]" site:github.com trending OR "new release"
12. "[niche] npm package" OR "[niche] pypi" new OR "just published"
13. "[niche]" site:stackoverflow.com unanswered OR "no library"
14. "[niche] API" new OR "just launched" OR "now available"
```

### SEO (3 templates)

```
15. "[niche] tool" OR "[niche] software" — analyze what currently ranks
16. "[niche] alternative to [competitor]" — find comparison opportunities
17. "how to [niche]" OR "[niche] tutorial" — find underserved search intents
```

### Competitor (4 templates)

```
18. "[niche] tool" OR "[niche] app" OR "[niche] software" best OR top
19. "[niche] alternative" OR "[niche] vs" OR "[niche] competitor"
20. "[niche] review" negative OR disappointed OR "switching from"
21. "[niche] shutting down" OR "[niche] sunset" OR "[niche] acquired"
```

### Validation (Wave 3, 4 templates)

```
22. "[opportunity title] alternative" OR "[niche] similar tool"
23. "why [niche] failed" OR "[niche] startup failure"
24. "[competitor name] roadmap" OR "[competitor name] upcoming features"
25. "[niche] crowded" OR "[niche] too many" OR "[niche] saturated"
```

---

## Community-Specific Patterns

### Reddit

- **Search pattern:** Use `site:reddit.com` in web search (Reddit's native search is unreliable)
- **Engagement signals:** Upvotes, comment count, awards visible in search snippets
- **High-value subreddits:** r/SaaS, r/startups, r/smallbusiness, r/Entrepreneur, r/webdev, r/selfhosted, r/nocode, niche-specific subreddits
- **Deep-read:** Fetch the full thread to get replies (pain signals often appear in comments, not just the post)
- **Date signals:** Reddit URLs contain timestamps; prefer posts from last 6 months

### Hacker News

- **Search pattern:** Use `site:news.ycombinator.com` or dedicated HN search APIs
- **Engagement signals:** Points, comment count. "Show HN" posts indicate builders sharing tools.
- **High-value patterns:** "Ask HN: How do you..." indicates unmet needs, "Show HN:" indicates new solutions and their reception
- **Deep-read:** HN comment threads are often more valuable than the linked article
- **Date signals:** HN URLs contain item IDs (higher = more recent)

### IndieHackers

- **Search pattern:** Use `site:indiehackers.com` in web search
- **Engagement signals:** Comments, upvotes on posts
- **High-value patterns:** "I built..." posts reveal what founders see as opportunities, "Looking for feedback" reveals demand validation attempts
- **Deep-read:** Product pages on IH contain revenue data and growth metrics
- **Date signals:** Post dates visible in search snippets

### Product Hunt

- **Search pattern:** Use `site:producthunt.com` in web search
- **Engagement signals:** Upvotes, comments, "Product of the Day" status
- **High-value patterns:** New launches show what is being built now, comment sections reveal user reactions and competitors mentioned
- **Deep-read:** Product pages contain feature lists and user comments
- **Date signals:** PH has daily launches; sort by recency

### Twitter/X

- **Search pattern:** Use `site:twitter.com OR site:x.com` in web search
- **Engagement signals:** Likes, retweets, replies
- **Limitations:** Thread content often truncated in search snippets; deep-read may be blocked
- **High-value patterns:** "I wish there was..." "Building in public" threads, "I need a tool that..."

---

## Rate Limiting

### Per-Tool Limits

| Tool | Known Rate Limit | Recommended Max/Session |
|------|-----------------|------------------------|
| `brave_web_search` | ~15 req/min (free tier) | 30 queries total |
| `tavily_search` | ~10 req/min | 15 queries total |
| `search` (duckduckgo) | ~20 req/min | 20 queries total |
| `WebSearch` | No documented limit | 10 queries total |
| `fetch_markdown` (fetcher) | No hard limit | 25 fetches total |
| `fetch_and_extract` (trafilatura) | No hard limit | 20 fetches total |
| `query-docs` (context7) | No documented limit | 5 queries total |
| `ask_question` (deepwiki) | No documented limit | 5 queries total |

### Subagent Budgets

| Wave | Subagents | Searches/Agent | Reads/Agent | Total Searches | Total Reads |
|------|-----------|---------------|-------------|---------------|-------------|
| 1 | 5 | 4 | 5 | 20 | 25 |
| 3 | 8-10 | 4 | 1-2 | 40 | 15 |
| **Total** | | | | **~60** | **~40** |

### Stagger Protocol

- Dispatch parallel subagents with 500ms delay between each
- If a 429 response is detected, wait 2 seconds before retry
- Maximum 1 retry per tool per subagent
- If retry fails, fall to next tool in fallback chain
- If all tools in chain fail, log gap and return partial results

### Politeness Rules

- Wait 500ms between consecutive fetches to the same domain
- Do not fetch more than 5 pages from the same domain in a single session
- Respect `robots.txt` implicitly (the fetch tools handle this)

---

## Source Authority Tiers

Weight evidence differently based on source quality. These tiers are used by the triage system (see `triage-system.md`) to validate signal intensity ratings.

### Tier 1: High Authority

| Source | Why High Authority |
|--------|--------------------|
| ProductHunt launch page with engagement metrics | Verified product + public reception data |
| G2/Capterra verified reviews | Verified purchaser reviews with structured ratings |
| Published pricing page | Authoritative competitive intelligence |
| GitHub repo with 100+ stars | Community-validated interest |
| Official shutdown/pivot announcement | Primary source for market gap signals |
| Industry market research report | Professional analysis with methodology |

### Tier 2: Medium Authority

| Source | Why Medium Authority |
|--------|----------------------|
| Reddit post with 50+ upvotes | Community engagement validates the signal |
| HN post on front page (50+ points) | High-quality technical community validation |
| IndieHackers post with engagement | Founder community with market awareness |
| Stack Overflow question with votes, no answer | Documented unmet need in developer community |
| Recognized tech publication analysis | Editorial standards, but may have biases |

### Tier 3: Low Authority

| Source | Why Low Authority |
|--------|-------------------|
| Reddit post with <50 upvotes | Low engagement — may be isolated opinion |
| Blog post without citations | Unverified individual perspective |
| Social media post without engagement | No community validation |
| Forum post on niche site (no metrics) | Cannot assess reach or agreement |
| LLM-generated summary without source | Not verifiable evidence |

### Authority Rules

- Strong intensity signals require Tier 1 or Tier 2 source
- Tier 3 signals alone cannot support PMF Signals = strong
- Counter-evidence from Tier 1 sources overrides Tier 2/3 positive signals
- When source tier is ambiguous, assign the lower tier

---

## Degraded Mode Table

When tools are unavailable, capabilities degrade. Check during Wave 0 and inform the user.

### Search Tool Degradation

| Tools Missing | Capability Impact | Triage Ceiling |
|---------------|-------------------|----------------|
| `brave_web_search` | Reduced search index coverage | No ceiling (use fallback) |
| `brave_web_search` + `tavily_search` | Limited to duckduckgo + WebSearch | No ceiling (two tools remain) |
| All search tools | Cannot discover signals | Abort: "No search tools available" |

### Deep-Read Tool Degradation

| Tools Missing | Capability Impact | Triage Ceiling |
|---------------|-------------------|----------------|
| `fetch_markdown` (fetcher) | Use trafilatura or fetch | No ceiling |
| All fetcher tools | Rely on search snippets only | Moderate (cap all tiers) |
| All fetcher + all search tools | No capability | Abort |

### Knowledge Tool Degradation

| Tools Missing | Capability Impact | Triage Ceiling |
|---------------|-------------------|----------------|
| `context7` | Cannot verify API docs | Technical Feasibility capped at moderate |
| `deepwiki` | Cannot analyze repos | No ceiling (use web search for repo info) |
| Both context7 + deepwiki | Limited technical assessment | Technical Feasibility capped at moderate |

### Degraded Mode Rules

1. Any tool unavailability triggers a user warning in Wave 0
2. When operating in degraded mode, add this banner to every card:
   ```
   Warning: Triage based on limited tool access ([missing tools]).
   Results may be less reliable than full-tool discovery.
   ```
3. Track `degraded: true` on the session record
4. Log which tools were missing and which fallbacks were used

---

## Tool Availability Probing

During Wave 0, probe each tool category with a trivial query to confirm availability.

### Probe Queries

| Tool | Probe Query | Expected Response |
|------|-------------|-------------------|
| `brave_web_search` | `"test query 2026"` | Search results array |
| `tavily_search` | `"test query"` | Search results |
| `fetch_markdown` (fetcher) | `"https://example.com"` | Markdown content |
| `fetch_and_extract` (trafilatura) | `"https://example.com"` | Extracted text |
| `query-docs` (context7) | Resolve a known library ID | Documentation content |
| `ask_question` (deepwiki) | Question about a known repo | Answer text |

### Probe Rules

- Probe only tools that will be used in the current session
- If probe fails, mark tool as unavailable and use fallback
- Do not retry probes — a single failure is sufficient to mark unavailable
- Record probe results for logging in the session record
