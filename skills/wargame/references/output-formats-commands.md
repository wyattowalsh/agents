# Output Formats — Analytical Commands

Display templates for in-session analytical commands. Read only when the specific command is invoked.

## Red Team Display

Triggered by `red team` or `challenge` command. One per decision point.

```
## Red Team — Case Against: {preferred option}

### Weakest Assumptions
| Assumption | Vulnerability | If Wrong |
|------------|---------------|----------|
| {assumption 1} | {how it could fail} | {consequence} |
| {assumption 2} | {how it could fail} | {consequence} |
| {assumption 3} | {how it could fail} | {consequence} |

### Attack Vectors
1. **{Actor} could:** {specific, scenario-grounded action that undermines the preferred option}
2. **{Actor} could:** {second attack vector}
3. **{Actor} could:** {third attack vector}

### Historical Analog
**Case:** {real-world example where similar strategy failed}
**Parallel:** {what makes this analogous}
**Outcome:** {what happened}

### Counter-Recommendation
**Alternative:** {strongest alternative option}
**Blind spot it addresses:** {what the preferred option misses}

### Verdict: {Fatal Flaw | Significant Concern | Cosmetic Only}
{1-2 sentence justification}
```

Verdict box styling by severity:
- Fatal Flaw → `╔══╗` double border (danger)
- Significant Concern → `┌──┐` standard border (warning)
- Cosmetic Only → `╭──╮` rounded border (info)

## Counterfactual Display

Triggered by `what if <condition>` command. Maximum 3 per decision.

```
## What If: {condition}

### Effect Chain
- **First-order:** {direct, immediate impact}
- **Second-order:** {how actors and systems respond}
- **Third-order:** {emergent effects from interactions}

### Impact Per Option
| Option | Effect | Revised Risk | Direction |
|--------|--------|-------------|-----------|
| {A}    | {how this option is affected} | {new risk %} | ↑ stronger / ↓ weaker / → unchanged |
| {B}    | {how this option is affected} | {new risk %} | ↑ / ↓ / → |

### Revised Recommendation
{Does this change the recommended option? If yes, explain the threshold crossed. If no, explain why the recommendation is robust to this condition.}

> {If condition is wide-ranging: "This condition has systemic effects. Consider `explore N` for full Monte Carlo instead."}
```

## Sensitivity Panel

Shown after Monte Carlo results. Highlights highest-value information to gather.

```
### Information Value
If you could know ONE thing with certainty, the most valuable would be:
→ **{variable name}**
- Current expected outcome: `{range with variable uncertain}`
- If resolved: `{range with variable known}`
- Suggested investigation: {specific action to gather this information}
```

## Sensitivity Analysis Display

Triggered by `sensitivity` command.

```
## Sensitivity Analysis

Baseline outcome: {recommendation}

| Variable | Pessimistic → Optimistic | Outcome Swing |
|----------|--------------------------|---------------|
| {variable 1} | {pessimistic} → {optimistic} | ████████ High |
| {variable 2} | {pessimistic} → {optimistic} | █████░░░ Med  |
| {variable 3} | {pessimistic} → {optimistic} | ████░░░░ Med  |
| {variable 4} | {pessimistic} → {optimistic} | ██░░░░░░ Low  |

Most sensitive: {variable}
  If {condition}, switch from {Option A} to {Option B}.
  Investment to resolve: {specific action}
```

## Delphi Panel Display

Triggered by `delphi` or `experts` command.

```
## Delphi Panel

| Expert | Domain | Assessment | Confidence |
|--------|--------|------------|------------|
| {name} | {domain} | {assessment} | `{N}%` |

### Convergence
{shared assessment across experts}

### Divergence
{key disagreement and reasoning}

### Crux
If {factual question} is true → {Expert A}'s view prevails.
If false → {Expert B}'s view prevails.
Resolution cost: {how to find out}
```

## Forecast Display

Triggered by `forecast` or `base rate` command.

```
## Reference Class Forecast

**Prediction:** {what we're estimating}
**Reference class:** {category} — base rate: `{N}%`

### Adjustments
| Factor | Direction | Magnitude | Adjusted |
|--------|-----------|-----------|----------|
| {factor} | ↑/↓ | ±{N}% | `{N}%` |

**Final estimate:** `{N}%` (range: `{low}%` – `{high}%`)
**Calibration gap:** `{difference}` — {interpretation}
```

## Negotiation Analysis Display

Triggered by `negotiate` or `batna` command.

```
## Negotiation Analysis

### Parties
| Party | BATNA | Reservation | Aspiration | Power |
|-------|-------|-------------|------------|-------|
| {party} | {fallback} | {minimum} | {ideal} | {H/M/L} |

### Zone of Possible Agreement
ZOPA width: {narrow / moderate / wide}
{description of overlap}

### Value Creation Opportunities
- {issue where parties value differently}

### Recommended Strategy
1. {opening move}  2. {key concession to offer}  3. {key concession to seek}  4. {walk-away signal}
```

## Calibration Audit Display

Triggered by `calibrate` command.

