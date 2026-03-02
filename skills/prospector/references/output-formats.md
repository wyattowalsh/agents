# Output Formats

Card templates, JSON schemas, export formats, lifecycle definitions, static dashboard data contract, and API specifications.

## Contents

- [Opportunity Card Template](#opportunity-card-template)
- [Opportunity JSON Schema](#opportunity-json-schema)
- [Evidence JSON Schema](#evidence-json-schema)
- [Session JSON Schema](#session-json-schema)
- [Export Formats](#export-formats)
- [Lifecycle Definitions](#lifecycle-definitions)
- [Static Dashboard Data Contract](#static-dashboard-data-contract)
- [FastAPI Dashboard API](#fastapi-dashboard-api)

---

## Opportunity Card Template

Every opportunity is presented using this markdown template. All sections are mandatory.

```markdown
## OPP-XXXX: [Title]

**Pitch:** [One-liner pitch a founder would use]
**Niche:** [Niche label] | **Signal:** [Primary gold signal type]
**Discovered:** [YYYY-MM-DD] | **Status:** [lifecycle status] | **Tier:** [Strong|Moderate|Weak]

### Triage
| Dimension | Rating | Reasoning |
|-----------|--------|-----------|
| Bootstrappability | [strong|moderate|weak] | [1-2 sentence justification] |
| PMF Signals | [strong|moderate|weak] | [1-2 sentence justification] |
| Competition | [strong|moderate|weak] | [1-2 sentence justification] |
| Revenue Potential | [strong|moderate|weak] | [1-2 sentence justification] |
| Technical Feasibility | [strong|moderate|weak] | [1-2 sentence justification] |
| Moat Potential | [strong|moderate|weak] | [1-2 sentence justification] |

### Evidence
[Numbered list of evidence items, each with:]
1. [Source] ([Date]): "[Exact quote from source]" [[engagement metrics]]
   — [search_tool] → [read_tool]

### Why This Might Be Wrong
- **[Risk category]:** [Specific risk with evidence]
- **[Risk category]:** [Specific risk with evidence]
- **[Risk category]:** [Specific risk with evidence]
[Minimum 3 items]

### MVP Estimate
[Days] days | [Tech stack] | ~$[cost]/mo hosting
```

### Card Rules

- Every card must include "Why This Might Be Wrong" with at least 3 items
- Every evidence item must include a source URL or source description
- Triage reasoning must reference specific evidence, not generic statements
- If degraded mode: prepend warning banner before the card
- If panel has been run: append panel verdict section after MVP Estimate

### Panel Verdict Section (Appended After Evaluate)

```markdown
### Expert Panel Verdict
**Verdict:** [Go|No-Go|Conditional] | **Panel Date:** [YYYY-MM-DD]
**Conditions:** [List conditions if conditional]
**Key Insight:** [1-2 sentence synthesis from panel]
```

---

## Opportunity JSON Schema

Used by `db-store.py` for storage and by the API for responses.

```json
{
  "id": "OPP-0017",
  "title": "AI-Powered Meeting Notes to Slack",
  "one_liner": "Auto-transcribe meetings, extract action items, post to Slack channels",
  "niche": "productivity/remote-work",
  "status": "discovered",
  "primary_signal": "manual_workflow",
  "triage": {
    "bootstrappability": "strong",
    "pmf_signals": "strong",
    "competition": "moderate",
    "revenue_potential": "moderate",
    "technical_feasibility": "strong",
    "moat_potential": "weak"
  },
  "triage_tier": "strong",
  "triage_reasoning": {
    "bootstrappability": "Whisper API + Slack Bot SDK, ~$20/mo infra, MVP in 5-7 days",
    "pmf_signals": "3 independent sources, 47 upvotes on r/remotework complaint",
    "competition": "Otter.ai exists ($17/mo) but no native Slack; Fireflies is enterprise-only",
    "revenue_potential": "$9-15/mo, TAM ~750K paid Slack workspaces",
    "technical_feasibility": "Python + well-documented APIs, builder's stack match",
    "moat_potential": "API wrapper, easily replicated, no data network effect"
  },
  "evidence": [
    {
      "id": 1,
      "source_category": "community",
      "signal_type": "manual_workflow",
      "source_url": "https://reddit.com/r/remotework/...",
      "source_tool": "brave_web_search → fetch_markdown",
      "quote": "I literally spend 30 minutes after every standup typing up what we discussed into Slack.",
      "intensity": "strong",
      "payment_signal": false,
      "context": "r/remotework, 53 upvotes, 12 replies",
      "accessed_at": "2026-03-01T14:30:00"
    }
  ],
  "counter_evidence": [
    "Otter.ai could ship native Slack integration any quarter",
    "Whisper API pricing increased 2x in 2025",
    "Market ceiling: Slack-only limits TAM"
  ],
  "panel_json": null,
  "panel_verdict": null,
  "mvp_days": 5,
  "mvp_tech_stack": "Python, Whisper API, Slack Bot SDK, SQLite",
  "session_id": "sess-20260301-abc123",
  "seed_query": "meeting notes automation",
  "created_at": "2026-03-01T14:30:00",
  "updated_at": "2026-03-01T15:45:00",
  "notes": null
}
```

### Field Constraints

| Field | Type | Constraints |
|-------|------|-------------|
| `id` | string | Format: `OPP-XXXX` (zero-padded 4-digit) |
| `status` | string | Enum: discovered, evaluated, researching, building, launched, parked, rejected |
| `primary_signal` | string | Enum: pain_no_solution, dying_product, platform_expansion, rising_trend, terrible_ux, manual_workflow |
| `triage.*` | string | Enum: strong, moderate, weak |
| `triage_tier` | string | Enum: strong, moderate, weak |
| `panel_verdict` | string/null | Enum: go, nogo, conditional, null |

---

## Evidence JSON Schema

Individual evidence items stored in the `evidence` table.

```json
{
  "id": 1,
  "opportunity_id": "OPP-0017",
  "source_category": "community",
  "signal_type": "manual_workflow",
  "source_url": "https://reddit.com/r/remotework/...",
  "source_tool": "brave_web_search → fetch_markdown",
  "quote": "Exact quote from the source page",
  "intensity": "strong",
  "payment_signal": false,
  "context": "r/remotework user, 53 upvotes, 12 replies agreeing",
  "accessed_at": "2026-03-01T14:30:00"
}
```

### Evidence Rules

- `quote` must be an exact extraction from the source — never paraphrased or invented
- `source_url` must be a valid URL (or null if from search snippet without URL)
- `source_tool` records the tool chain used: "search_tool → read_tool"
- `intensity` follows the scale defined in `discovery-pipeline.md`
- `payment_signal` is true only when explicit payment willingness is detected

---

## Session JSON Schema

```json
{
  "id": "sess-20260301-abc123",
  "mode": "mine",
  "seed_query": "meeting notes automation",
  "source_filter": null,
  "opportunities_found": 7,
  "wave_completed": 4,
  "status": "complete",
  "started_at": "2026-03-01T14:00:00",
  "completed_at": "2026-03-01T15:45:00"
}
```

---

## Export Formats

### JSON Export

Full opportunity data including evidence. Output by `db-store.py export --format json`.

```json
{
  "export_date": "2026-03-02",
  "total_opportunities": 15,
  "opportunities": [
    { "...full opportunity JSON as above..." }
  ]
}
```

### CSV Export

Flat format with selected columns. Output by `db-store.py export --format csv`.

| Column | Source |
|--------|--------|
| id | `opportunities.id` |
| title | `opportunities.title` |
| one_liner | `opportunities.one_liner` |
| niche | `opportunities.niche` |
| status | `opportunities.status` |
| primary_signal | `opportunities.primary_signal` |
| tier | `opportunities.triage_tier` |
| bootstrappability | `opportunities.triage_bootstrappability` |
| pmf_signals | `opportunities.triage_pmf` |
| competition | `opportunities.triage_competition` |
| revenue_potential | `opportunities.triage_revenue` |
| technical_feasibility | `opportunities.triage_technical` |
| moat_potential | `opportunities.triage_moat` |
| signal_count | COUNT of evidence rows |
| panel_verdict | `opportunities.panel_verdict` |
| mvp_days | `opportunities.mvp_days` |
| created_at | `opportunities.created_at` |
| updated_at | `opportunities.updated_at` |

### HTML Export

Generate a static HTML dashboard. Use `templates/dashboard.html` with JSON data injection.

Process:
1. Run `db-store.py export --format json` to get full data
2. Inject JSON into the `<script id="data" type="application/json">` tag in the template
3. Write the resulting HTML to the user's specified output path
4. The template renders a self-contained dashboard with no server required

---

## Lifecycle Definitions

### Status Definitions

| Status | Meaning | Who Transitions | Valid From |
|--------|---------|-----------------|------------|
| `discovered` | Initial discovery, triaged but not deeply evaluated | System (Wave 4) | — (initial) |
| `evaluated` | Expert panel has assessed this opportunity | System (panel complete) | discovered |
| `researching` | Builder is actively investigating (talking to users, prototyping) | User | evaluated |
| `building` | Builder is constructing the MVP | User | researching |
| `launched` | MVP is live and available to users | User | building |
| `parked` | Paused for later — not rejected, but not active | User | any except rejected |
| `rejected` | Explicitly decided not to pursue | User | any except launched |

### Transition Rules

```
discovered → evaluated       (after expert panel)
discovered → parked          (user decides to skip)
discovered → rejected        (user decides against)
evaluated  → researching     (user begins investigation)
evaluated  → parked          (user defers)
evaluated  → rejected        (panel says no-go, user agrees)
researching → building       (user starts building)
researching → parked         (user pauses)
researching → rejected       (user abandons)
building   → launched        (MVP goes live)
building   → parked          (user pauses)
building   → rejected        (user abandons)
launched   → parked          (product paused/sunset)
parked     → researching     (user resumes from parked)
parked     → rejected        (user decides against)
```

### Invalid Transitions (Rejected by db-store.py)

- `launched → discovered` (cannot un-launch)
- `rejected → *` (rejection is final)
- `discovered → building` (must evaluate or research first)
- `discovered → launched` (must go through pipeline)
- Any transition not listed above

---

## Static Dashboard Data Contract

The `templates/dashboard.html` file expects data injected via a `<script>` tag with this structure:

```json
{
  "generated_at": "2026-03-02T10:00:00",
  "stats": {
    "total": 15,
    "by_status": {"discovered": 8, "evaluated": 3, "researching": 2, "building": 1, "launched": 1},
    "by_tier": {"strong": 3, "moderate": 8, "weak": 4},
    "by_signal": {"pain_no_solution": 5, "manual_workflow": 4, "terrible_ux": 3, "rising_trend": 2, "dying_product": 1},
    "by_niche": {"productivity": 4, "developer-tools": 3, "remote-work": 2}
  },
  "opportunities": [
    {
      "id": "OPP-0017",
      "title": "AI-Powered Meeting Notes to Slack",
      "one_liner": "Auto-transcribe meetings, extract action items, post to Slack",
      "niche": "productivity/remote-work",
      "status": "evaluated",
      "primary_signal": "manual_workflow",
      "tier": "strong",
      "triage": {"bootstrappability": "strong", "pmf_signals": "strong", "competition": "moderate", "revenue_potential": "moderate", "technical_feasibility": "strong", "moat_potential": "weak"},
      "signal_count": 3,
      "panel_verdict": "go",
      "mvp_days": 5,
      "created_at": "2026-03-01",
      "updated_at": "2026-03-01"
    }
  ],
  "profile": {
    "tech_stack": ["Python", "FastAPI", "React"],
    "time_budget_hours_week": 15,
    "revenue_goal_mrr": 2000
  }
}
```

### Dashboard Views

The static dashboard (and the webapp SPA) render these views from the data:

| View | Route/Hash | Content |
|------|-----------|---------|
| Pipeline | `#pipeline` | Kanban board grouped by lifecycle status |
| Feed | `#feed` | Chronological list of opportunities with cards |
| Leaderboard | `#leaderboard` | Ranked by tier, then signal count |
| Detail | `#detail/{id}` | Full opportunity card with evidence and panel |
| Stats | `#stats` | Aggregate charts: by status, tier, signal type, niche |

---

## FastAPI Dashboard API

Endpoint specifications for `webapp/app.py`.

### List Opportunities

```
GET /api/opportunities
Query params: status, tier, niche, sort (tier|date|signals), limit (default 50), offset (default 0)
Response: { "total": N, "opportunities": [...] }
```

### Get Opportunity Detail

```
GET /api/opportunities/{id}
Response: Full opportunity JSON with evidence array (JOIN)
404 if not found
```

### Update Opportunity

```
PATCH /api/opportunities/{id}
Body: { "status": "researching", "notes": "..." }
Validates lifecycle transition. Returns updated opportunity.
422 if invalid transition.
```

### Delete Opportunity

```
DELETE /api/opportunities/{id}
Returns: { "deleted": true }
404 if not found
```

### List Sessions

```
GET /api/sessions
Query params: status, limit, offset
Response: { "total": N, "sessions": [...] }
```

### Get Stats

```
GET /api/stats
Response: { "total": N, "by_status": {...}, "by_tier": {...}, "by_signal": {...}, "by_niche": {...} }
```

### Get Profile

```
GET /api/profile
Response: Profile JSON or 404 if no profile set
```

### Update Profile

```
PUT /api/profile
Body: { "tech_stack": [...], "time_budget_hours_week": 15, "revenue_goal_mrr": 2000, "interests": [...], "avoid": [...] }
Response: Updated profile JSON (upserts singleton row)
```

### Export

```
GET /api/export/{format}
Path param: format = json|csv
Response: JSON array or CSV file (Content-Type: text/csv for CSV)
```

### Serve Frontend

```
GET /
Response: Serve webapp/index.html as static file
```

### Error Response Format

All error responses use this structure:

```json
{
  "error": "short error code",
  "detail": "human-readable description",
  "status_code": 422
}
```

| Status Code | Use For |
|-------------|---------|
| 400 | Malformed request |
| 404 | Opportunity or resource not found |
| 422 | Invalid lifecycle transition or validation failure |
| 500 | Internal server error |
