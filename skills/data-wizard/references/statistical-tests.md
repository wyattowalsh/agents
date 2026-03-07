# Statistical Tests Decision Guide

## Contents

1. [Test Selection Decision Tree](#test-selection-decision-tree)
2. [Parametric vs Non-Parametric](#parametric-vs-non-parametric)
3. [Assumption Checks](#assumption-checks)
4. [Effect Size Interpretation](#effect-size-interpretation)
5. [Multiple Comparisons](#multiple-comparisons)
6. [Common Mistakes](#common-mistakes)

---

## Test Selection Decision Tree

### Step 1: What is the goal?

| Goal | Next Question |
|------|--------------|
| Compare groups | How many groups? Paired or independent? |
| Test association | Both categorical? Both continuous? Mixed? |
| Test correlation | Normality? Linear or monotonic? |
| Compare proportions | How many groups? |
| Fit to distribution | Chi-square goodness of fit |

### Step 2: Data characteristics

Run `statistical-test-selector.py` with these parameters:
- `data_type`: continuous, categorical, ordinal, binary, count
- `groups`: number of groups being compared
- `paired`: are observations matched/repeated?
- `normality`: yes, no, or unknown (defaults to non-parametric)

### Step 3: Verify assumptions

Every test has assumptions. Violating them produces unreliable results.

---

## Parametric vs Non-Parametric

| Parametric | Non-Parametric | When to Use Non-Parametric |
|-----------|----------------|---------------------------|
| t-test | Mann-Whitney U | Non-normal data, small samples, ordinal data |
| Paired t-test | Wilcoxon Signed-Rank | Non-normal differences |
| ANOVA | Kruskal-Wallis | Non-normal groups, unequal variances |
| Pearson r | Spearman rho | Non-linear monotonic relationship, ordinal data |

**Rule of thumb:** With n > 30 per group and no severe skew, parametric tests are robust to non-normality (Central Limit Theorem). With n < 30, test normality explicitly.

---

## Assumption Checks

| Assumption | Test | Library | Threshold |
|-----------|------|---------|-----------|
| Normality | Shapiro-Wilk | `scipy.stats.shapiro` | p > 0.05 to accept normality |
| Normality (large n) | D'Agostino-Pearson | `scipy.stats.normaltest` | p > 0.05 |
| Equal variances | Levene's test | `scipy.stats.levene` | p > 0.05 for equal variances |
| Sphericity | Mauchly's test | `pingouin` | p > 0.05 for sphericity |
| Independence | Study design | — | Observations must not influence each other |
| Linearity | Scatter plot + residuals | visual | No curved pattern in residuals |

**When normality fails:**
1. Try data transformation (log, sqrt, Box-Cox)
2. Use non-parametric alternative
3. Use bootstrap confidence intervals

---

## Effect Size Interpretation

| Measure | Small | Medium | Large | Used With |
|---------|-------|--------|-------|-----------|
| Cohen's d | 0.2 | 0.5 | 0.8 | t-tests |
| Eta-squared | 0.01 | 0.06 | 0.14 | ANOVA |
| Cramer's V | 0.1 | 0.3 | 0.5 | Chi-square |
| Pearson r | 0.1 | 0.3 | 0.5 | Correlation |
| Odds ratio | 1.5 | 2.5 | 4.0 | Binary outcomes |

**Always report effect size alongside p-values.** A tiny p-value with a tiny effect size means statistically significant but practically irrelevant.

---

## Multiple Comparisons

When running multiple tests, false positive rate inflates:
- 20 tests at alpha=0.05 → expect 1 false positive by chance

| Correction | Method | When to Use |
|-----------|--------|-------------|
| Bonferroni | alpha / n_tests | Conservative, few comparisons |
| Holm-Bonferroni | Step-down Bonferroni | Less conservative, still controls FWER |
| Benjamini-Hochberg | FDR control | Many comparisons, discovery-oriented |
| Tukey HSD | Simultaneous CIs | Post-hoc after ANOVA |
| Dunn's test | Rank-based pairwise | Post-hoc after Kruskal-Wallis |

---

## Common Mistakes

1. **Treating p > 0.05 as proof of no effect** — absence of evidence is not evidence of absence. Report confidence intervals and power.
2. **Ignoring effect size** — large samples produce tiny p-values for trivial effects.
3. **Multiple testing without correction** — running many tests inflates false positives.
4. **Using parametric tests on ordinal data** — Likert scales are ordinal, not interval.
5. **Confusing correlation with causation** — observational data cannot establish causality without experimental design.
6. **Cherry-picking the test that gives significance** — pre-register analysis plan or use exploratory/confirmatory distinction.
7. **Ignoring sample size in normality tests** — Shapiro-Wilk rejects normality too easily with large n. Use visual inspection (Q-Q plot) alongside.