```
## Calibration Audit

| Estimate | Value | Base Rate? | Decomposed? | Flag |
|----------|-------|------------|-------------|------|
| {prediction} | `{N}%` | {Yes/No} | {Yes/No} | {✓/⚠} |

### Corrections
- {estimate}: Base rate {N}%. After adjustments: `{N}%` (from `{N}%`)

### Overall Calibration
Your estimates skew {overconfident / underconfident / well-calibrated}.
Average correction: {direction and magnitude}.
```

## Real Options Display

Triggered by `options` or `optionality` command.

```
## Real Options Analysis

| Option | Creates | Destroys | Net Optionality | Exercise Trigger |
|--------|---------|----------|-----------------|------------------|
| {option} | {future choices} | {foreclosed} | `{High/Med/Low}` | {when to commit} |

### Optionality Ranking (under current uncertainty)
1. {option} — preserves {what}, costs {opportunity cost}

### Recommendation
Uncertainty level: {high / moderate / low}
When uncertainty is {level}: {preserve optionality / commit early}
```

## Causal Map Display

Triggered by `cause` or `causal` command.

```
## Causal Map

### Key Variables
1. {variable} — {current state}

### Causal Links
{A} ──(+)──→ {B}     (A increases B)
{B} ──(-)──→ {C}     (B decreases C)

### Feedback Loops
- ↻ **Reinforcing:** {A} → {B} → {A} — {description}
- ↺ **Balancing:** {C} → {D} → {C} — {description}

### Intervention Points
Best leverage: {variable} — influences {N} downstream variables
```

## Morphological Analysis Display

Triggered by `morph` or `scenarios` command.

```
## Morphological Analysis

### Dimensions
| Dimension | Value 1 | Value 2 | Value 3 |
|-----------|---------|---------|---------|
| {dimension} | {val} | {val} | {val} |

### Scenario Space
{N} combinations → {M} consistent → {K} clusters

### Key Scenarios
| # | Combo | Scenario | Probability | Best Move |
|---|-------|----------|-------------|-----------|
| 1 | {combo} | {narrative} | `{N}%` | {option} |

### Wild Card
{most surprising viable scenario} — probability `{N}%` but impact: {extreme}

### Robust Moves
{options performing well across 3+ clusters}
```

## Meta Analysis Display

Triggered by `meta` command. Cross-journal decision fitness report.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  DECISION FITNESS REPORT — {N} journals analyzed
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  BIAS PROFILE
  Most frequent: {bias_name} ({count} occurrences)
  Trend: {improving | stable | worsening}

  DOMAIN PERFORMANCE
  | Domain | Sessions | Avg Quality | Trend |
  |--------|----------|-------------|-------|
  | {domain} | {N} | {rating} | {↗↘→} |

  RISK TENDENCY
  Overall: {risk-seeking | balanced | risk-averse}
  Shift over time: {description}

  CALIBRATION
  Probability accuracy: {score}%
  Common error: {over/under-confidence in {domain}}

  TOP INSIGHT
  {most transferable principle from all journals}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Compare Display

Triggered by `compare` command. Side-by-side journal comparison.

```
╭── COMPARISON ─────────────────────────────────────────────────╮
│  Journal A: {title_a}                                         │
│  Journal B: {title_b}                                         │
╰───────────────────────────────────────────────────────────────╯

  DECISIONS
  | Turn | Journal A | Journal B | Better? |
  |------|-----------|-----------|---------|
  | {N}  | {choice}  | {choice}  | {A/B/=} |

  OUTCOMES
  | Criterion | Journal A | Journal B |
  |-----------|-----------|-----------|
  | {criterion} | {score} | {score} |

  DIVERGENCE POINTS
  - Turn {N}: A chose {x}, B chose {y} → {consequence difference}

  VERDICT: {which strategy dominated and why}
  Caveat: {what would change this assessment}
```

## Intelligence Research Display

Triggered by `research` command. Web intelligence briefing for current decision point.

```
╭── INTELLIGENCE RESEARCH ──────────────────────────────────────╮
│                                                                │
│  QUERY: {what was searched}                                    │
│                                                                │
│  KEY FINDINGS                                                  │
│  • {finding 1 — with source attribution}                       │
│  • {finding 2}                                                 │
│  • {finding 3}                                                 │
│                                                                │
│  RELEVANCE TO CURRENT DECISION                                 │
│  {how these findings affect the options on the table}          │
│                                                                │
│  CAVEAT: Web research is supplementary. Continue with          │
│  your decision or type ? for commands.                         │
╰────────────────────────────────────────────────────────────────╯
```

## Summary Display

Triggered by `summary` command. Condensed journal review (10-20 lines).

```
╭── JOURNAL SUMMARY ────────────────────────────────────────────╮
│  {scenario_title} — {tier} — {date}                           │
│  Turns: {N/M} │ Status: {status}                              │
├───────────────────────────────────────────────────────────────┤
│  KEY DECISIONS                                                │
│  T{N}: {decision} → {outcome}                                 │
│  T{N}: {decision} → {outcome}                                 │
│                                                               │
│  TOP INSIGHT                                                  │
│  {transferable principle}                                     │
│                                                               │
│  ACTION BRIDGE STATUS                                         │
│  Probe: {status}  Position: {status}  Commit: {status}        │
│                                                               │
│  ASSESSMENT: {what went well} / {what to do differently}      │
╰───────────────────────────────────────────────────────────────╯
```
