# Triage System

6-dimension rubric for qualitatively assessing microSaaS opportunities. The LLM assigns ratings in Wave 2; the `triage-validator.py` script enforces hard rules and computes tier.

## Contents

- [Dimensions](#dimensions)
- [Bootstrappability](#bootstrappability)
- [PMF Signals](#pmf-signals)
- [Competition](#competition)
- [Revenue Potential](#revenue-potential)
- [Technical Feasibility](#technical-feasibility)
- [Moat Potential](#moat-potential)
- [Tier Assignment Algorithm](#tier-assignment-algorithm)
- [Hard Rules](#hard-rules)
- [Counter-Evidence Requirements](#counter-evidence-requirements)
- [Builder Profile Adjustments](#builder-profile-adjustments)
- [Source Authority Tiers](#source-authority-tiers)
- [Triage Vocabulary](#triage-vocabulary)

---

## Dimensions

| Dimension | Weight | What It Measures |
|-----------|--------|------------------|
| Bootstrappability | High | Can a solo dev ship an MVP quickly and cheaply? |
| PMF Signals | High | Is there evidence real people want this and would pay? |
| Competition | Medium | How crowded is the space? (inversely scored: strong = few competitors) |
| Revenue Potential | Medium | What is the realistic revenue ceiling? |
| Technical Feasibility | Medium | Can this be built with standard tools and skills? |
| Moat Potential | Low | Can the builder create lasting defensibility? |

The LLM assigns `strong`, `moderate`, or `weak` per dimension. These are qualitative assessments, not numeric scores.

---

## Bootstrappability

### Strong

- Weekend MVP possible (3-7 days for working prototype)
- Infrastructure cost under $100/month at launch
- No regulatory compliance required (HIPAA, PCI, SOC2)
- Well-known tech stack with abundant tutorials and libraries
- Single developer can build, deploy, and maintain
- No cold-start problem (does not require existing users to be useful)

### Moderate

- MVP possible in 2-4 weeks
- Infrastructure cost $100-500/month
- Minor compliance considerations (e.g., GDPR data handling)
- Requires learning one unfamiliar API or framework
- Single developer can build but may need help with specific domain
- Mild cold-start: works with small data but improves with more

### Weak

- MVP requires 1+ months or multiple developers
- Infrastructure cost over $500/month (GPU compute, licensed APIs)
- Significant compliance requirements (healthcare, finance, education)
- Requires proprietary data, licensed content, or specialized hardware
- Complex domain requiring expert knowledge (ML training, crypto)
- Hard cold-start: useless without critical mass of users or data

---

## PMF Signals

### Strong

- 3+ independent pain signals from different communities
- Explicit payment willingness mentioned ("I would pay for this")
- Growing search volume for the problem/solution space
- People describe detailed workflows they wish were automated
- Multiple users agree in threads (high engagement: 50+ upvotes, many replies)
- Signals span multiple user personas (not just one niche sub-community)

### Moderate

- 2 independent pain signals from different sources
- Implied payment willingness (users mention price comparisons, budget)
- Stable search volume (not declining)
- Users describe frustrations but less specific about needs
- Moderate engagement (10-50 upvotes)
- Signals from a single community type (e.g., all Reddit) but multiple subreddits

### Weak

- Only 1 signal or all signals from the same thread/source
- No payment signals detected
- Declining or flat search volume
- Vague complaints without specific need articulation
- Low engagement (<10 upvotes, few replies)
- Single persona, single community — could be an isolated complaint

---

## Competition

Score inversely: "strong" means favorable competitive landscape (few/weak competitors).

### Strong (Favorable)

- No direct competitor serving this exact niche
- Existing tools are expensive (>$50/month) and enterprise-focused
- Competitors have terrible UX with vocal complaints
- Gap exists because market leader pivoted away or shut down
- Niche is too small for VC-backed companies to pursue

### Moderate

- 1-3 competitors exist but with clear gaps or weaknesses
- Competitors are priced $15-50/month with room for cheaper alternative
- Incumbent has loyal users but has not updated in 12+ months
- Open-source alternative exists but requires self-hosting and configuration
- Competitors serve adjacent niche, not exact use case

### Weak (Unfavorable)

- Well-funded incumbent with strong product and loyal users
- Free alternatives exist that are good enough for most users
- 5+ competitors actively iterating in this space
- Competitor is a feature of a larger platform (e.g., built into Slack, Notion)
- VC-backed competitor recently raised a round and is expanding

---

## Revenue Potential

### Strong

- Realistic $10K+ MRR ceiling within 12 months
- Pricing power exists: users already pay for inferior alternatives
- Clear expansion paths (tiers, add-ons, team plans)
- TAM supports 1000+ potential paying customers at target price
- Low churn risk: product becomes part of daily workflow

### Moderate

- Realistic $2K-10K MRR ceiling
- Some pricing power but price-sensitive market
- Limited expansion paths (single tier, one-time purchase possible)
- TAM supports 200-1000 potential paying customers
- Moderate churn risk: nice-to-have rather than must-have

### Weak

- MRR ceiling likely under $2K
- Race-to-bottom pricing (users expect free or very cheap)
- No clear expansion beyond initial offering
- Tiny TAM or users are unwilling to pay
- High churn: seasonal use, one-time need, or easy to switch away

---

## Technical Feasibility

### Strong

- Standard web stack (Python/Node + database + API integrations)
- All required APIs are well-documented and have free tiers
- No ML training required (inference-only or no AI needed)
- Builder's existing tech stack matches (if profile loaded)
- Deployment to standard platforms (Vercel, Railway, Fly.io)
- Clear architecture: CRUD app, API wrapper, or automation pipeline

### Moderate

- Requires 1-2 unfamiliar APIs or services
- Some API limitations (rate limits, pricing tiers, beta APIs)
- May need lightweight ML (using pre-trained models, not training)
- Partial tech stack match with builder profile
- Requires background jobs, webhooks, or real-time features
- Architecture has some complexity: multi-service, queue, or pipeline

### Weak

- Requires ML model training or fine-tuning
- Depends on unstable or undocumented APIs
- Requires mobile app development (iOS/Android native)
- Hardware integration (IoT, embedded systems)
- Complex distributed systems (real-time collaboration, multi-region)
- No tech stack match with builder profile

---

## Moat Potential

### Strong

- Data network effects: product gets better as more users contribute data
- Integration lock-in: deep integration with user's existing tools
- Compounding advantage: each user action creates value for other users
- Proprietary dataset: product generates unique data over time
- Community/marketplace: two-sided dynamics create switching costs

### Moderate

- Workflow lock-in: users invest time configuring the product
- Brand/trust: in a space where trust matters (security, finance)
- Speed advantage: first-mover in a growing niche
- Content moat: user-generated content that is hard to replicate
- Partial network effects that require critical mass

### Weak

- Pure API wrapper with no proprietary value-add
- Easily replicated with a weekend project
- No data or network effects
- Commodity features available in larger platforms
- No switching costs: users can export and leave easily

---

## Tier Assignment Algorithm

This algorithm is implemented deterministically in `triage-validator.py`. The LLM does NOT assign tiers — it assigns per-dimension ratings, and the script computes the tier.

### Counting

```
strong_count = count of dimensions rated "strong"
weak_count = count of dimensions rated "weak"
```

### Tier Rules

**Strong tier:**
- 4+ dimensions strong AND 0 weak
- OR: 3 dimensions strong including PMF Signals, AND 0-1 weak (and the weak is not Bootstrappability)

**Moderate tier:**
- 2-3 dimensions strong AND at most 2 weak
- OR: Mixed ratings but no critical weakness (PMF Signals is not weak AND Bootstrappability is not weak)
- OR: Would be Strong but hard rules capped it

**Weak tier:**
- 1 or fewer dimensions strong
- OR: PMF Signals is weak (regardless of other ratings)
- OR: Bootstrappability is weak (regardless of other ratings)
- OR: 3+ dimensions are weak

### Precedence

Hard rules (below) take precedence over the algorithm. A candidate that qualifies for Strong under the algorithm but triggers a hard rule cap will be set to Moderate.

---

## Hard Rules

These rules are enforced by `triage-validator.py` and cannot be overridden by LLM reasoning.

### Single-Signal Cap

- **Rule:** Opportunities with only 1 supporting signal cannot be Strong tier
- **Effect:** Cap at Moderate regardless of dimension ratings
- **Rationale:** Single signals may be outliers; require corroboration

### Freshness Requirement

- **Rule:** Opportunities where ALL signals are older than 6 months cap at Weak
- **Effect:** Force tier to Weak if `oldest_signal > 6 months` and no fresh signals exist
- **Rationale:** Stale pain may have been solved since the signal was generated

### Independence Check

- **Rule:** Opportunities where ALL signals come from the same source (same thread, same author) cap at Moderate
- **Effect:** Downgrade PMF Signals by one level, then recompute tier
- **Rationale:** Echo chamber — one frustrated user is not a market

### Strong Incumbent Override

- **Rule:** When Wave 3 validation finds a well-funded direct competitor, force Competition to weak
- **Effect:** Recompute tier with Competition = weak
- **Rationale:** Counter-evidence from validation supersedes initial triage

### Degraded Mode Cap

- **Rule:** When operating without deep-read tools, no opportunity can be Strong
- **Effect:** Cap all tiers at Moderate; add warning to card
- **Rationale:** Search snippets alone are insufficient evidence for Strong confidence

---

## Counter-Evidence Requirements

Wave 3 validation subagents must perform at minimum:

### Mandatory Searches

1. **Competitor search:** "[opportunity title] alternative" or "[niche] tool"
2. **Failure search:** "why [niche] failed" or "[similar product] shutdown"

### Recommended Searches (When Budget Allows)

3. **Market saturation:** "[niche] crowded" or "[niche] too many tools"
4. **Technical risk:** "[key technology] deprecated" or "[API] pricing increase"

### Counter-Evidence Impact Table

| Counter-Evidence Found | Triage Impact |
|----------------------|---------------|
| Strong funded incumbent (raised >$5M, active development) | Competition → weak |
| Recently failed similar product (<12 months) | Add to "Why This Might Be Wrong," no auto-downgrade |
| Key API deprecation announced | Technical Feasibility → weak |
| Market saturation signals (5+ active competitors) | Competition → weak |
| Regulatory risk identified | Bootstrappability → moderate (at best) |
| No counter-evidence found after 2+ searches | Positive signal — note in card |

### Evidence Quality Standards

- Counter-evidence must come from verifiable sources (not LLM inference)
- Each counter-evidence claim must include a source URL
- Severity rating required: high (threatens viability), medium (adds risk), low (minor concern)

---

## Builder Profile Adjustments

When a builder profile is loaded from the database, adjust triage ratings:

### Tech Stack Match

| Match Level | Adjustment |
|-------------|------------|
| Builder's primary stack matches MVP requirements | Technical Feasibility +1 (moderate → strong) |
| Builder's stack partially overlaps (knows 50%+ of required tech) | No change |
| Builder has no experience with required stack | Technical Feasibility -1 (strong → moderate) |

### Time Budget Match

| Match Level | Adjustment |
|-------------|------------|
| Builder's weekly hours >= MVP estimate / 4 weeks | No change |
| Builder's weekly hours < MVP estimate / 4 weeks | Bootstrappability -1 |

### Interest and Avoid Lists

| Condition | Action |
|-----------|--------|
| Opportunity niche is in builder's interests | Highlight with note, no triage change |
| Opportunity niche is in builder's avoid list | Add warning: "This niche is on your avoid list" |
| Opportunity requires technology on builder's avoid list | Technical Feasibility -1 |

### Application

Profile adjustments apply AFTER initial triage and BEFORE tier assignment. The adjustment reason is recorded in `triage_reasoning` for transparency.

---

## Source Authority Tiers

Weight evidence differently based on source quality.

### Tier 1: High Authority

- ProductHunt launch with traction metrics (upvotes, comments)
- G2/Capterra verified reviews with star ratings
- Published pricing pages of competitors
- GitHub repository with stars and download counts
- Official product shutdown/pivot announcements
- Published market research reports

### Tier 2: Medium Authority

- Reddit post with 50+ upvotes and discussion thread
- Hacker News post on front page or with 50+ points
- IndieHackers post with engagement (comments, likes)
- Stack Overflow question with votes and no accepted answer
- Tech blog analysis from recognized publication

### Tier 3: Low Authority

- Reddit post with <50 upvotes or few replies
- Random blog post without citations
- Social media post without engagement metrics
- Forum post on niche site with no visible metrics
- Self-reported anecdotes without corroboration

### Weighting Rules

- Strong intensity signals require Tier 1 or Tier 2 source
- A single Tier 3 signal alone cannot support PMF Signals = strong
- Tier 1 source with negative signal (competitor is strong) weighs heavily in Competition rating
- Source tier is recorded alongside each evidence item for traceability

---

## Triage Vocabulary

| Term | Meaning |
|------|---------|
| triage | Qualitative assessment for sorting — NOT a validity claim |
| dimension | One of the 6 assessment axes |
| rating | strong, moderate, or weak on a single dimension |
| tier | Overall classification derived from dimension ratings: Strong, Moderate, Weak |
| hard rule | Deterministic constraint enforced by script, cannot be overridden |
| cap | Maximum tier an opportunity can reach due to a hard rule |
| counter-evidence | Information that challenges the opportunity's viability |
| profile adjustment | Triage modification based on builder's skills and preferences |
| source authority | Quality weight of the evidence source |
