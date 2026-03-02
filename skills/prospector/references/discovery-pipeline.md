# Discovery Pipeline

Full wave protocols, subagent prompts, signal extraction, clustering heuristics, and error handling for the prospector discovery engine.

## Contents

- [Wave 0: Triage](#wave-0-triage)
- [Free-Roam Meta-Queries](#free-roam-meta-queries)
- [Free-Roam Clustering Heuristic](#free-roam-clustering-heuristic)
- [Wave 1: Signal Discovery](#wave-1-signal-discovery)
- [Subagent Prompt Templates](#subagent-prompt-templates)
- [Signal Extraction Prompt](#signal-extraction-prompt)
- [Wave 1 Return Schema](#wave-1-return-schema)
- [Wave 2: Opportunity Crystallization](#wave-2-opportunity-crystallization)
- [Clustering Prompt](#clustering-prompt)
- [Wave 2 Output Schema](#wave-2-output-schema)
- [Wave 3: Validation](#wave-3-validation)
- [Wave 3 Subagent Prompt](#wave-3-subagent-prompt)
- [Wave 3 Return Schema](#wave-3-return-schema)
- [Wave 4: Synthesis](#wave-4-synthesis)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

---

## Wave 0: Triage

Execute inline. Never parallelize Wave 0 — it determines the shape of all subsequent waves.

### Steps

1. Run `signal-scanner.py "$ARGUMENTS"` for deterministic pre-scan of the seed query
2. Load builder profile from DB via `db-store.py profile-get` (skip if none exists)
3. Probe tool availability by checking which MCP tools respond:
   - Search: `brave_web_search`, `tavily_search`, `duckduckgo-search`, `WebSearch`
   - Deep-read: `fetch_markdown` (fetcher), `fetch_and_extract` (trafilatura), `fetch_markdown` (fetch), `WebFetch`
   - Knowledge: `context7`, `deepwiki`
4. Select available tools per source category (see `data-sources.md` for full mapping)
5. **Seeded mode:** Decompose seed into 3-5 search angles per source category
6. **Free-roam mode:** Execute meta-queries (see below), cluster results, select 3-5 ad-hoc seeds
7. Check for interrupted sessions: `db-store.py list-sessions --status in_progress`
   - If match found for same seed, offer to resume from last completed wave
8. Present triage to user:
   ```
   I'll scan [N] source categories using [tools].
   Estimated [X] search queries, [Y] deep reads.
   [If free-roam: "[N] meta-queries → cluster → 3-5 seeds"]
   [If profile loaded: "Adjusting for your profile: [tech stack], [time budget]"]
   Proceed?
   ```
9. User approves or adjusts scope

### Decision Points

| Condition | Action |
|-----------|--------|
| No search tools available | Abort with error: "No search tools accessible" |
| No deep-read tools available | Warn: "Operating in degraded mode." Set `degraded = true` |
| Profile loaded | Pass to Wave 2 for triage adjustments |
| Interrupted session found | Offer resume: load existing data, continue from Wave N+1 |
| User adjusts scope | Re-run decomposition with adjusted parameters |

### Seeded Decomposition Example

For seed "developer tools for AI agents": Community → frustrations, missing tools, pain points. Market → market size, platform pricing, trends. Technical → GitHub trending, new SDKs, orchestration libraries. SEO → search volume gaps, keyword opportunities. Competitor → LangChain alternatives, framework comparisons.

---

## Free-Roam Meta-Queries

Use these curated queries when no seed is provided. Each targets a different signal pattern. Execute all in parallel via search tools.

### Pain and Frustration Signals

```
"looking for tool to" site:reddit.com
"wish there was a" site:reddit.com OR site:news.ycombinator.com
"frustrated with" SaaS site:reddit.com
"anyone know a tool that" site:reddit.com 2026
"I've been manually" site:reddit.com OR site:indiehackers.com
```

### Market Gap Signals

```
"shutting down" OR "end of life" SaaS 2026
"built an internal tool" site:indiehackers.com
"there's no good" site:news.ycombinator.com
"why hasn't someone built" site:reddit.com OR site:news.ycombinator.com
```

### Trending Signals

```
trending "Show HN" site:news.ycombinator.com
"Product Hunt" new launches this week
"just launched" site:indiehackers.com 2026
```

### Expansion Signals

```
"new API" OR "just released API" site:news.ycombinator.com
"now supports" integration site:producthunt.com 2026
```

Minimum: execute 10 of these queries. Maximum: all 14.

---

## Free-Roam Clustering Heuristic

After meta-query results return, the LLM clusters raw signals into thematic groups.

### Process

1. Collect all results from meta-queries (typically 30-80 raw snippets)
2. Feed to clustering prompt (below) along with builder profile if available
3. LLM groups signals by theme: same unmet need, same frustrated workflow, same market gap
4. Select top 3-5 clusters based on:
   - **Signal density:** More independent signals in a cluster = higher priority
   - **Recency:** Clusters with signals from the last 3 months rank higher
   - **Payment indicators:** Any mention of willingness to pay elevates a cluster
   - **Specificity:** "I need X for Y" beats "something better than Z"
5. Each selected cluster becomes an ad-hoc seed
6. Enter normal seeded pipeline for each ad-hoc seed

### Clustering Prompt

```
You are analyzing [N] raw signals from a broad scan of communities,
markets, and trending sources. No specific niche was provided — your
job is to find the most promising opportunity clusters.

Group related signals by theme. Signals belong together when they:
- Reference the same unmet need or frustration
- Describe the same manual workflow
- Mention the same product gap or dying product
- Target the same user persona

For each cluster, provide:
{
  "theme": "short descriptive label",
  "signal_count": N,
  "top_signals": [3-5 most representative signal snippets],
  "recency": "all 2026|mixed|mostly older",
  "payment_indicators": true/false,
  "specificity": "high|medium|low",
  "suggested_seed": "the search seed to use for seeded discovery"
}

Return 5-8 clusters ranked by promise. Target the top 3-5 for
further investigation.
```

---

## Wave 1: Signal Discovery

Dispatch one subagent per source category. All subagents run in parallel. Each executes a two-stage architecture:

- **Stage A (Search):** Use search tools to find relevant threads, discussions, reviews
- **Stage B (Deep Read):** Use fetcher/trafilatura to extract full page text from top 3-5 URLs

**5 source categories:** Community (Reddit, HN, IndieHackers), Market (G2, Capterra, trends), Technical (GitHub, npm, PyPI, SO), SEO (keyword gaps, search intents), Competitor (product pages, reviews, shutdowns).

Dispatch one TaskCreate per category. Stagger by 500ms. Each subagent uses the prompt template and query set for its category (below).

---

## Subagent Prompt Templates

All subagent prompts share this structure. Replace `[ROLE]`, `[FOCUS]`, and query slots per category.

> You are a [ROLE] scanner. Search for [FOCUS] related to [seed_query].
>
> **Seed:** [seed_query] | **Angles:** [angles from Wave 0]
> **Tools:** [available search tool] for search, [available deep-read tool] for extraction
>
> **Stage A — Search (max 4 queries):** Execute the 4 queries below.
> **Stage B — Deep Read (max 5 URLs):** Select top 3-5 URLs, extract full text, run signal extraction prompt.
> **Return:** JSON matching Wave 1 return schema.

### Per-Category Query Sets

| Category | Role | Focus | Query 1 | Query 2 | Query 3 | Query 4 |
|----------|------|-------|---------|---------|---------|---------|
| Community | community signal | pain points, feature requests | `"[seed] frustration" site:reddit.com` | `"[seed] wish there was" site:reddit.com OR site:news.ycombinator.com` | `"[seed] looking for tool" site:reddit.com` | `"[seed] manual process" site:indiehackers.com` |
| Market | market intelligence | market sizing, pricing, trends | `"[seed] market size 2026"` | `"[seed] pricing" OR "[seed] plans"` | `"[seed] trends" OR "[seed] growth"` | `"[seed] reviews" site:g2.com OR site:capterra.com` |
| Technical | technical signal | rising frameworks, new APIs, library gaps | `"[seed] github trending" OR "[seed] new release"` | `"[seed] npm" OR "[seed] pypi" new` | `"[seed] stack overflow" unanswered` | `"[seed] API" new OR "just launched"` |
| SEO | SEO gap | keyword opportunities, content gaps | `"[seed] tool" OR "[seed] software"` | `"[seed] alternative to"` | `"[seed] how to" OR "[seed] tutorial"` | `"[seed] vs"` |
| Competitor | competitor intelligence | existing solutions, weaknesses, shutdowns | `"[seed] tool" OR "[seed] app"` | `"[seed] alternative" OR "[seed] competitor"` | `"[seed] review" negative OR "switching from"` | `"[seed] shutting down" OR "[seed] pivot"` |

### Stage B Notes Per Category

- **Community:** Fetch full threads — pain signals often in comments, not just posts
- **Market:** Note specific numbers: MRR, pricing tiers, user counts, growth rates
- **Technical:** Note stars, download counts, open issues, last commit date
- **SEO:** Note quality, recency, and gaps in existing content
- **Competitor:** Note pricing, feature gaps, user complaints, churn indicators

---

## Signal Extraction Prompt

Run after deep-reading each page. Every subagent uses this during Stage B.

```
Analyzing a page about [niche]. Extract every instance where a user:
- Expresses frustration with an existing tool/process
- Requests a tool that does not exist
- Describes a manual workflow they wish were automated
- Mentions willingness to pay for a solution
- Discusses a product shutting down/pivoting
- Reports terrible UX, rising trend with few tools, or building an internal tool

Per signal: {"quote": "exact text (never invent)", "signal_type": "pain_no_solution|
dying_product|platform_expansion|rising_trend|terrible_ux|manual_workflow",
"intensity": "strong|moderate|weak", "context": "who/where/engagement",
"payment_signal": true/false, "source_url": "...", "source_tool": "search → read"}

Intensity: strong = specific pain with numbers + high engagement (50+ upvotes) or payment signal.
moderate = clear frustration, 10-50 upvotes. weak = vague, <10 upvotes.
Never invent quotes. Empty array if no signals found.
```

---

## Wave 1 Return Schema

```json
{
  "source_category": "community|market|technical|seo|competitor",
  "seed_query": "...", "urls_searched": N, "urls_deep_read": N,
  "signals": [{"quote": "exact text", "signal_type": "...", "intensity": "strong|moderate|weak",
    "context": "who/where/engagement", "payment_signal": false, "source_url": "...", "source_tool": "search → read"}],
  "market_data": {"pricing_found": ["..."], "user_counts": ["..."], "trend_data": ["..."]},
  "tools_used": ["..."], "gaps": ["..."], "degraded": false
}
```

All fields required except `market_data` (only from market/competitor scanners). `degraded` is `true` when deep-read was unavailable.

---

## Wave 2: Opportunity Crystallization

Execute inline (not parallelized). The LLM receives all signals from all Wave 1 subagents and clusters them into opportunity candidates.

### Input Assembly

1. Concatenate all `signals` arrays from Wave 1 subagent returns
2. Include `market_data` from market and competitor scanners
3. Include `gaps` for context on blind spots
4. Include builder profile if loaded in Wave 0

### Process

1. Feed signals + market data to clustering prompt (below)
2. LLM produces 8-15 candidate opportunities
3. Run `triage-validator.py` on each candidate to enforce hard rules and assign tiers
4. Run `db-store.py dedup-check --title "..." --niche "..."` on each candidate
5. If dedup finds a match (similarity > 0.7), present to LLM: "Merge with existing OPP-XXXX or create new?"
6. Save Wave 2 results to DB via `db-store.py save-opportunity` (crash recovery)
7. Select top 8-10 candidates for Wave 3 validation

---

## Clustering Prompt

```
You have [N] signals from [M] source categories about [niche/seed].
[If builder profile: "Builder profile: [tech_stack], [time_budget]h/week, [revenue_goal] MRR target"]

Group related signals into candidate opportunities. Signals about the same unmet need,
frustrated workflow, or market gap belong together.

Per candidate, provide: title (5-8 words), one_liner, niche (2-3 words), primary_signal
(pain_no_solution|dying_product|platform_expansion|rising_trend|terrible_ux|manual_workflow),
signal_count, signals array, initial_triage (6 dimensions: strong|moderate|weak each),
triage_reasoning (per dimension), mvp_estimate (days, tech_stack, monthly_cost),
why_might_be_wrong (2+ reasons).

Target 8-15 candidates. EXCLUDE: single weak signal, generic ideas without pain evidence.
INCLUDE: candidates with competition (competition validates demand).
Every candidate MUST have "why_might_be_wrong" with at least 2 reasons.
```

---

## Wave 2 Output Schema

```json
{
  "seed_query": "...",
  "total_signals_received": N,
  "candidates": [{"title": "...", "one_liner": "...", "niche": "...", "primary_signal": "...",
    "signal_count": N, "signals": ["..."], "initial_triage": {"bootstrappability": "strong", "...": "..."},
    "triage_reasoning": {"...": "..."}, "mvp_estimate": {"days": N, "tech_stack": "...", "monthly_cost": "..."},
    "why_might_be_wrong": ["...", "..."]}],
  "excluded_count": N,
  "exclusion_reasons": ["..."]
}
```

---

## Wave 3: Validation

Dispatch one subagent per top candidate (8-10 candidates). All run in parallel. Each subagent performs counter-evidence search and freshness/independence checks.

### Validation Requirements

For each candidate, the validation subagent must:

1. **Search for existing solutions:** Find direct competitors
2. **Search for counter-evidence:** Find reasons this might fail
3. **Check freshness:** Verify signal sources are from the last 6 months
4. **Check independence:** Verify signals come from different communities

Minimum 2 counter-evidence searches per candidate.

---

## Wave 3 Subagent Prompt

> You are a validation agent performing counter-evidence search for a
> microSaaS opportunity candidate.
>
> **Opportunity:** [title]
> **One-liner:** [one_liner]
> **Niche:** [niche]
> **Claimed signals:** [signal_count] signals from [sources]
> **Initial triage:** [initial_triage summary]
> **Tools:** [available search tool] for search, [available deep-read tool] for extraction
>
> Execute these validation searches (max 4 search + 3 deep reads):
>
> 1. **Existing solutions:** Search "[title] alternative" and "[niche] tool"
>    List every competitor found with pricing and feature summary.
>
> 2. **Counter-evidence:** Search "why [niche] failed" and "[similar product] shutdown"
>    Find specific reasons why this opportunity might not work.
>
> 3. **Freshness check:** Review the dates on the original signal sources.
>    Are they from the last 6 months? Flag stale signals.
>
> 4. **Independence check:** Are the signals from different communities?
>    Flag if 2+ signals come from the same subreddit or thread.
>
> Based on your findings, recommend triage adjustments:
> - If strong incumbent found: recommend competition → weak
> - If signals are stale (>6 months): recommend freshness cap
> - If signals lack independence: recommend PMF downgrade
> - If no counter-evidence found: note this as a positive signal
>
> Return results as JSON matching the Wave 3 return schema.

---

## Wave 3 Return Schema

```json
{
  "opportunity_title": "...",
  "existing_solutions": [{"name": "...", "pricing": "...", "relevance": "...", "source_url": "..."}],
  "counter_evidence": [{"claim": "...", "source": "...", "severity": "high|medium|low", "source_url": "..."}],
  "freshness_check": {"all_fresh": true, "stale_signals": [], "freshest": "YYYY-MM-DD", "oldest": "YYYY-MM-DD"},
  "independence_check": {"independent": true, "communities_represented": ["..."], "clustering_warning": null},
  "triage_adjustments": {"dimension": {"from": "rating", "to": "rating", "reason": "..."}},
  "validation_confidence": "high|medium|low",
  "tools_used": ["..."],
  "gaps": ["..."]
}
```

---

## Wave 4: Synthesis

Execute inline. Produces final opportunity cards and persists results.

### Steps

1. Collect all Wave 3 validation returns
2. Apply triage adjustments from each validation subagent
3. Re-run `triage-validator.py` on each candidate with adjusted ratings
4. Rank by tier (Strong > Moderate > Weak), then by signal count within tier
5. Select top 5-10 opportunities
6. Produce opportunity card for each (see `output-formats.md` for card template)
7. Save all to SQLite via `db-store.py save-opportunity`
8. Update session via `db-store.py update-session --wave-completed 4 --status complete`
9. Present cards to user
10. If any opportunity is Strong tier: "Run `/prospector evaluate OPP-XXXX` for expert panel assessment"

### Wave 4 Decision Points

| Condition | Action |
|-----------|--------|
| 0 candidates survive validation | Report "No viable opportunities found" with explanation |
| All candidates are Weak tier | Present them with caveat: "All candidates have significant weaknesses" |
| Degraded mode active | Append warning to every card: "Triage based on search snippets, not full page analysis" |
| Dedup match found | Merge with existing, update triage, note "updated from session [ID]" |
| 5+ Strong tier candidates | Unusual — warn: "High Strong count may indicate overly generous triage" |

---

## Error Handling

| Category | Scenario | Action |
|----------|----------|--------|
| Search | Single query returns 0 | Retry broader terms; if still 0, log gap, continue |
| Search | Entire source category returns 0 | Exclude category from clustering |
| Search | All categories return 0 | Abort: "No signals found for [seed]" |
| Deep-read | 404 / paywall / timeout (>30s) | Log gap, skip URL (use snippet if paywall) |
| Deep-read | Tool error | Fall to next tool in chain (see `data-sources.md`) |
| Subagent | Single timeout | Log warning, proceed with other subagents |
| Subagent | 2+ timeouts | Warn user, cap triage at Moderate |
| Subagent | All timeout | Abort: "Discovery failed" |
| Database | Not initialized | Auto-run `db-store.py init` |
| Database | Write fails | Retry once; if still fails, warn and continue in memory |
| Database | Dedup fails | Skip dedup, create new, warn about potential duplicate |

---

## Rate Limiting

**Per subagent:** Max 4 search + 5 deep reads = 9 tool calls.
**Session totals:** Wave 1 ~45 (5 subagents x 9), Wave 3 ~55 (10 candidates x ~5.5 avg), total ~100.

**Stagger:** 500ms between parallel subagent dispatches. On 429: wait 2s, retry once, then fall to next tool. Never retry more than once per tool per subagent.

See `data-sources.md` for per-tool rate limits and API-specific strategies.
