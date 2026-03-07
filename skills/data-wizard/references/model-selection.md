# Model Selection Guide

## Contents

1. [Selection Framework](#selection-framework)
2. [By Data Size](#by-data-size)
3. [By Task Type](#by-task-type)
4. [Interpretability Trade-offs](#interpretability-trade-offs)
5. [Evaluation Strategy](#evaluation-strategy)
6. [Hyperparameter Tuning](#hyperparameter-tuning)

---

## Selection Framework

Always start with the simplest viable model. Complexity must be justified by performance gains.

### Decision flow

1. **Define the task** — classification, regression, clustering, ranking, forecasting, anomaly detection
2. **Assess data size** — small (< 10K), medium (10K-1M), large (1M-100M), very large (> 100M)
3. **Check interpretability requirements** — regulated domain? Stakeholder trust? Debug needs?
4. **Identify feature types** — numeric, categorical, text, image, mixed
5. **Run `model-recommender.py`** with the above as input

---

## By Data Size

| Size | Characteristics | Preferred Models |
|------|----------------|-----------------|
| **Small (< 10K)** | Overfitting risk high, CV variance high | Linear models, small RF, regularized models |
| **Medium (10K-1M)** | Sweet spot for most algorithms | Gradient boosting (LightGBM, XGBoost), RF |
| **Large (1M-100M)** | Training time matters, diminishing returns | LightGBM, CatBoost, mini-batch methods |
| **Very large (> 100M)** | Need distributed or streaming | Distributed GBDT, deep learning, online learning |

### Small data strategies

- Heavy regularization (L1/L2, dropout, early stopping)
- Cross-validation with more folds (10-fold or leave-one-out)
- Data augmentation where applicable
- Transfer learning for text/image domains
- Bayesian approaches (informative priors)

---

## By Task Type

### Classification

| Scenario | Recommended | Why |
|----------|------------|-----|
| Binary, tabular, interpretable | Logistic Regression | Coefficients are directly interpretable |
| Binary, tabular, performance | LightGBM | Best speed/accuracy ratio |
| Multiclass, many features | LightGBM / XGBoost | Native multiclass support |
| Imbalanced classes | SMOTE + LightGBM, or class weights | Address imbalance explicitly |
| Text classification | Fine-tuned transformer / TF-IDF + LR | Depends on data size and quality |

### Regression

| Scenario | Recommended | Why |
|----------|------------|-----|
| Linear relationships | Ridge / Lasso | Feature selection built in (Lasso) |
| Non-linear, tabular | LightGBM | Handles non-linearity automatically |
| Heteroscedastic | Quantile regression | Predicts intervals, not just mean |
| Zero-inflated | Two-stage model | Separate classification + regression |

### Clustering

| Scenario | Recommended | Why |
|----------|------------|-----|
| Known K, spherical clusters | K-Means | Simple, fast, interpretable centroids |
| Unknown K, arbitrary shapes | HDBSCAN | Auto-selects clusters, no K needed |
| Soft assignments needed | Gaussian Mixture Model | Probabilistic cluster membership |
| Very large data | Mini-Batch K-Means | Streaming-compatible |

---

## Interpretability Trade-offs

| Level | Models | Techniques |
|-------|--------|-----------|
| **Glass-box** | Linear/Logistic Regression, Decision Tree, EBM | Coefficients, rules, direct interpretation |
| **Post-hoc** | GBDT + SHAP, RF + permutation importance | SHAP values, partial dependence plots |
| **Black-box** | Deep learning, ensemble stacking | LIME (local), attention maps |

**When interpretability is required:**
1. Start with glass-box models — they may be sufficient
2. If performance gap > 3-5% vs black-box, use black-box + SHAP
3. Document feature importances and partial dependence for stakeholders

---

## Evaluation Strategy

### Train/Test Split

| Method | When | Implementation |
|--------|------|---------------|
| Hold-out (80/20) | Large data, quick iteration | `train_test_split(test_size=0.2, stratify=y)` |
| K-Fold CV (5 or 10) | Medium data, robust estimate | `StratifiedKFold(n_splits=5)` |
| Stratified K-Fold | Imbalanced classes | Preserves class proportions |
| Time-based split | Time series, temporal data | Train on past, test on future |
| Group K-Fold | Grouped data (users, sessions) | Prevents leakage across groups |
| Leave-One-Out | Very small data | Every sample is a test set once |

### Leakage prevention checklist

1. Split BEFORE any preprocessing (scaling, encoding, imputation)
2. Never use test data for feature selection or hyperparameter tuning
3. Check for features derived from the target variable
4. Verify temporal ordering in time series
5. Ensure no data from the same entity appears in both train and test

---

## Hyperparameter Tuning

| Method | When | Library |
|--------|------|---------|
| Grid search | Few hyperparameters, small search space | `GridSearchCV` |
| Random search | Many hyperparameters, wide ranges | `RandomizedSearchCV` |
| Bayesian optimization | Expensive training, need efficiency | `optuna`, `hyperopt` |
| Successive halving | Many configs, want to eliminate quickly | `HalvingGridSearchCV` |

**LightGBM key hyperparameters:**

| Parameter | Range | Impact |
|-----------|-------|--------|
| `num_leaves` | 20-200 | Model complexity |
| `learning_rate` | 0.01-0.3 | Convergence speed vs quality |
| `max_depth` | 3-12 | Overfitting control |
| `min_child_samples` | 5-100 | Regularization |
| `feature_fraction` | 0.5-1.0 | Feature subsampling |
| `lambda_l1`, `lambda_l2` | 0-10 | Regularization strength |
