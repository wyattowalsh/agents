# Feature Engineering Cookbook

## Contents

1. [Workflow](#workflow)
2. [Numeric Features](#numeric-features)
3. [Categorical Features](#categorical-features)
4. [Temporal Features](#temporal-features)
5. [Text Features](#text-features)
6. [Feature Selection](#feature-selection)
7. [Leakage Prevention](#leakage-prevention)

---

## Workflow

1. **Profile** — run `data-profiler.py` to understand distributions, types, missing patterns
2. **Clean** — handle missing values, fix inconsistencies
3. **Transform** — apply type-specific transformations from `data/feature-engineering-patterns.json`
4. **Create** — engineer new features from domain knowledge
5. **Select** — reduce dimensionality, remove redundant features
6. **Validate** — check for leakage, verify feature importance

---

## Numeric Features

### Missing value strategies

| Strategy | When | Risk |
|----------|------|------|
| Mean/median imputation | MCAR (random missingness) | Reduces variance |
| Mode imputation | Categorical, few missing | Biases toward mode |
| KNN imputation | MAR (missingness depends on other features) | Computationally expensive |
| Iterative imputation (MICE) | Complex patterns | May not converge |
| Indicator + imputation | Missingness is informative | Adds features |
| Drop rows | Few missing, large dataset | Loses data |
| Drop columns | > 50% missing, not critical | Loses information |

### Transformation guide

| Distribution Shape | Transformation | Effect |
|-------------------|---------------|--------|
| Right-skewed (long right tail) | log(x+1) | Compresses large values |
| Left-skewed (long left tail) | x^2 or exp(x) | Compresses small values |
| Heavy tails (kurtosis > 3) | Winsorize at 1st/99th percentile | Caps extreme values |
| Bimodal | Consider splitting into two features | Separates populations |
| Zero-inflated | Two features: is_zero indicator + log(x) for non-zero | Handles structural zeros |

### Scaling decision

| Scaler | Formula | Use When |
|--------|---------|----------|
| StandardScaler | (x - mean) / std | Linear models, SVM, neural nets |
| MinMaxScaler | (x - min) / (max - min) | Neural nets with sigmoid/tanh |
| RobustScaler | (x - median) / IQR | Data with outliers |
| None | — | Tree-based models (scale-invariant) |

---

## Categorical Features

### Encoding decision tree

```
Cardinality < 5?       → One-hot encoding
Cardinality 5-15?      → One-hot (linear) or Label encoding (tree)
Cardinality 15-100?    → Target encoding (with CV) or Frequency encoding
Cardinality > 100?     → Hash encoding, Embedding, or Target encoding
Ordinal relationship?  → Ordinal encoding with explicit order
```

### Target encoding (safely)

Target encoding leaks information. Mitigate with:

1. **K-fold target encoding** — compute target mean using out-of-fold data only
2. **Smoothing** — blend category mean with global mean: `encoded = (count * cat_mean + m * global_mean) / (count + m)` where m is smoothing parameter
3. **Add noise** — small Gaussian noise reduces overfitting

---

## Temporal Features

### Date/time decomposition

| Feature | Type | When Useful |
|---------|------|------------|
| Year, month, day | Integer | Trend, seasonality |
| Day of week | Cyclical (sin/cos) | Weekly patterns |
| Hour of day | Cyclical (sin/cos) | Intraday patterns |
| Is weekend | Binary | Consumer behavior |
| Quarter | Integer/cyclical | Business cycles |
| Days since epoch | Integer | Monotonic trend |
| Days until/since event | Integer | Event proximity effects |

### Cyclical encoding

```python
import numpy as np
df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
```

### Lag features for time series

| Feature | Lag | When |
|---------|-----|------|
| Value at t-1 | 1 | Autoregressive modeling |
| Value at t-7 | 7 | Weekly seasonality |
| Rolling mean (7d) | Window | Trend smoothing |
| Rolling std (7d) | Window | Volatility measure |
| Diff (t - t-1) | 1 | Rate of change |

**Leakage warning:** Lag features must use only past data. Never compute rolling stats that include future values.

---

## Text Features

### Pipeline by data size

| Data Size | Approach | Library |
|-----------|----------|---------|
| < 1K samples | TF-IDF + simple model | scikit-learn |
| 1K-100K | TF-IDF or sentence embeddings | scikit-learn / sentence-transformers |
| > 100K | Fine-tuned transformer | Hugging Face |

### Quick text features (always useful)

- `text_length`: character count
- `word_count`: space-split word count
- `avg_word_length`: mean word length
- `uppercase_ratio`: fraction of uppercase characters
- `special_char_ratio`: non-alphanumeric fraction
- `has_url`, `has_email`, `has_number`: binary indicators

---

## Feature Selection

### Strategy by feature count

| Features | Strategy |
|----------|----------|
| < 20 | Manual review + domain knowledge |
| 20-100 | Correlation filter + tree importance |
| 100-1000 | LASSO + mutual information + SHAP |
| > 1000 | Variance threshold → mutual info → RFE on subset |

### Removal criteria

1. **Near-zero variance** — features constant in > 95% of samples
2. **High correlation** — pairs with abs(r) > 0.95, remove the less important one
3. **Low importance** — SHAP or permutation importance near zero
4. **Post-outcome features** — any feature derived from or correlated with future information

---

## Leakage Prevention

### Checklist

| Check | How |
|-------|-----|
| Feature derived from target? | Trace feature computation — does it use `y`? |
| Feature from the future? | Check temporal ordering of feature vs prediction time |
| Preprocessing fit on test? | Ensure scaler.fit() uses train only |
| Same entity in train+test? | GroupKFold if data has entity IDs |
| Aggregation across split? | Group-level stats must be computed within split |

### Red flags in feature importance

- A single feature dominates with > 50% importance → likely leakage
- Feature has near-perfect correlation with target → investigate derivation
- Removing the feature drops AUC from 0.99 to 0.65 → almost certainly leakage
