---
name: prospector
description: >-
  MicroSaaS opportunity discovery engine. Scans communities (Reddit, HN,
  IndieHackers, Twitter/X), market data (Google Trends, app stores, G2),
  technical signals (GitHub trending, npm/PyPI, Stack Overflow), SEO gaps,
  and competitor intel to surface bootstrappable microSaaS ideas. Triages
  on 6 dimensions, tracks lifecycle from discovery to launch, manages a
  web dashboard. Use when hunting for side-project ideas, scanning for
  market gaps, maintaining an opportunity pipeline, or evaluating a
  specific discovery with expert perspectives. NOT for evaluating existing
  live products (use honest-review), competitive strategy (use wargame),
  or general research (use research).
argument-hint: "<niche or keyword> [--source community|market|technical|seo|all]"
model: opus
license: MIT
metadata:
  author: wyattowalsh
  version: "1.0.0"
hooks:
  PreToolUse:
    - matcher: Edit
      hooks:
        - command: 'bash -c "echo BLOCKED: prospector is read-only — does not edit project files >&2; exit 1"'
---

# Prospector

MicroSaaS opportunity discovery engine. Surface bootstrappable ideas backed by real community signals, validated with counter-evidence, and tracked through a full lifecycle pipeline.

**Scope:** Discovery and triage of microSaaS opportunities. NOT for evaluating existing live products (use honest-review), competitive strategy or wargaming (use wargame), general-purpose research (use research), or building/coding the discovered ideas.

## Dispatch

| `$ARGUMENTS` | Action |
|---|---|
| `<niche or keyword>` | **Mine** — seeded discovery in that niche |
| `scan` / `scan --source <filter>` | **Scan** — autonomous free-roam discovery |
| `evaluate <id>` | **Evaluate** — expert panel deep assessment |
| `list [--status <s>] [--tier <t>]` | **List** — show opportunity pipeline |
| `detail <id>` | **Detail** — full opportunity card with evidence |
| `update <id> --status <s>` | **Update** — lifecycle transition |
| `dashboard` / `dashboard stop` | **Dashboard** — launch/stop the web app |
| `resume <session-id>` | **Resume** — continue interrupted session from last completed wave |
| `profile` / `profile set <json>` | **Profile** — view/edit builder profile |
| `export [json\|csv\|html]` | **Export** — export opportunities (`html` uses static template) |
| Empty | **Gallery** — mode menu, recent discoveries, pipeline summary |

**Examples:**

```
/prospector developer tools for AI agents
/prospector scan --source community
/prospector evaluate OPP-0017
/prospector list --tier strong
/prospector dashboard
```

## Reference File Index

| File | Content | Read When |
|------|---------|-----------|
| `references/discovery-pipeline.md` | Full wave protocols, subagent prompts, signal extraction, clustering, free-roam meta-queries, return schemas | Wave 0 (planning), Wave 1-2 (executing) |
| `references/triage-system.md` | 6-dimension rubric, tier assignment rules, hard caps, profile adjustments, counter-evidence requirements | Wave 2 (initial triage), Wave 3 (validation) |
| `references/expert-panel.md` | 4 persona definitions, 3-round protocol, tier adjustment triggers, go/no-go criteria | Evaluate mode only |
| `references/data-sources.md` | Tool mapping per source category, fallback chains, query templates, rate limiting | Wave 0 (tool selection), Wave 1 (querying) |
| `references/output-formats.md` | Card template, export formats, dashboard API spec, lifecycle definitions, static dashboard data contract | Wave 4 (output), Export/Dashboard modes |

Do not load all references at once. Load per the "Read When" column.

## Discovery Pipeline (Mine / Scan)

### Wave 0: Triage (inline, never parallelized)

0. Check for interrupted sessions: `uv run python skills/prospector/scripts/db-store.py list-sessions --status in_progress`
   If a session matches the same seed: "Found interrupted session [ID] at Wave N. Resume from Wave N+1, or start fresh? [Resume / Fresh]"
1. Run `uv run python skills/prospector/scripts/signal-scanner.py "$ARGUMENTS"` for deterministic pre-scan
2. Load builder profile from DB via `uv run python skills/prospector/scripts/db-store.py profile-get` (if exists)
3. Probe tool availability: check which of brave-search, fetcher, trafilatura, tavily are accessible
4. **Seeded mode:** Decompose seed into 3-5 search angles per source category
5. **Free-roam mode:** Use meta-queries to discover trending pain points, then cluster into 3-5 ad-hoc seeds before entering the normal pipeline

