# Experiment Design Patterns

## Contents

1. [A/B Test Design](#ab-test-design)
2. [Power Analysis](#power-analysis)
3. [CUPED Variance Reduction](#cuped-variance-reduction)
4. [Multiple Comparisons](#multiple-comparisons)
5. [Common Pitfalls](#common-pitfalls)
6. [Advanced Designs](#advanced-designs)

---

## A/B Test Design

### Experiment brief template

1. **Hypothesis:** "[Change X] will [increase/decrease] [metric Y] by [Z%] for [population]"
2. **Primary metric:** The one metric that determines success/failure
3. **Guardrail metrics:** Metrics that must NOT degrade (e.g., latency, error rate)
4. **Secondary metrics:** Nice-to-know metrics for deeper understanding
5. **Randomization unit:** User, session, device, page view
6. **Population:** Who is eligible? Exclusion criteria?
7. **Duration:** Minimum days to run (power calculation + weekly cycles)
8. **Sample size:** From power analysis
9. **Decision criteria:** What p-value and effect size trigger a launch decision?

### Metric selection

| Metric Type | Role | Example |
|-------------|------|---------|
| Primary | Decision metric | Conversion rate, revenue per user |
| Guardrail | Must not degrade | Page load time, error rate, churn |
| Secondary | Explanatory | Click-through rate, session duration |
| Diagnostic | Debug only | Feature usage, funnel step completion |

**Good primary metrics:**
- Sensitive enough to detect the expected effect
- Not too noisy (high variance = need more samples)
- Directly tied to business value
- Not easily gamed

---

## Power Analysis

### Key parameters

| Parameter | Symbol | Typical Values |
|-----------|--------|---------------|
| Significance level | alpha | 0.05 (standard), 0.01 (conservative) |
| Power | 1 - beta | 0.80 (standard), 0.90 (high-stakes) |
| Minimum detectable effect | MDE | Business-determined — smallest change worth detecting |
| Baseline rate | p0 | Current conversion rate, mean metric value |
| Variance | sigma^2 | From historical data |

### Sample size formulas

**Proportions (conversion rates):**

```
n_per_group = (Z_alpha/2 + Z_beta)^2 * (p1*(1-p1) + p2*(1-p2)) / (p2 - p1)^2
```

**Means (continuous metrics):**

```
n_per_group = (Z_alpha/2 + Z_beta)^2 * 2 * sigma^2 / delta^2
```

**Python implementation:**

```python
from scipy import stats
import numpy as np

def sample_size_proportions(p0, mde, alpha=0.05, power=0.80):
    p1 = p0 + mde
    z_alpha = stats.norm.ppf(1 - alpha/2)
    z_beta = stats.norm.ppf(power)
    n = (z_alpha + z_beta)**2 * (p0*(1-p0) + p1*(1-p1)) / mde**2
    return int(np.ceil(n))

def sample_size_means(sigma, mde, alpha=0.05, power=0.80):
    z_alpha = stats.norm.ppf(1 - alpha/2)
    z_beta = stats.norm.ppf(power)
    n = (z_alpha + z_beta)**2 * 2 * sigma**2 / mde**2
    return int(np.ceil(n))
```

### Duration calculation

```
duration_days = n_per_group * 2 / daily_eligible_traffic
```

Minimum: 2 full weeks (capture weekly cycles). Maximum: 6-8 weeks (avoid novelty effects plateauing).

---

## CUPED Variance Reduction

Controlled-experiment Using Pre-Experiment Data. Reduces variance by regressing out pre-experiment signal.

### How it works

```
Y_cuped = Y - theta * X
theta = Cov(Y, X) / Var(X)
```

Where X is the pre-experiment value of the same metric (or a correlated proxy).

### Benefits

- Reduces variance by 20-50% typically
- Equivalent to running the experiment 1.5-2x longer
- No bias introduced (X is pre-experiment, independent of treatment)

### Requirements

- Pre-experiment data available for the same metric
- Correlation between pre and post values (higher = more variance reduction)
- Same randomization unit in pre and post periods

### Variance reduction estimate

```
variance_reduction = r^2 (correlation squared between pre and post)
```

| Pre-post correlation | Variance reduction | Equivalent sample increase |
|---------------------|-------------------|--------------------------|
| 0.3 | 9% | 1.1x |
| 0.5 | 25% | 1.3x |
| 0.7 | 49% | 2.0x |
| 0.9 | 81% | 5.3x |

---

## Multiple Comparisons

When testing multiple variants or metrics simultaneously:

| Scenario | Correction | Method |
|----------|-----------|--------|
| 3-4 variants | Bonferroni | alpha / n_comparisons |
| Many metrics | Benjamini-Hochberg | FDR control |
| Primary + guardrails | No correction on primary, Bonferroni on guardrails | Standard practice |
| Sequential testing | Alpha spending function | Group sequential design |

**Practical approach:**
1. One primary metric — no correction needed
2. Guardrail metrics — Bonferroni correction
3. Secondary metrics — report as exploratory, no correction, note multiple testing

---

## Common Pitfalls

| Pitfall | Problem | Prevention |
|---------|---------|-----------|
| Peeking | Checking results early inflates false positives | Use sequential testing or pre-commit to duration |
| Novelty effects | Users react to newness, not the change itself | Run for 2+ weeks, segment by new vs returning |
| Simpson's paradox | Effect reverses when data is segmented | Pre-register segments, check heterogeneity |
| Survivorship bias | Only analyzing users who complete the funnel | Intent-to-treat analysis — include all randomized |
| Interference | Treatment users affect control users | Use cluster randomization or geo experiments |
| Underpowered test | Can't detect real effects → false negatives | Always run power analysis before starting |
| Metric gaming | Optimizing for metric, not user value | Use guardrail metrics and qualitative checks |

---

## Advanced Designs

### Multi-armed bandit

- **When:** Many variants, want to minimize regret during experiment
- **Trade-off:** Faster convergence but less statistical rigor than fixed-horizon A/B
- **Algorithms:** Thompson Sampling, UCB1, Epsilon-Greedy

### Switchback experiments

- **When:** Interference between users (marketplace, social network)
- **Method:** Alternate treatment/control across time periods within clusters
- **Analysis:** Mixed-effects model accounting for time and cluster

### Interleaving

- **When:** Ranking/recommendation systems
- **Method:** Mix treatment and control recommendations in same results page
- **Benefit:** Much more sensitive than between-subject A/B tests
