# Wargame Engine

Actor definitions, adjudication rules, Monte Carlo protocol, inject design, and AAR template.
Read during Interactive Wargame setup and turn execution.

## Contents

- [Structured Actor Definition](#structured-actor-definition)
- [Persona Library](#persona-library)
- [Turn Structure](#turn-structure)
- [Adjudication Protocol](#adjudication-protocol)
- [Monte Carlo Iteration Protocol](#monte-carlo-iteration-protocol)
- [Information Asymmetry Rules](#information-asymmetry-rules)
- [Inject Design](#inject-design)
- [AAR Protocol](#aar-protocol)

---

## Structured Actor Definition

Labels alone are insufficient (Schneider et al. 2024). Every actor requires all seven fields.

| # | Field | Description |
|---|-------|-------------|
| 1 | **Name & Role** | Full name and position (e.g., "Chen Wei — CEO, Rival Corp") |
| 2 | **Persona template** | Starting archetype: hawk / dove / pragmatist / ideologue / bureaucrat / opportunist / disruptor / custom |
| 3 | **Background narrative** | 2-3 sentences grounding the persona in the scenario |
| 4 | **Specific objectives** | Ranked priorities, concrete and measurable |
| 5 | **Constraints / red lines** | What the actor will NOT do under any circumstances |
| 6 | **Information state** | Three columns: knows, thinks they know (may be wrong), does not know |
| 7 | **Relationship dynamics** | Stance toward each other actor: allied / neutral / hostile / dependent |

### Example Actor

> **Name & Role:** Chen Wei — CEO, Rival Corp
> **Persona:** pragmatist
> **Background:** Built Rival Corp from a regional player to a national brand over 12 years. Engineer by training, data-driven, but increasingly pressured by an activist board pushing for aggressive expansion.
> **Objectives:** 1. Acquire market share in APAC 2. Maintain board confidence 3. Avoid regulatory scrutiny
> **Red lines:** Will not pursue acquisitions requiring >40% debt-to-equity. Will not publicly attack competitors.
> **Information state:**
> | Knows | Thinks they know | Does not know |
> |-------|-----------------|---------------|
> | Own Q3 revenue figures | Competitor's margins (estimate, off by 15%) | Competitor's pending patent filing |
> **Relationships:** Allied with distributor network. Neutral toward regulator. Hostile toward Player (direct competitor). Dependent on board approval for major moves.

---

## Persona Library

Eight starting templates. Expand each into a full seven-field definition before play begins.

| # | Archetype | Core trait | Decision style |
|---|-----------|-----------|----------------|
| 1 | **Hawk** | Aggressive, maximalist | Escalation-prone, views concession as weakness |
| 2 | **Dove** | Conciliatory, risk-averse | De-escalation-focused, seeks mutual benefit |
| 3 | **Pragmatist** | Practical, evidence-driven | Compromise-seeking, follows data over ideology |
| 4 | **Ideologue** | Principles-first, inflexible on core values | Rejects deals that violate beliefs, even at cost |
| 5 | **Bureaucrat** | Process-oriented, slow-moving | Rule-following, prefers precedent over innovation |
| 6 | **Opportunist** | Self-interested, deal-seeking | Alliance-flexible, pivots to whoever offers most |
| 7 | **Disruptor** | Rule-breaking, innovative | Unpredictable, forces structural change |
| 8 | **Custom** | User-defined | User-defined |

**Domain mapping guidance:**
- **Business:** pragmatist as incumbent, disruptor as startup, bureaucrat as regulator.
- **Personal:** ideologue as values-driven self, pragmatist as practical self, opportunist as short-term-gain self.
- **Geopolitical:** hawk and dove as competing policy factions, bureaucrat as institutional inertia.

---

## Turn Structure

Each turn follows this sequence. Reference the Roguelike Layout from `references/output-formats.md` for rendering.

1. **Generate AI actor actions** before presenting to user (information asymmetry mitigation)
2. **Render situation brief** using the Roguelike Layout
3. **Present actor actions** with visible effects on game state
4. **Present decision menu** (3+ options plus custom action slot)
5. **Receive user choice**
6. **Adjudicate** using the protocol below
7. **Generate unexpected consequences** (mandatory, at least one per turn)
8. **Update actor states** (objectives, resources, relationships, information)
9. **Save turn** to journal file immediately
10. **Render visualizations** per `references/visualizations.md` (at minimum: actor status table and resource bars)

---

## Adjudication Protocol

Matrix Game style with emergence. Apply to every action — user and AI actors alike.

1. **Action** — state the action taken and the actor taking it.
2. **Argument for success** — strongest case why this succeeds, grounded in actor resources, position, and situation.
3. **Counter-argument** — strongest case why it fails or backfires, grounded in opposition capabilities, friction, and information gaps.
4. **Plausibility assessment** — exact mapping:

| Assessment | Condition | Outcome |
|------------|-----------|---------|
| **Strong** | Argument clearly dominates counter-argument | Succeeds fully; intended effects realized |
| **Moderate** | Argument and counter-argument balanced | Partial success with complications (specify the complication) |
| **Weak** | Counter-argument dominates argument | Fails or backfires (specify how) |

**Anti-escalation check (integrated):** Before finalizing, ask: "Am I defaulting to a more dramatic or aggressive outcome than warranted?" If yes, re-assess at one level lower intensity.

**Anti-blue-bias check (integrated):** When adjudicating adversary actions, ask: "Am I underestimating this adversary's capability or resolve?" Calibrate upward if necessary.

5. **Second-order cascade** — trace at least one consequence that ripples beyond the immediate action into the broader game state.
6. **Unexpected consequences** — MANDATORY. Generate at least one emergent event that no player ordered but logically follows from the situation. This is the Snow Globe architecture's key innovation.

Examples: a third party reacts, public opinion shifts, a resource becomes scarce, an alliance fractures, a previously uninvolved stakeholder enters the game.

**Anti-farcical-harmony check (integrated):** After generating all actor actions for a turn, verify at least one actor genuinely disagrees with the prevailing direction. If none do, revise the actor whose persona most supports disagreement.

**Anti-positional-bias check (integrated):** Randomize the order in which actor actions are generated between turns.

---

## Monte Carlo Iteration Protocol

When the user requests "explore N variations" (default N=10). This is the single highest-value AI-unique feature (CGSC research: 9 wargame turns amplified to 900 via Monte Carlo exploration).

1. Take the current decision point and the user's proposed action.
2. Run N iterations with probabilistic variation: vary actor responses, random events, and plausibility rolls.
3. Classify outcomes into 3-5 clusters.
4. Present as distribution table:

| Cluster | Frequency | Key Differentiator | Representative Narrative |
|---------|-----------|-------------------|------------------------|
| {name} | `{N}%` | {what makes this cluster distinct} | {one-sentence story} |

5. Highlight the most sensitive variable — which single factor most changes the outcome distribution.
6. Label as exploratory (RAND guardrail): "Heuristic estimates, not statistical simulations."
7. Return to the actual turn — user still makes their choice.

---

## Information Asymmetry Rules

Best-effort convention. Acknowledge that LLMs cannot truly hide information from themselves.

- Generate actor actions BEFORE composing the user briefing.
- Explicitly state what the user's character does NOT know.
- Never reveal adversary internal deliberations unless the user has an intelligence capability justifying access.
- State in the setup phase: "This is simulation, not true fog of war. AI actors optimize for their goals, but information separation is best-effort."

---

## Inject Design

Pre-seed 3-5 injects during the setup phase. Deploy at dramatically appropriate moments, not on a fixed schedule.

### Requirements
- At least 1 inject must be POSITIVE (unexpected opportunity, not just crisis).
- Injects must create DILEMMAS — force trade-offs between competing objectives, not just complications.
- Each inject needs: event description, immediate pressure, the dilemma it creates, response deadline (in turns).

### Example Inject

> **Event:** Your largest customer (30% of revenue) announces they are evaluating your competitor's product. Simultaneously, your VP of Engineering reports a breakthrough on the next-gen feature — 3 months from ready.
> **Pressure:** Revenue concentration risk is now active. Board will ask about retention at next meeting.
> **Dilemma:** Divert engineering resources to rush a retention package (risking the breakthrough timeline) OR stay the course on next-gen (risking the customer).
> **Deadline:** Respond by Turn N+2 or the customer begins formal evaluation.

---

## AAR Protocol

Never skip the After Action Review — this is where learning happens. Generate Mermaid timeline (campaign phases) and decision tree (key branch points) in the journal per `references/visualizations.md`.

For AAR structure and rendering template, see `references/output-formats.md` (AAR Display section). The output-formats template is the single source of truth for AAR content and layout.