**Free-roam meta-queries** (curated set, no seed needed):
```
"looking for tool to" site:reddit.com
"wish there was a" site:reddit.com OR site:news.ycombinator.com
"frustrated with" SaaS site:reddit.com
"shutting down" OR "end of life" SaaS 2026
"built an internal tool" site:indiehackers.com
trending Show HN
Product Hunt new launches this week
```

After meta-query results return, cluster raw signals by theme, select 3-5 most promising clusters, each becomes an ad-hoc seed for the normal pipeline.

6. Present triage to user: "I'll scan [N] source categories using [tools]. Estimated [X] search queries, [Y] deep reads. Proceed?"
7. User approves or adjusts

### Wave 1: Signal Discovery (parallel — one subagent per source category)

Load `references/discovery-pipeline.md` and `references/data-sources.md`.

Two-stage architecture per subagent:
- **Stage A (Search):** Use search tools to find relevant threads, discussions, reviews
- **Stage B (Deep Read):** Use fetcher/trafilatura to extract full page text from top 3-5 URLs

**Signal extraction prompt** (used by each subagent after deep-reading a page):
```
You are analyzing a community discussion / review / article about [niche].
Extract every instance where a user:
- Expresses frustration with an existing tool or process
- Requests a feature or tool that does not exist
- Describes a manual workflow they wish were automated
- Mentions willingness to pay for a solution
- Discusses a product shutting down or pivoting away

For each signal, output JSON:
{"quote": "exact text", "signal_type": "pain_no_solution|dying_product|platform_expansion|
rising_trend|terrible_ux|manual_workflow", "intensity": "strong|moderate|weak",
"context": "who is saying this and why", "payment_signal": true/false}

Only extract signals with actual textual evidence. Never invent quotes.
If no signals found, return empty array.
```

Max queries per subagent: 4 search + 5 deep reads = 9 tool calls. Total across 5 categories: ~45 tool calls max.

### Wave 2: Opportunity Crystallization (inline LLM work)

Receive all signals from all subagents. Cluster related signals into candidate opportunities. For each candidate, assign qualitative triage ratings (strong/moderate/weak) on 6 dimensions with reasoning.

Target 8-15 candidates. Exclude candidates with only 1 weak signal.

Run `uv run python skills/prospector/scripts/triage-validator.py` on each candidate to enforce hard rules and compute tier. Then dedup against existing DB via `uv run python skills/prospector/scripts/db-store.py dedup-check`.

Save Wave 2 results to DB: `uv run python skills/prospector/scripts/db-store.py save-opportunity`.

### Wave 3: Validation (parallel — one subagent per top candidate)

Select top 8-10 from Wave 2 by: tier (Strong first, then Moderate), then by signal_count descending. Include Weak-tier candidates only if fewer than 8 total candidates exist.

For each of the top 8-10 candidates after Wave 2:
- Search for existing solutions: "[title] alternative", "[niche] tool"
- Search for counter-evidence: "why [niche] failed", "[similar product] shutdown"
- Validate demand freshness: are signal sources from the last 6 months?
- Check source independence: are signals from different communities?

Apply Wave 3 adjustments to triage ratings. Re-run `triage-validator.py` for final tier.

### Wave 4: Synthesis (inline)

1. Rank by tier (Strong > Moderate > Weak), then by signal count
2. Select top 5-10
3. Produce opportunity card for each (see card format below)
4. Save all to SQLite via `db-store.py save-opportunity`
5. Save session via `db-store.py save-session`
6. If any opportunity is Strong tier: "Run `/prospector evaluate OPP-XXXX` for expert panel assessment"

## Opportunity Card Format

Every card includes these sections. Load `references/output-formats.md` for full template.

