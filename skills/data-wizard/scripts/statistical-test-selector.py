#!/usr/bin/env python3
"""Guided statistical test selection. Stdlib only.

Input (JSON via stdin or --input):
  {
    "data_type": "continuous|categorical|ordinal|binary|count",
    "groups": 1|2|3+,
    "paired": true|false,
    "normality": "yes|no|unknown",
    "goal": "difference|association|correlation|proportion"  (optional)
  }

Output: JSON with recommended test, alternatives, and assumptions.
"""

import argparse
import json
import sys

DECISION_TREE = {
    ("continuous", 1, False, "yes"): {
        "test": "One-Sample t-test",
        "alternatives": ["One-Sample Wilcoxon Signed-Rank (if normality violated)"],
        "assumptions": ["Data is normally distributed", "Observations are independent", "Continuous outcome variable"],
        "when_to_use": "Compare sample mean to a known population mean",
        "effect_size": "Cohen's d = (mean - mu) / sd",
    },
    ("continuous", 2, False, "yes"): {
        "test": "Independent Samples t-test",
        "alternatives": ["Welch's t-test (unequal variances)", "Mann-Whitney U (non-normal)"],
        "assumptions": ["Both groups normally distributed", "Independent observations", "Equal variances (Levene's test)"],
        "when_to_use": "Compare means of two independent groups",
        "effect_size": "Cohen's d = (mean1 - mean2) / pooled_sd",
    },
    ("continuous", 2, True, "yes"): {
        "test": "Paired t-test",
        "alternatives": ["Wilcoxon Signed-Rank (non-normal)"],
        "assumptions": ["Differences are normally distributed", "Pairs are independent of each other"],
        "when_to_use": "Compare means of two related measurements (before/after, matched pairs)",
        "effect_size": "Cohen's d = mean_diff / sd_diff",
    },
    ("continuous", 2, False, "no"): {
        "test": "Mann-Whitney U test",
        "alternatives": ["Permutation test", "Bootstrap confidence interval"],
        "assumptions": ["Independent observations", "Similar distribution shapes (for median comparison)"],
        "when_to_use": "Compare two independent groups when normality is violated",
        "effect_size": "Rank-biserial correlation r = 1 - 2U/(n1*n2)",
    },
    ("continuous", 2, True, "no"): {
        "test": "Wilcoxon Signed-Rank test",
        "alternatives": ["Sign test (fewer assumptions)", "Permutation test"],
        "assumptions": ["Paired observations", "Symmetric distribution of differences"],
        "when_to_use": "Compare two related measurements when normality is violated",
        "effect_size": "r = Z / sqrt(N)",
    },
    ("continuous", 3, False, "yes"): {
        "test": "One-Way ANOVA",
        "alternatives": ["Welch's ANOVA (unequal variances)", "Kruskal-Wallis (non-normal)"],
        "assumptions": ["Normal distribution within groups", "Equal variances (Levene's test)", "Independent observations"],
        "when_to_use": "Compare means of 3+ independent groups",
        "effect_size": "Eta-squared = SS_between / SS_total",
        "post_hoc": "Tukey HSD for pairwise comparisons",
    },
    ("continuous", 3, False, "no"): {
        "test": "Kruskal-Wallis H test",
        "alternatives": ["Permutation ANOVA", "Bootstrap"],
        "assumptions": ["Independent observations", "Similar distribution shapes across groups"],
        "when_to_use": "Compare 3+ independent groups when normality is violated",
        "effect_size": "Epsilon-squared = H / (n-1)",
        "post_hoc": "Dunn's test for pairwise comparisons",
    },
    ("continuous", 3, True, "yes"): {
        "test": "Repeated Measures ANOVA",
        "alternatives": ["Friedman test (non-normal)"],
        "assumptions": ["Sphericity (Mauchly's test)", "Normal distribution", "No significant outliers"],
        "when_to_use": "Compare 3+ related measurements on the same subjects",
        "effect_size": "Partial eta-squared",
        "post_hoc": "Bonferroni-corrected paired t-tests",
    },
    ("continuous", 3, True, "no"): {
        "test": "Friedman test",
        "alternatives": ["Permutation test for repeated measures"],
        "assumptions": ["Paired/related groups", "Ordinal or continuous outcome"],
        "when_to_use": "Compare 3+ related measurements when normality is violated",
        "effect_size": "Kendall's W",
        "post_hoc": "Nemenyi test for pairwise comparisons",
    },
    ("categorical", 2, False, "no"): {
        "test": "Chi-Square Test of Independence",
        "alternatives": ["Fisher's Exact Test (small samples, 2x2)", "Barnard's Exact Test"],
        "assumptions": ["Expected cell counts >= 5", "Independent observations"],
        "when_to_use": "Test association between two categorical variables",
        "effect_size": "Cramer's V = sqrt(chi2 / (n * min(r-1, c-1)))",
    },
    ("binary", 2, False, "no"): {
        "test": "Chi-Square Test / Fisher's Exact Test",
        "alternatives": ["Z-test for proportions (large samples)", "McNemar's test (paired)"],
        "assumptions": ["Independent observations", "Expected counts >= 5 for chi-square"],
        "when_to_use": "Compare proportions between two groups",
        "effect_size": "Odds ratio or relative risk",
    },
    ("binary", 2, True, "no"): {
        "test": "McNemar's test",
        "alternatives": ["Cochran's Q (3+ paired groups)"],
        "assumptions": ["Paired binary observations", "Sufficient discordant pairs"],
        "when_to_use": "Compare paired proportions (before/after on same subjects)",
        "effect_size": "Odds ratio of discordant pairs",
    },
    ("ordinal", 2, False, "no"): {
        "test": "Mann-Whitney U test",
        "alternatives": ["Kolmogorov-Smirnov test (distribution comparison)"],
        "assumptions": ["Independent observations", "Ordinal or continuous data"],
        "when_to_use": "Compare two groups on an ordinal scale",
        "effect_size": "Rank-biserial correlation",
    },
    ("count", 1, False, "no"): {
        "test": "Chi-Square Goodness of Fit",
        "alternatives": ["G-test (log-likelihood ratio)", "Exact multinomial test"],
        "assumptions": ["Expected counts >= 5", "Independent observations"],
        "when_to_use": "Test if observed counts match expected distribution",
        "effect_size": "Cramer's V",
    },
}

