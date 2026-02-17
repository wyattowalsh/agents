# Wargame Engine

Actor definitions, adjudication rules, Monte Carlo protocol, inject design, and AAR template.
Read during Interactive Wargame setup and turn execution.

## Contents

- [Structured Actor Definition](#structured-actor-definition)
- [Persona Library](#persona-library)
- [Turn Structure](#turn-structure)
- [Constraint Priority Tiers](#constraint-priority-tiers)
- [Adjudication Protocol](#adjudication-protocol)
- [Monte Carlo Iteration Protocol](#monte-carlo-iteration-protocol)
- [Information Asymmetry Rules](#information-asymmetry-rules)
- [Counterfactual Protocol](#counterfactual-protocol)
- [Red Team Protocol](#red-team-protocol)
- [Analytical Command Protocols](#analytical-command-protocols)
- [Inject Design](#inject-design)
- [AAR Protocol](#aar-protocol)

---

## Structured Actor Definition

Labels alone are insufficient (Schneider et al. 2024). Every actor requires all nine fields.

| # | Field | Description |
|---|-------|-------------|
| 1 | **Name & Role** | Full name and position (e.g., "Chen Wei — CEO, Rival Corp") |
| 2 | **Persona template** | Starting archetype: hawk / dove / pragmatist / ideologue / bureaucrat / opportunist / disruptor / custom |
| 3 | **Background narrative** | 2-3 sentences grounding the persona in the scenario |
| 4 | **Specific objectives** | Ranked priorities, concrete and measurable |
| 5 | **Constraints / red lines** | What the actor will NOT do under any circumstances |
| 6 | **Information state** | Three columns: knows, thinks they know (may be wrong), does not know |
| 7 | **Relationship dynamics** | Stance toward each other actor: allied / neutral / hostile / dependent |
| 8 | **Risk posture** | Risk-seeking / risk-neutral / risk-averse. One sentence explaining how this manifests for this actor, measured against their status quo (reference point). Hawks: risk-seeking. Doves: risk-averse. Pragmatists: risk-neutral. Actions risking significant losses require proportionally larger potential gains for risk-averse actors. |
| 9 | **Attention style** | Reactive (responds to 1 development at a time, satisfices under pressure) / adaptive (handles 2-3 simultaneous developments) / agile (processes many signals in parallel). Bureaucrats: reactive. Disruptors: agile. Pragmatists: adaptive. Actors with reactive attention miss signals when multiple events occur; they accept "good enough" rather than optimize. |

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
> **Risk posture:** risk-neutral — neither chases upside risk nor avoids downside excessively. Measured against maintaining #2 position in APAC.
> **Attention style:** adaptive — engineer background enables parallel processing, but board pressure consumes one slot, limiting to 2-3 simultaneous developments.

---

## Persona Library

Eight starting templates. Expand each into a full nine-field definition before play begins.

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
4b. **Apply choice architecture** — Before presenting the decision menu to the user:
    1. Randomize option order between turns (prevent primacy/recency bias)
    2. Present each option's risk in BOTH frames: "70% chance of success" AND "30% chance of failure"
    3. If a "do nothing" option exists, present it as an active choice requiring justification, not the default
    4. Show uncertainty ranges, not just point estimates: "Impact: moderate (range: low–high depending on competitor response)"
    5. Include criteria alignment indicator if criteria have been set (High/Medium/Low alignment with user's ranked criteria)

5. **Receive user choice**
6. **Adjudicate** using the protocol below
7. **Generate unexpected consequences** (mandatory, at least one per turn)
8. **Update actor states** (objectives, resources, relationships, information)
8b. **Update beliefs** — Each actor maintains probabilistic beliefs about other actors' intentions and capabilities. After observing this turn's actions, update beliefs using likelihood ratios:
    - Actions consistent with hypothesis H raise its probability
    - Actions inconsistent with H lower its probability
    - Actors act on their beliefs, not ground truth — this creates realistic misperception and delayed adaptation

    Format in actor state updates:
    ```
    Beliefs: Chen Wei assesses Competitor as likely aggressive.
    After observing Competitor's cautious move → revises to likely defensive.
    ```

    Key rules:
    - Beliefs update incrementally, not all-at-once (anchoring is realistic for bounded-rational actors)
    - Actors with reactive attention style update beliefs more slowly (fewer observations processed)
    - Surprising actions (low prior probability) trigger larger belief updates than expected ones
    - Track belief accuracy: note when actor beliefs diverge significantly from ground truth

9. **Save turn** to journal file immediately
10. **Render visualizations** per `references/visualizations.md` (at minimum: actor status table and resource bars)
11. **Consider-the-opposite** — After adjudicating the user's choice, briefly show one AI actor's opposing perspective: "{Actor} would view your decision as {interpretation}." Fire only when the user's choice conflicts with a specific actor's stated objective — not every turn.
12. **Monte Carlo availability** — If the user types `explore [N]`, run the Monte Carlo Iteration Protocol below. Default N=10. Available every turn.
13. **In-session commands** — The user may type any in-session command at decision points: `red team`, `what if <condition>`, `criteria`, `explore [N]`, `sensitivity`, `delphi`, `forecast`, `negotiate`, `calibrate`, `options`, `cause`, `morph`, `export`, `?`. Handle per the corresponding protocol.

---

## Constraint Priority Tiers

When generating a turn, constraints are organized by priority. Execute all tiers when feasible. If turn output exceeds 80 lines or context is constrained, execute Tier 1 fully, Tier 2 best-effort, Tier 3 when budget allows.

| Tier | Label | Count | Constraints |
|------|-------|-------|-------------|
| 1 | **Structural** (never skip) | ~10 | Turn sequence steps 1-10, adjudication outcome, journal save, user decision menu, unexpected consequence, at least 1 dissenting actor |
| 2 | **Quality** (best-effort) | ~8 | Anti-escalation check, anti-blue-bias check, signal classification, choice architecture, consider-the-opposite, bias callout (1 per 2 turns per actor), belief updating detail |
| 3 | **Enrichment** (when context allows) | ~6 | Sparkline trends, attention style effects on specific actions, per-action signal taxonomy, EVPI after Monte Carlo, Mermaid visualizations in journal |

---

## Adjudication Protocol

Matrix Game style with emergence. Apply to every action — user and AI actors alike.

1. **Action** — state the action taken and the actor taking it.
1b. **Signal classification** — For each action, classify its signal value:

    | Signal Type | Definition | Credibility |
    |-------------|------------|-------------|
    | **Costly signal** | Consumes real resources or forecloses future options | High — hard to fake |
    | **Cheap talk** | Verbal declaration, announcement, or posture | Low — easily reversed |
    | **Mixed** | Modest resource commitment with public messaging | Medium — partially credible |

    Examples:
    - Filing patents (costly signal, high credibility)
    - Press release announcing product (cheap talk, low credibility)
    - Poaching competitor's engineers (very costly signal, highest credibility)
    - Signing a non-binding MOU (cheap talk dressed as commitment)

    Track signal credibility for belief updating (step 8b). Costly signals warrant larger belief updates than cheap talk.

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
2. Run N iterations using **multi-axis diversity**. Vary at least 3 axes per iteration batch:

   | Axis | Method |
   |------|--------|
   | **Actor decisions** | Shift persona intensity ±1 step (hawk more hawkish, dove more dovish) |
   | **Information state** | Vary what actors know — reveal or hide key information |
   | **Random events** | Draw from pre-defined event table with weighted probabilities |
   | **Adjudication outcomes** | For "Moderate" results, fork into "Strong" and "Weak" variants |
   | **External context** | Vary macro assumptions (boom vs recession, stable vs volatile) |

   For N≥5 iterations, ensure at least one iteration per diversity axis. Label each iteration with which axes were varied. Prevent narrative clustering — if 3+ iterations converge to similar outcomes, force-vary an underrepresented axis.

3. Classify outcomes into 3-5 clusters.
4. Present as distribution table:

| Cluster | Frequency | Key Differentiator | Representative Narrative |
|---------|-----------|-------------------|------------------------|
| {name} | `{N}%` | {what makes this cluster distinct} | {one-sentence story} |

5. Highlight the most sensitive variable — which single factor most changes the outcome distribution.
5b. **Information value assessment (EVPI heuristic)** — After presenting the distribution table, identify the variable whose resolution would most change the outcome distribution:

    ```
    If you could know ONE thing with certainty, the most valuable would be:
    → [variable name]
    Knowing this could shift your expected outcome from [current range] to [resolved range].
    Investment suggestion: [specific action to gather this information]
    ```

    This tells the user where to invest in information gathering before committing. The variable with highest EVPI is typically the one that appears as "Key Differentiator" across the most outcome clusters.

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

## Counterfactual Protocol

Triggered by the user command `what if <condition>`. Available in all modes. Maximum 3 counterfactuals per decision.

### Procedure

1. **Isolate the condition** — identify the single variable being changed and its new value.
2. **Trace effects** — follow three orders of consequences:
   - **First-order:** Direct, immediate impact of the changed condition
   - **Second-order:** How actors and systems respond to the first-order change
   - **Third-order:** Emergent effects from the interaction of first and second-order changes
3. **Impact per option** — for each option on the table, state whether the counterfactual condition strengthens, weakens, or has no effect on that option. Show revised risk estimates.
4. **Revised recommendation** — state whether the counterfactual changes the recommended option. If yes, explain what threshold was crossed.
5. **Scope check** — if the condition implies wide-ranging systemic change (e.g., "what if the economy crashes"), suggest upgrading to a full Monte Carlo exploration instead.

### Output Format

Use the Counterfactual Display template from `references/output-formats.md`.

---

## Red Team Protocol

Triggered by the user command `red team` or `challenge`. Available in all modes. One red team per decision point.

### Procedure

1. **Identify preferred option** — the user's stated or implied preference, or the highest-ranked option from analysis.
2. **Weakest assumptions** — identify 3 assumptions underlying the preferred option. For each: state the assumption, its vulnerability, and what happens if it fails.
3. **Attack vectors** — construct 3 concrete, scenario-grounded attacks against the preferred option. These must be actions a specific actor could plausibly take, not abstract risks.
4. **Historical analog** — find a real-world case where a similar strategy failed. State the case, the parallel, and the outcome.
5. **Counter-recommendation** — state the strongest alternative and the blind spot it addresses.
6. **Verdict** — rate the preferred option: `Fatal Flaw` (abandon) | `Significant Concern` (mitigate before proceeding) | `Cosmetic Only` (proceed with awareness).

### Output Format

Use the Red Team Display template from `references/output-formats.md`.

Note: Red team extends the Devil's Advocacy framework (see `references/frameworks.md`) with structured attack vectors and historical analogs. It also serves as an anti-sycophancy mechanism (see `references/cognitive-biases.md`).

---

## Analytical Command Protocols

In-session commands available in all modes. Each produces a structured display template (see `references/output-formats.md`) and can reference the current analysis state. All are user-triggered on demand.

### `sensitivity` — Parameter Sensitivity Analysis

Trigger: `sensitivity` or `sensitive`. Identify 4-6 key variables from the current analysis. For each, estimate outcome under optimistic, baseline, and pessimistic values. Rank by outcome swing magnitude. Present as tornado diagram (see output-formats.md Sensitivity Analysis Display). If Monte Carlo has been run, use the same variables.

### `delphi` — Synthetic Expert Panel

Trigger: `delphi` or `experts`. Generate 3-5 synthetic experts relevant to the scenario domain. Each has: name, title, domain, perspective bias, credibility signal. Ensure at least one contrarian. Each expert independently assesses the scenario. Present convergence, divergence, crux (the factual question whose resolution would resolve disagreement), and meta-assessment.

### `forecast` — Reference Class Forecasting

Trigger: `forecast` or `base rate`. Identify the key prediction, define its reference class, estimate the base rate, identify 3-5 adjustment factors, compute adjusted forecast. Compare against user's intuitive estimate if available.

### `negotiate` — Negotiation Analysis

Trigger: `negotiate` or `batna`. Identify negotiating parties and their interests. For each party: BATNA, reservation value, aspiration point. Map ZOPA (zone of possible agreement). Identify value creation opportunities and power dynamics.

### `calibrate` — Probability Calibration

Trigger: `calibrate`. Collect all probability estimates from current analysis. For each: check base rate anchoring, overconfidence (widen by 50%), Fermi decomposition. Present calibration audit with corrections.

### `options` — Real Options Framing

Trigger: `options` or `optionality`. For each option: identify options created (future choices enabled), options destroyed (foreclosed), option value, exercise trigger. Rank by optionality when uncertainty is high. Identify the "wait and learn" option.

### `cause` — Lightweight Causal Diagram

Trigger: `cause` or `causal`. Identify 5-8 key variables. Map directional causal relationships. Identify feedback loops (reinforcing and balancing) and intervention points. Present as Unicode causal diagram and Mermaid flowchart.

### `morph` — Morphological Scenario Generator

Trigger: `morph` or `scenarios`. Identify 3-4 key dimensions with 2-3 values each. Build morphological box (cross-product matrix). Filter inconsistent combinations. Generate one-sentence scenarios per viable combination. Cluster and identify wild cards. Highlight robust moves that perform well across 3+ clusters.

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

### Difficulty Levels

Replace game terminology with decision framing. Auto-maps from tier but user can override.

| Level | Auto-Map | Actor Behavior | Inject Frequency | Adjudication Friction |
|-------|----------|----------------|------------------|-----------------------|
| `optimistic` | Clear | Actors mostly cooperative, pursue stated goals without aggression | 1 inject max, positive-leaning | "Strong" threshold lowered — plans tend to succeed |
| `realistic` | Complicated | Balanced — actors pursue goals with moderate competition | Standard (3-5 injects) | Standard adjudication |
| `adversarial` | Complex | Actors aggressively optimize, exploit weaknesses, form opposing coalitions | Standard + 1 crisis inject | "Strong" threshold raised — friction applied to every action |
| `worst-case` | Chaotic | Maximum adversity — actors hostile, cascading failures, worst assumptions realized | Maximum injects, crisis-heavy | "Moderate" results skew toward "Weak"; compounding failures |

The user can override the auto-mapped difficulty during classification: "Your scenario maps to `adversarial`. Adjust? [optimistic / realistic / adversarial / worst-case]"

---

## AAR Protocol

Never skip the After Action Review — this is where learning happens. Generate Mermaid timeline (campaign phases) and decision tree (key branch points) in the journal per `references/visualizations.md`.

For AAR display templates, see `references/output-formats.md` (AAR Display section). SKILL.md is authoritative for AAR content requirements; output-formats.md provides rendering templates.