```markdown
## OPP-0017: AI-Powered Meeting Notes -> Slack

**Pitch:** Auto-transcribe meetings, extract action items, post to Slack channels.
**Niche:** Productivity / Remote Work | **Signal:** Manual Workflow
**Discovered:** 2026-03-01 | **Status:** discovered | **Tier:** Strong

### Triage
| Dimension | Rating | Reasoning |
|-----------|--------|-----------|
| Bootstrappability | strong | Whisper API + Slack Bot SDK, ~$20/mo infra, MVP in 5-7 days |
| PMF Signals | strong | 3 independent sources, 47 upvotes on r/remotework complaint |
| Competition | moderate | Otter.ai exists but no native Slack; Fireflies enterprise-only |
| Revenue Potential | moderate | $9-15/mo, TAM ~750K paid Slack workspaces |
| Technical Feasibility | strong | Python + well-documented APIs, builder's stack match |
| Moat Potential | weak | API wrapper, easily replicated, no data network effect |

### Evidence
1. r/remotework (2026-02-14): "I spend 30 min after every standup typing up
   what we discussed into Slack." [53 upvotes] — brave_web_search -> fetch_markdown
2. HN (2026-02-20): "Otter.ai is too expensive for our 5-person startup"
   — brave_web_search -> trafilatura
3. G2 (2026-01-30): "2/5 stars — Slack integration frequently fails"
   — brave_web_search -> fetch_markdown

### Why This Might Be Wrong
- **Incumbent risk:** Otter.ai could ship native Slack integration any quarter
- **API dependency:** Whisper API pricing could change
- **Market ceiling:** Slack-only limits TAM; Teams/Discord unreachable
- **Echo chamber:** 2 of 3 Reddit sources from same subreddit

### MVP Estimate
5-7 days | Python, Whisper API, Slack Bot SDK, SQLite | ~$20/mo hosting
```

## Triage System (overview)

6 dimensions scored qualitatively by the LLM in Wave 2, validated by `triage-validator.py`. Load `references/triage-system.md` for full rubric.

| Dimension | Weight | What "strong" means |
|-----------|--------|---------------------|
| Bootstrappability | High | Solo-dev MVP in <2 weeks, <$100/mo infra, no compliance |
| PMF Signals | High | 2+ independent pain signals, payment evidence present |
| Competition | Medium | No direct competitor OR only weak/expensive ones |
| Revenue Potential | Medium | Realistic $5K+ MRR ceiling, pricing power exists |
| Technical Feasibility | Medium | Standard web stack, well-documented APIs |
| Moat Potential | Low | Data/network effects, integration lock-in possible |

**Tier assignment (by triage-validator.py):**
- **Strong:** 4+ dimensions strong, 0 weak. Or 3 strong including PMF Signals, 0-1 weak.
- **Moderate:** 2-3 dimensions strong, <=2 weak. No critical weakness in PMF + Bootstrappability.
- **Weak:** <=1 strong, or PMF Signals is weak, or Bootstrappability is weak.

**Hard rules enforced by script:**
- Single-signal opportunities cannot be Strong (cap at Moderate)
- Stale signals only (>6 months) cap at Weak
- Strong incumbent found: Competition forced to weak

**Gold signal types:**
1. Pain + No Solution — complaints with no good existing tool
2. Dying/Pivoting Product Gap — product shutting down, stranded users
3. Platform Expansion — new API/platform creates tooling gaps
4. Rising Trend + Low Competition — growing usage, few competitors
5. Terrible UX Ripe for Disruption — negative reviews citing UX
6. Manual Workflow Begging for Automation — "I spend X hours" patterns

## Tool Fallback Chain

For deep-read (Stage B of Wave 1):
```
fetcher (fetch_markdown) -> trafilatura (fetch_and_extract) -> fetch MCP (fetch_markdown) -> WebFetch -> search snippets only
```
If no deep-read tool is available:
- Warn user: "Operating in degraded mode — triage based on search snippets only"
- Cap all triage tiers at Moderate maximum
- Add warning to every card

For search:
```
brave_web_search -> tavily_search -> duckduckgo-search -> WebSearch
```

## Expert Panel (Evaluate mode)

Triggered by `/prospector evaluate OPP-XXXX`. Load `references/expert-panel.md`.

**3-round roundtable protocol:**
- **Round 1 — Individual Assessment:** Each of 4 personas gives 150-word verdict
- **Round 2 — Cross-Examination:** Each persona challenges the most opposed position
- **Round 3 — Verdict:** Each persona gives go/no-go/conditional with 50-word reasoning

**4 personas:**
- Bootstrap Founder — "Can I ship this weekend? Where are the first 10 customers?"
- Market Analyst — "What's the realistic MRR ceiling? Who gets disrupted?"
- Technical Architect — "What's the simplest architecture? What breaks at scale?"
- Devil's Advocate — "Why hasn't someone built this? What kills it in 6 months?"