CORRELATION_TESTS = {
    ("continuous", "continuous", "yes"): {
        "test": "Pearson correlation",
        "assumptions": ["Bivariate normality", "Linear relationship", "No significant outliers"],
        "effect_size": "r (small: 0.1, medium: 0.3, large: 0.5)",
    },
    ("continuous", "continuous", "no"): {
        "test": "Spearman rank correlation",
        "assumptions": ["Monotonic relationship", "Ordinal or continuous data"],
        "effect_size": "rho (same thresholds as Pearson)",
    },
    ("ordinal", "ordinal", "no"): {
        "test": "Kendall's tau",
        "assumptions": ["Ordinal data", "Better for small samples with ties"],
        "effect_size": "tau",
    },
}


def select_test(params: dict) -> dict:
    data_type = params.get("data_type", "continuous")
    groups = params.get("groups", 2)
    paired = params.get("paired", False)
    normality = params.get("normality", "unknown")
    goal = params.get("goal", "difference")

    if normality == "unknown":
        normality = "no"
        normality_note = "Normality unknown: defaulting to non-parametric. Run Shapiro-Wilk test to verify."
    else:
        normality_note = None

    if groups > 3:
        groups = 3

    if goal == "correlation":
        key = (data_type, data_type, normality)
        result = CORRELATION_TESTS.get(key, CORRELATION_TESTS.get(("continuous", "continuous", "no")))
        result = dict(result)
        result["goal"] = "correlation"
        if groups and groups > 2:
            result["warning"] = f"groups={groups} ignored for correlation goal (only pairwise supported)"
        if normality_note:
            result["normality_note"] = normality_note
        return result

    key = (data_type, groups, paired, normality)
    result = DECISION_TREE.get(key)

    if not result:
        # Fallback: try without normality constraint
        for norm in ["no", "yes"]:
            fallback_key = (data_type, groups, paired, norm)
            if fallback_key in DECISION_TREE:
                result = dict(DECISION_TREE[fallback_key])
                result["fallback_note"] = f"Exact match not found. Using {norm}-normality variant."
                break

    if not result:
        return {
            "error": "No matching test found",
            "params": params,
            "suggestion": "Try specifying data_type, groups, paired, and normality more precisely",
        }

    result = dict(result)
    result["input_params"] = params
    if normality_note:
        result["normality_note"] = normality_note

    return result


def main():
    parser = argparse.ArgumentParser(description="Select appropriate statistical test")
    parser.add_argument("--input", help="JSON string or file path with test parameters")
    args = parser.parse_args()

    if args.input:
        try:
            params = json.loads(args.input)
        except json.JSONDecodeError:
            with open(args.input) as f:
                params = json.load(f)
    else:
        params = json.load(sys.stdin)

    result = select_test(params)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
