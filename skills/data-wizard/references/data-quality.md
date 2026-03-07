# Data Quality Framework

## Contents

1. [Quality Dimensions](#quality-dimensions)
2. [Assessment Workflow](#assessment-workflow)
3. [Remediation Strategies](#remediation-strategies)
4. [Quality Scoring](#quality-scoring)

---

## Quality Dimensions

### Completeness (Weight: 25%)

Missing data patterns and their implications.

| Pattern | Detection | Impact |
|---------|----------|--------|
| MCAR (Missing Completely At Random) | Little's MCAR test | Safe to impute or drop |
| MAR (Missing At Random) | Conditional on observed data | Use model-based imputation |
| MNAR (Missing Not At Random) | Domain knowledge needed | May bias analysis significantly |

**Scoring:** `score = (1 - missing_cells / total_cells) * 100`

### Consistency (Weight: 20%)

| Check | Example | Fix |
|-------|---------|-----|
| Type uniformity | "123" and 123 in same column | Cast to consistent type |
| Format consistency | "2024-01-01" and "01/01/2024" | Standardize format |
| Case consistency | "New York", "new york", "NEW YORK" | Normalize casing |
| Unit consistency | Mixing kg and lbs | Convert to single unit |
| Cross-field consistency | State="CA" but ZIP starts with "1" | Flag for review |

### Accuracy (Weight: 20%)

| Check | Method | Threshold |
|-------|--------|-----------|
| Range violations | Domain-specific bounds | Flag values outside valid range |
| Statistical outliers | IQR method (3x IQR) | Flag extreme outliers |
| Reference validation | Check against master data | Flag mismatches |
| Semantic accuracy | Domain rules | E.g., age < 0, price < 0 |

### Timeliness (Weight: 15%)

| Check | Threshold | Action |
|-------|-----------|--------|
| Data freshness | Most recent record > N days old | Flag stale data |
| Temporal gaps | Missing time periods | Flag gaps |
| Update frequency | Expected vs actual | Alert on delayed updates |

### Uniqueness (Weight: 20%)

| Check | Method | Action |
|-------|--------|--------|
| Exact duplicates | `df.duplicated()` | Remove or investigate |
| Near-duplicates | Fuzzy matching on key fields | Review and merge |
| ID uniqueness | Check supposed-unique columns | Fix or re-key |

---

## Assessment Workflow

1. Run `data-quality-scorer.py <path>` for automated assessment
2. Review each dimension's score and issues
3. Prioritize fixes by weight and severity
4. Apply remediation strategies
5. Re-run scorer to verify improvement

### Interpreting the overall score

| Grade | Score | Interpretation |
|-------|-------|---------------|
| A | 90+ | Production-ready, minimal issues |
| B | 75-89 | Usable with minor cleanup |
| C | 60-74 | Needs significant cleaning before modeling |
| D | 40-59 | Major quality issues, investigate data source |
| F | < 40 | Unreliable, consider alternative data sources |

---

## Remediation Strategies

### Missing data remediation

| Strategy | When | Implementation |
|----------|------|---------------|
| Drop rows | Few missing, large dataset, MCAR | `df.dropna(subset=critical_cols)` |
| Drop columns | > 50% missing, not essential | `df.drop(columns=high_missing)` |
| Mean/median imputation | Numeric, MCAR, few missing | `SimpleImputer(strategy="median")` |
| Mode imputation | Categorical, few missing | `SimpleImputer(strategy="most_frequent")` |
| KNN imputation | MAR, related features exist | `KNNImputer(n_neighbors=5)` |
| Iterative imputation | Complex MAR patterns | `IterativeImputer()` |
| Domain value | Known default exists | E.g., 0 for count, "Unknown" for category |

### Outlier handling

| Strategy | When | Implementation |
|----------|------|---------------|
| Winsorize | Keep all data, cap extremes | Clip at 1st/99th percentile |
| Remove | Clear errors, small fraction | Filter rows beyond bounds |
| Transform | Skewed distribution | log, sqrt, Box-Cox |
| Separate model | Outliers are meaningful | Flag and model separately |
| Robust methods | Outliers expected | Use median-based stats, robust scaler |

### Duplicate handling

| Strategy | When | Implementation |
|----------|------|---------------|
| Drop exact duplicates | Clear duplicates | `df.drop_duplicates()` |
| Keep first/last | Temporal data with updates | `df.drop_duplicates(keep="last")` |
| Merge records | Near-duplicates with complementary info | Custom merge logic |
| Investigate | Unexpected duplicates | Check data pipeline for bugs |

---

## Quality Scoring

Run `data-quality-scorer.py` for automated scoring. The script computes:

```
overall_score = 0.25 * completeness + 0.20 * consistency +
                0.20 * accuracy + 0.15 * timeliness + 0.20 * uniqueness
```

Each dimension is scored 0-100 based on automated checks. The overall grade uses standard thresholds:

- A (90+): Ready for production modeling
- B (75-89): Minor issues, safe for most analyses
- C (60-74): Significant issues, clean before modeling
- D (40-59): Major problems, investigate data source
- F (< 40): Data may be unreliable

**Limitation:** Automated scoring cannot assess semantic accuracy or business rule compliance. Always combine with domain expert review for critical analyses.