**Tier adjustment:** Panel can move tier by +/-1 level.
**Go/no-go:** 3+ recommend = Go. 2 recommend with conditions = Conditional. 2+ against (including Devil's Advocate) = No-go.

Panel output saved to `opportunities.panel_json` via `db-store.py update`.

## Lifecycle

Valid transitions:
```
discovered -> evaluated -> researching -> building -> launched
                \                  \              \
                 -> parked <--------<--------------<
                 -> rejected
```

`/prospector update OPP-XXXX --status researching` validates the transition is legal. Invalid transitions are rejected with explanation.

## State Management

- **Database:** `~/.claude/prospector/prospector.db` (created by `db-store.py init`)
- **Schema version:** stored in `pragma user_version`. Migration: `db-store.py migrate`
- **Server PID:** `~/.claude/prospector/server.pid`
- Create directory on first use: `mkdir -p ~/.claude/prospector/`

**Persistence timing:** Save to SQLite after EACH wave completes (crash recovery). Sessions table tracks `wave_completed`.

**Session resumability:** If a session is interrupted:
1. `db-store.py list-sessions --status in_progress` shows interrupted sessions
2. Detect in-progress sessions for the same seed, offer to resume from last completed wave
3. Resumed sessions load existing evidence from DB and continue from Wave N+1

## Dashboard

Launch: `/prospector dashboard`
Stop: `/prospector dashboard stop`

**Protocol:**
1. Build frontend if `skills/prospector/webapp/frontend/dist/` is missing: `cd skills/prospector/webapp/frontend && pnpm install && pnpm build`
2. Check port 8765 (fallback: 8766, 8767)
3. Run: `uv run python -m skills.prospector.webapp.cli serve --port 8765 --db ~/.claude/prospector/prospector.db`
4. PID written automatically to `~/.claude/prospector/server.pid`
5. Open browser: `open http://localhost:{port}` (macOS) or `xdg-open http://localhost:{port}` (Linux). Print URL if open fails.

**Stop:** `uv run python -m skills.prospector.webapp.cli stop`
**Status:** `uv run python -m skills.prospector.webapp.cli status`

## Gallery (Empty Arguments)

Show:
1. Mode menu with examples for each mode
2. Pipeline summary (one line): `discovered: N | evaluated: N | researching: N | building: N | launched: N`
3. Recent discoveries (5-row table): `ID | Title | Tier | Status | Date`
4. Builder profile status (one line): `Stack: [...] | Budget: Nh/wk | Goal: $N MRR` (or "No profile set — run `/prospector profile set {...}`")

## Critical Rules

1. Never fabricate evidence — every quote traces to a real URL. Unverifiable quotes marked "unverified" and downweighted.
2. Single-signal opportunities cannot reach Strong tier.
3. Deep-read is mandatory when tools are available. Degraded mode: cap at Moderate, warn on every card.
4. Always present Wave 0 triage to user for approval before executing.
5. 5-10 opportunities per session maximum.
6. Never skip Wave 3 (validation) — counter-evidence search is mandatory.
7. Every opportunity card must include "Why This Might Be Wrong".
8. Builder profile is optional — triage works without it.
9. Lifecycle transitions require explicit user action.
10. Database writes after every wave (crash recovery).
11. Never claim an opportunity is "validated" — only that signals were detected.
12. Dashboard is a bonus feature — all core modes work without it.
13. N dispatched = N accounted for before advancing waves.
14. PreToolUse Edit hook is non-negotiable.
15. Max tool calls per session: ~45 search + ~25 deep reads + ~10 validation = ~80 total.

## Vocabulary

| Term | Meaning |
|------|---------|
| opportunity | A discovered microSaaS idea with evidence, triage, and lifecycle status |
| signal | A raw data point: forum post, trend data, review, competitor gap |
| gold signal | One of 6 high-value signal types |
| triage | Qualitative assessment (strong/moderate/weak) for sorting — NOT a validity claim |
| tier | Overall classification: Strong, Moderate, Weak |
| deep-read | Fetching full page text via fetcher/trafilatura, not relying on search snippets |
| opportunity card | Structured output: evidence + counter-evidence + triage |
| pipeline | Lifecycle: discovered -> evaluated -> researching -> building -> launched -> parked/rejected |
| seed | User-provided niche/keyword for focused discovery |
| free-roam | Autonomous discovery via meta-queries, no user seed |
| wave | Pipeline phase (0-4) |
| meta-query | Curated search queries used in free-roam to discover trending pain points |
