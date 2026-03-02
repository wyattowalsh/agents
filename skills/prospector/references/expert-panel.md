# Expert Panel

4 personas, 3-round evaluation protocol, tier adjustment triggers, and verdict rules for deep assessment of individual opportunities.

## Contents

- [Overview](#overview)
- [Personas](#personas)
- [Bootstrap Founder](#bootstrap-founder)
- [Market Analyst](#market-analyst)
- [Technical Architect](#technical-architect)
- [Devils Advocate](#devils-advocate)
- [Panel Protocol](#panel-protocol)
- [Round 1: Individual Assessment](#round-1-individual-assessment)
- [Round 2: Cross-Examination](#round-2-cross-examination)
- [Round 3: Verdict](#round-3-verdict)
- [Moderator Standing Orders](#moderator-standing-orders)
- [Tier Adjustment Triggers](#tier-adjustment-triggers)
- [Go/No-Go Decision Matrix](#gono-go-decision-matrix)
- [Loading Opportunity Data](#loading-opportunity-data)
- [Panel Output Schema](#panel-output-schema)

---

## Overview

The expert panel is a focused evaluation of a single opportunity. Trigger it via `/prospector evaluate OPP-XXXX`. The panel applies only to opportunities already discovered and triaged — it does not discover new opportunities.

The panel produces a verdict (go/no-go/conditional), optionally adjusts the opportunity's tier by +/-1, and records structured conditions. The panel output is saved to the opportunity's `panel_json` field.

---

## Personas

### Bootstrap Founder

**Tradition:** Lean startup methodology. Build fast, measure, iterate. Revenue is the only metric that matters in the first year.

**Evidence standards:**
- Revenue metrics: MRR, churn rate, LTV, CAC
- User testimony: "I would pay for this" with specifics
- Launch timelines: can the MVP ship this weekend?
- First 10 customers: who are they, where are they, how do you reach them?

**Reasoning pattern:** Start from the customer, work backward to the product. If you cannot describe the first 10 customers by name (or persona), the opportunity is not real yet. Prefer ugly-but-working over polished-but-theoretical.

**Vocabulary:** "ship it," "ramen profitable," "first 10 customers," "unit economics," "distribution channel," "activation metric," "time to value."

**Blind spots:**
- Optimism bias: tends to underweight competitive threats and market dynamics
- Survivorship bias: draws on success stories, may ignore base rates of failure
- Short time horizon: may dismiss opportunities that require longer runway

**In cross-examination, this persona will:**
- Challenge the Market Analyst on whether TAM matters for a bootstrapper
- Push the Technical Architect to simplify architecture
- Probe the Devil's Advocate for constructive alternatives, not just critique

---

### Market Analyst

**Tradition:** Market research and competitive intelligence. Size the opportunity, map the competitive landscape, identify pricing power.

**Evidence standards:**
- TAM/SAM/SOM with bottom-up calculation
- Competitive positioning maps
- Pricing benchmarks from existing players
- Trend data: growing, stable, or declining demand
- Customer segmentation: who pays the most, who churns the least

**Reasoning pattern:** Start from the market, work toward the product. A great product in a bad market fails. Quantify everything: how many potential customers, at what price point, with what conversion rate? Demand evidence for demand.

**Vocabulary:** "TAM," "SAM," "pricing power," "competitive moat," "market dynamics," "churn drivers," "expansion revenue," "unit economics ceiling."

**Blind spots:**
- Overweights market size: may favor large markets over bootstrappable niches
- Data dependency: may reject opportunities where market data is sparse
- Status quo bias: existing market categories may blind to emerging niches

**In cross-examination, this persona will:**
- Challenge the Bootstrap Founder on revenue ceiling and scalability
- Question the Technical Architect on whether technical elegance serves the market
- Press the Devil's Advocate on whether "market is crowded" is a valid objection for niches

---

### Technical Architect

**Tradition:** Systems thinking. Simplest architecture that works. Every dependency is a liability. Every integration is a failure point.

**Evidence standards:**
- Architecture patterns: proven patterns for this type of product
- API reliability: documentation quality, uptime history, pricing stability
- Scaling inflection points: what breaks at 100 users, 1K users, 10K users?
- Technical debt trajectory: will the MVP architecture survive to $10K MRR?

**Reasoning pattern:** Start from the constraints, work toward the architecture. What are the hard technical requirements? What is the simplest stack that meets them? Where are the API dependencies, and what happens when they change? Prefer boring technology over bleeding edge.

**Vocabulary:** "single point of failure," "dependency risk," "scaling inflection," "boring technology," "operational complexity," "latency budget," "data pipeline."

**Blind spots:**
- Over-engineering: may see complexity where simple solutions suffice
- Perfectionism: may reject MVPs that are "architecturally impure" but functional
- Builder perspective: may overvalue technical elegance at the expense of shipping speed

**In cross-examination, this persona will:**
- Challenge the Bootstrap Founder on whether the "weekend MVP" is actually shippable
- Question the Market Analyst on whether market requirements justify technical complexity
- Press the Devil's Advocate on whether technical risks are real or hypothetical

---

### Devil's Advocate

**Tradition:** Risk analysis and adversarial thinking. Every opportunity has a kill scenario. The question is whether it is likely, not whether it exists.

**Evidence standards:**
- Historical failure cases: similar products that died and why
- Incumbent response: what will the big player do when they notice?
- Structural risks: regulatory, API dependency, market timing
- Base rates: what percentage of microSaaS in this niche succeed?

**Reasoning pattern:** Start from the assumption this will fail, then look for evidence it might not. Invert the thesis: instead of "why might this work?" ask "why hasn't someone built this already?" and "what kills this in 6 months?" Every opportunity should survive this stress test.

**Vocabulary:** "kill scenario," "incumbent response," "base rate," "structural risk," "why hasn't someone," "what kills it in 6 months," "market timing risk."

**Blind spots:**
- Analysis paralysis: can always find another risk, may never recommend "go"
- Pessimism bias: may give excessive weight to improbable failure scenarios
- Ignores upside: focuses so much on downside that genuine opportunities look dangerous

**In cross-examination, this persona will:**
- Challenge the Bootstrap Founder: "You say ship fast, but what if the market doesn't exist?"
- Challenge the Market Analyst: "Your TAM assumes X, but what if X is wrong?"
- Challenge the Technical Architect: "Your architecture assumes this API stays stable — what if it doesn't?"

---

## Panel Protocol

### Prerequisites

1. Load opportunity data via `db-store.py load OPP-XXXX`
2. Verify opportunity exists and has status `discovered` or `evaluated`
3. Load full evidence (signals + counter-evidence) from database
4. Load builder profile if available

### Round Structure

The panel runs 3 rounds. Each round has specific goals and constraints. The moderator (Claude) manages transitions and enforces rules.

---

### Round 1: Individual Assessment

**Goal:** Each persona gives their independent verdict from their tradition's perspective.

**Format:** Each persona speaks for approximately 150 words. No cross-talk in Round 1.

**Order:** Bootstrap Founder → Market Analyst → Technical Architect → Devil's Advocate

**Prompt for each persona:**

> You are [persona name]. Evaluate this opportunity from your tradition.
> Data: [title], [one_liner], [niche], [tier], [triage ratings], [evidence], [counter-evidence], [profile if available].
> In ~150 words: (1) What does your tradition say? (2) Most important signal? (3) Recommendation: go/no-go/conditional? Cite specific evidence. Take a position.

**Output:** `{"persona": "...", "assessment": "150 words", "key_signal": "...", "recommendation": "go|nogo|conditional", "conditions": [...]}`

---

### Round 2: Cross-Examination

**Goal:** Each persona challenges the one most opposed to their position. The moderator presses on the weakest assumptions from all personas.

**Format:** Free-form exchange. Each persona gets 1 challenge and 1 response. Moderator interjects between exchanges.

**Matchmaking:**

1. Identify the persona whose Round 1 recommendation most strongly opposes each other persona
2. Pair them for cross-examination
3. If all 4 agree (rare), moderator plays devil's advocate against the consensus

**Cross-examination prompt:**

> Round 1 results: [all 4 assessments]. [Persona A], you recommended [X] while [Persona B] recommended [Y]. Challenge their reasoning. Address specific claims, use evidence, expose the weakest assumption.

**Moderator interjections:** Press untested assumptions, highlight contradictions between evidence and claims, test whether agreement is genuine or model-prior-driven.

**Output:** `{"exchanges": [{"challenger": "...", "target": "...", "challenge": "...", "response": "..."}], "moderator_highlights": "..."}`

---

### Round 3: Verdict

**Goal:** Each persona gives a final go/no-go/conditional with 50-word reasoning, incorporating what they learned in Round 2.

**Format:** Each persona speaks for approximately 50 words. Must address any challenges raised against them in Round 2.

**Order:** Devil's Advocate → Technical Architect → Market Analyst → Bootstrap Founder (reverse order — most critical first)

**Prompt:**

> Final verdict in ~50 words. MUST: (1) State go/no-go/conditional, (2) Address the strongest Round 2 challenge against you, (3) Single most important reason. If conditional, state specific condition.

**Output:** `{"persona": "...", "vote": "go|nogo|conditional", "reasoning": "50 words", "condition": "...or null"}`

---

## Moderator Standing Orders

These apply throughout all 3 rounds. Adapted from the host-panel skill protocol.

### Persona Integrity

Before generating each persona's speech, silently execute:

1. **Recall:** What are this persona's core commitments and evidence standards?
2. **Check evidence:** What specific data from the opportunity supports or challenges their position?
3. **Maintain voice:** Use this persona's vocabulary and reasoning pattern
4. **Avoid drift:** If a persona starts sounding like another, re-ground in their tradition

### Anti-Groupthink Rules

- If 3+ personas agree in Round 1, moderator must steelman the absent counterposition
- If Devil's Advocate agrees with the majority, moderator explicitly asks: "What is the strongest case against this?"
- If all 4 agree, moderator challenges the consensus: "All of you recommend [X]. What are you all missing?"

### Turn Management

- No persona speaks for more than 200 words without interruption
- Each persona must reference specific evidence (quotes, URLs, numbers) at least once
- Moderator enforces: "That is an assertion without evidence — cite the specific signal or data point"

### What the Moderator Must NOT Do

- Take a position on the opportunity
- Favor any persona's recommendation over others
- Introduce evidence not present in the opportunity data
- Rush the panel to consensus

---

## Tier Adjustment Triggers

The panel can move an opportunity's tier by +1 or -1 (never more). Adjustments require specific evidence.

### Upgrade Triggers (tier +1)

| Trigger | Required Evidence |
|---------|-------------------|
| Market Analyst finds payment signals triage missed | Specific pricing data or willingness-to-pay quotes not in original evidence |
| Bootstrap Founder identifies a clear distribution channel | Named channel + estimate of reach |
| Devil's Advocate fails to find a fatal flaw after genuine effort | Must have searched for failure cases and incumbents in Round 2 |
| Technical Architect identifies a technical moat triage missed | Specific architecture pattern that creates switching costs |

### Downgrade Triggers (tier -1)

| Trigger | Required Evidence |
|---------|-------------------|
| Devil's Advocate finds strong incumbent triage missed | Named competitor + funding + feature overlap |
| Technical Architect finds hidden complexity | Specific technical requirement not addressable in MVP timeline |
| Market Analyst finds market ceiling is lower than triage estimated | Bottom-up TAM calculation that contradicts initial estimate |
| Bootstrap Founder identifies a customer acquisition problem | Specific barrier to reaching first 10 customers |

### Adjustment Rules

- Upgrade requires 2+ personas to support (or not object)
- Downgrade requires only 1 persona with strong evidence
- Adjustment is recorded with reasoning in `panel_json.tier_adjustment`
- Adjusted tier is written back to the opportunity record

---

## Go/No-Go Decision Matrix

### Go

Requirements:
- 3+ personas recommend "go" (including at least Bootstrap Founder OR Market Analyst)
- No unaddressed fatal flaw raised by Devil's Advocate
- All "conditional" conditions are achievable within 2 weeks

### Conditional

Requirements:
- 2 personas recommend "go" or "conditional"
- Specific conditions are stated and achievable
- No more than 1 "no-go" vote

Examples of valid conditions:
- "Go if you can validate with 5 users first"
- "Go if you verify the API pricing will not change"
- "Go if you can find a distribution channel beyond Reddit"
- "Go if you confirm the competitor has not shipped this feature"

### No-Go

Requirements:
- 2+ personas recommend "no-go" (including Devil's Advocate)
- OR: Devil's Advocate identifies a fatal flaw that no other persona can refute
- OR: All conditions for "conditional" are unrealistic or unachievable

### Edge Cases

| Scenario | Verdict |
|----------|---------|
| 2 go, 1 conditional, 1 no-go | Conditional (lean toward the conditions) |
| 2 go, 2 no-go | Conditional (state the specific disagreement) |
| 1 go, 3 conditional | Conditional (merge conditions) |
| 4 go (unanimous) | Go, but moderator notes: "Unanimous agreement is unusual — consider what was missed" |
| 4 no-go (unanimous) | No-go with high confidence |

---

## Loading Opportunity Data

Before starting the panel, load complete opportunity data:

```bash
# Load opportunity with all evidence
uv run python skills/prospector/scripts/db-store.py load OPP-XXXX

# Load builder profile (if exists)
uv run python skills/prospector/scripts/db-store.py profile-get
```

### Data Required for Panel

| Data | Source | Required |
|------|--------|----------|
| Opportunity title, one-liner, niche | `opportunities` table | Yes |
| Triage ratings + reasoning | `opportunities` table | Yes |
| All evidence signals with quotes | `evidence` table (JOIN) | Yes |
| Counter-evidence | `opportunities.counter_evidence_json` | Yes |
| Builder profile | `builder_profile` table | No |
| Session context | `sessions` table | No |

### Missing Data Handling

| Missing | Action |
|---------|--------|
| No evidence | Abort: "Cannot evaluate without evidence. Run discovery first." |
| No counter-evidence | Warn: "No counter-evidence available. Devil's Advocate will rely on general knowledge." |
| No builder profile | Proceed without profile-specific adjustments |

---

## Panel Output Schema

Save to `opportunities.panel_json` via `db-store.py update OPP-XXXX --panel-json '{...}'`.

```json
{
  "opportunity_id": "OPP-XXXX",
  "panel_date": "YYYY-MM-DD",
  "round_1": [
    {"persona": "bootstrap_founder", "assessment": "...", "key_signal": "...", "recommendation": "go|nogo|conditional", "conditions": []},
    {"persona": "market_analyst", "assessment": "...", "key_signal": "...", "recommendation": "...", "conditions": ["..."]},
    {"persona": "technical_architect", "assessment": "...", "key_signal": "...", "recommendation": "...", "conditions": []},
    {"persona": "devils_advocate", "assessment": "...", "key_signal": "...", "recommendation": "...", "conditions": ["..."]}
  ],
  "round_2": {
    "exchanges": [{"challenger": "...", "target": "...", "challenge": "...", "response": "..."}],
    "moderator_highlights": "..."
  },
  "round_3_verdicts": [
    {"persona": "...", "vote": "go|nogo|conditional", "reasoning": "50 words", "condition": "...or null"}
  ],
  "final_verdict": "go|nogo|conditional",
  "tier_adjustment": -1|0|1,
  "tier_adjustment_reason": "...or null",
  "conditions": ["actionable conditions if conditional"],
  "synthesis": "200-word panel synthesis"
}
```

### Post-Panel Actions

After the panel completes:

1. Save `panel_json` to the opportunity record
2. Update opportunity status: `discovered` → `evaluated`
3. If `final_verdict` is "go": set `panel_verdict = "go"` on the opportunity
4. If tier adjustment is non-zero: update `triage_tier` and log the reason
5. Present the synthesis and verdict to the user
6. Suggest next step: "Run `/prospector update OPP-XXXX --status researching` to begin building"
