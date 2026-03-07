# MLOps Maturity Model

## Contents

1. [Maturity Levels](#maturity-levels)
2. [Deployment Patterns](#deployment-patterns)
3. [Monitoring Strategy](#monitoring-strategy)
4. [Retraining Triggers](#retraining-triggers)
5. [Model Versioning](#model-versioning)

---

## Maturity Levels

### Level 0: Manual

| Aspect | State |
|--------|-------|
| Training | Jupyter notebooks, manual execution |
| Deployment | Manual export, ad-hoc serving |
| Monitoring | None or manual checks |
| Retraining | When someone remembers |
| Testing | None |

**Next step:** Version control notebooks, standardize data access, add basic monitoring.

### Level 1: ML Pipeline

| Aspect | State |
|--------|-------|
| Training | Automated pipeline (Airflow, Prefect, Dagster) |
| Deployment | Scripted deployment to single environment |
| Monitoring | Basic metrics logged (accuracy, latency) |
| Retraining | Scheduled (weekly, monthly) |
| Testing | Data validation, model performance checks |

**Next step:** Add CI/CD for model code, implement A/B testing, automate rollback.

### Level 2: CI/CD + Continuous Training

| Aspect | State |
|--------|-------|
| Training | Triggered by data drift or schedule, parameterized |
| Deployment | CI/CD pipeline, staging + production, canary/blue-green |
| Monitoring | Data drift, prediction drift, feature importance shifts |
| Retraining | Triggered by monitoring alerts |
| Testing | Unit tests, integration tests, model validation gates |

**Next step:** Full automation, multi-model management, experiment platform.

### Level 3: Full Automation

| Aspect | State |
|--------|-------|
| Training | Auto-triggered, auto-tuned, experiment tracking |
| Deployment | Fully automated with safety checks, multi-region |
| Monitoring | Comprehensive: data, model, business metrics, alerts |
| Retraining | Automatic with human approval for significant changes |
| Testing | Automated testing suite, shadow mode, champion/challenger |

---

## Deployment Patterns

### Batch vs Real-time

| Pattern | Latency | Throughput | Use Case |
|---------|---------|-----------|----------|
| **Batch** | Hours | Very high | Recommendations, risk scoring, reports |
| **Near real-time** | Seconds-minutes | Medium | Fraud alerts, content moderation |
| **Real-time** | Milliseconds | Variable | Search ranking, pricing, personalization |
| **Streaming** | Sub-second | Continuous | Anomaly detection, IoT |

### Serving architectures

| Architecture | When | Tools |
|-------------|------|-------|
| REST API | Standard web integration | FastAPI, Flask, BentoML |
| gRPC | High-throughput, low-latency | TensorFlow Serving, Triton |
| Embedded | Edge devices, offline | ONNX Runtime, TFLite |
| Batch job | Scheduled predictions | Spark, Airflow |
| Streaming | Real-time event processing | Kafka + Flink, Beam |

### Deployment strategies

| Strategy | Risk | Rollback Speed | When |
|----------|------|---------------|------|
| **Direct replacement** | High | Slow | Low-risk models, dev/staging |
| **Blue-green** | Low | Fast | Stateless models |
| **Canary** | Low | Fast | Production-critical models |
| **Shadow mode** | Zero | N/A | New models before launch |
| **Champion/challenger** | Low | Fast | Continuous improvement |

---

## Monitoring Strategy

### What to monitor

| Layer | Metrics | Alert Threshold |
|-------|---------|----------------|
| **Infrastructure** | Latency, throughput, error rate, CPU/memory | P99 latency > SLA, error rate > 1% |
| **Data quality** | Missing values, schema changes, distribution drift | PSI > 0.2, missing rate change > 5% |
| **Feature drift** | Feature distribution shift (PSI, KS test) | PSI > 0.1 per feature |
| **Prediction drift** | Output distribution shift | PSI > 0.2 on predictions |
| **Model performance** | Accuracy, AUC, RMSE (requires labels) | Drop > 5% from baseline |
| **Business impact** | Conversion, revenue, user engagement | Drop > 3% from baseline |

### Drift detection methods

| Method | Type | Library |
|--------|------|---------|
| Population Stability Index (PSI) | Distribution shift | Custom / evidently |
| Kolmogorov-Smirnov test | Distribution comparison | scipy |
| Page-Hinkley test | Sequential change detection | river |
| ADWIN | Adaptive windowing | river |
| Evidently reports | Comprehensive dashboard | evidently |

---

## Retraining Triggers

| Trigger | Detection | Action |
|---------|----------|--------|
| **Scheduled** | Calendar (weekly, monthly) | Retrain on latest data |
| **Performance degradation** | Monitoring alert | Investigate → retrain |
| **Data drift** | PSI / KS threshold | Retrain with new distribution |
| **New data volume** | Row count threshold | Retrain to capture new patterns |
| **Feature schema change** | Schema validation failure | Update pipeline → retrain |
| **Business event** | External signal (product launch, policy change) | Retrain with new context |

### Retraining pipeline

1. Validate new training data (schema, quality, distribution)
2. Train candidate model with same hyperparameters
3. Evaluate on holdout set — compare to champion
4. If candidate >= champion: promote to staging
5. A/B test in production (canary deployment)
6. If metrics hold: promote to champion, archive old model

---

## Model Versioning

### What to version

| Artifact | Tool | Why |
|----------|------|-----|
| Code | Git | Reproducibility |
| Data | DVC, LakeFS | Training data lineage |
| Model | MLflow, W&B | Model artifacts + metrics |
| Config | Git (YAML/JSON) | Hyperparameters, feature lists |
| Environment | Docker, conda-lock | Dependency pinning |

### Naming convention

```
{model_name}-v{major}.{minor}.{patch}
```

- **Major:** Architecture change, new features, breaking API change
- **Minor:** Retrained on new data, hyperparameter tuning
- **Patch:** Bug fix, no model change

### Model registry workflow

1. **Development** → train and evaluate locally
2. **Staging** → register in registry, run integration tests
3. **Production** → deploy via CI/CD, monitor
4. **Archived** → retain for audit, comparison, rollback
