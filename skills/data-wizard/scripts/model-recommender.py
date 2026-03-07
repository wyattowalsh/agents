#!/usr/bin/env python3
"""Task-based model selection decision tree. Stdlib only.

Input (JSON via stdin or --input):
  {
    "task_type": "classification|regression|clustering|ranking|anomaly_detection|forecasting",
    "data_size": "small|medium|large|very_large",
    "feature_types": ["numeric", "categorical", "text", "image", "mixed"],
    "interpretability_required": true|false,
    "latency_constraint": "none|moderate|strict"  (optional)
  }

Output: JSON with ranked model recommendations.
"""

import argparse
import json
import sys

MODEL_CATALOG = {
    "classification": {
        "small": {
            "interpretable": [
                {"model": "Logistic Regression", "library": "scikit-learn", "rationale": "Strong baseline, interpretable coefficients, fast training"},
                {"model": "Decision Tree", "library": "scikit-learn", "rationale": "Fully interpretable, handles mixed types"},
                {"model": "Naive Bayes", "library": "scikit-learn", "rationale": "Works well with small data, probabilistic output"},
            ],
            "flexible": [
                {"model": "Random Forest", "library": "scikit-learn", "rationale": "Robust to overfitting on small data, feature importance"},
                {"model": "SVM (RBF)", "library": "scikit-learn", "rationale": "Effective in high-dimensional spaces"},
                {"model": "Logistic Regression", "library": "scikit-learn", "rationale": "Always include as baseline"},
            ],
        },
        "medium": {
            "interpretable": [
                {"model": "Logistic Regression", "library": "scikit-learn", "rationale": "Baseline with regularization"},
                {"model": "Explainable Boosting Machine", "library": "interpret", "rationale": "Glass-box model, near-GBDT performance"},
                {"model": "LightGBM + SHAP", "library": "lightgbm + shap", "rationale": "High performance with post-hoc explanations"},
            ],
            "flexible": [
                {"model": "LightGBM", "library": "lightgbm", "rationale": "Fast training, handles categorical natively"},
                {"model": "XGBoost", "library": "xgboost", "rationale": "Mature, extensive hyperparameter control"},
                {"model": "Random Forest", "library": "scikit-learn", "rationale": "Robust baseline, parallelizable"},
            ],
        },
        "large": {
            "interpretable": [
                {"model": "LightGBM + SHAP", "library": "lightgbm + shap", "rationale": "Scales well, post-hoc interpretability"},
                {"model": "Linear Model + Feature Engineering", "library": "scikit-learn", "rationale": "Interpretable if features are meaningful"},
            ],
            "flexible": [
                {"model": "LightGBM", "library": "lightgbm", "rationale": "Best speed/performance ratio at scale"},
                {"model": "XGBoost", "library": "xgboost", "rationale": "Distributed training support"},
                {"model": "CatBoost", "library": "catboost", "rationale": "Best for high-cardinality categoricals"},
                {"model": "Deep Learning (TabNet)", "library": "pytorch-tabnet", "rationale": "Attention-based, self-supervised pretraining"},
            ],
        },
        "very_large": {
            "interpretable": [
                {"model": "LightGBM + SHAP", "library": "lightgbm + shap", "rationale": "Distributed mode handles billions of rows"},
            ],
            "flexible": [
                {"model": "LightGBM (distributed)", "library": "lightgbm", "rationale": "Native distributed training"},
                {"model": "Deep Learning", "library": "PyTorch / TensorFlow", "rationale": "Can learn complex representations"},
                {"model": "XGBoost (distributed)", "library": "xgboost + dask/ray", "rationale": "Distributed gradient boosting"},
            ],
        },
    },
    "regression": {
        "small": {
            "interpretable": [
                {"model": "Linear Regression", "library": "scikit-learn", "rationale": "Interpretable coefficients, fast"},
                {"model": "Ridge / Lasso", "library": "scikit-learn", "rationale": "Regularization prevents overfitting on small data"},
                {"model": "Decision Tree Regressor", "library": "scikit-learn", "rationale": "Non-linear, fully interpretable"},
            ],
            "flexible": [
                {"model": "Random Forest Regressor", "library": "scikit-learn", "rationale": "Handles non-linearity, robust"},
                {"model": "SVR", "library": "scikit-learn", "rationale": "Effective for small, high-dimensional data"},
                {"model": "Linear Regression", "library": "scikit-learn", "rationale": "Always include as baseline"},
            ],
        },
        "medium": {
            "interpretable": [
                {"model": "Ridge / Lasso", "library": "scikit-learn", "rationale": "Baseline with feature selection"},
                {"model": "Explainable Boosting Machine", "library": "interpret", "rationale": "Glass-box with near-GBDT accuracy"},
            ],
            "flexible": [
                {"model": "LightGBM Regressor", "library": "lightgbm", "rationale": "Fast, handles missing values"},
                {"model": "XGBoost Regressor", "library": "xgboost", "rationale": "Robust, well-tuned defaults"},
            ],
        },
        "large": {
            "interpretable": [
                {"model": "LightGBM + SHAP", "library": "lightgbm + shap", "rationale": "Scales well with interpretability"},
            ],
            "flexible": [
                {"model": "LightGBM Regressor", "library": "lightgbm", "rationale": "Best speed/accuracy at scale"},
                {"model": "CatBoost Regressor", "library": "catboost", "rationale": "Ordered boosting, categorical support"},
                {"model": "Neural Network", "library": "PyTorch", "rationale": "For complex non-linear relationships"},
            ],
        },
        "very_large": {
            "interpretable": [
                {"model": "LightGBM + SHAP", "library": "lightgbm + shap", "rationale": "Distributed interpretable modeling"},
            ],
            "flexible": [
                {"model": "LightGBM (distributed)", "library": "lightgbm", "rationale": "Native distributed training"},
                {"model": "Deep Learning", "library": "PyTorch / TensorFlow", "rationale": "Learns complex representations at scale"},
            ],
        },
    },
    "clustering": {
        "small": {
            "interpretable": [
                {"model": "K-Means", "library": "scikit-learn", "rationale": "Simple, interpretable centroids"},
                {"model": "Hierarchical (Agglomerative)", "library": "scikit-learn", "rationale": "Dendrogram shows cluster relationships"},
            ],
            "flexible": [
                {"model": "DBSCAN", "library": "scikit-learn", "rationale": "No need to specify k, finds arbitrary shapes"},
                {"model": "Gaussian Mixture Model", "library": "scikit-learn", "rationale": "Soft assignments, probabilistic"},
            ],
        },
        "medium": {
            "interpretable": [
                {"model": "K-Means", "library": "scikit-learn", "rationale": "Scales well, interpretable"},
            ],
            "flexible": [
                {"model": "HDBSCAN", "library": "hdbscan", "rationale": "Robust density-based, auto-selects clusters"},
                {"model": "Gaussian Mixture Model", "library": "scikit-learn", "rationale": "Handles elliptical clusters"},
            ],
        },
        "large": {
            "interpretable": [
                {"model": "Mini-Batch K-Means", "library": "scikit-learn", "rationale": "Scalable K-Means variant"},
            ],
            "flexible": [
                {"model": "HDBSCAN", "library": "hdbscan", "rationale": "Scales with approximate nearest neighbors"},
                {"model": "Birch", "library": "scikit-learn", "rationale": "Memory-efficient for large datasets"},
            ],
        },
        "very_large": {
            "interpretable": [
                {"model": "Mini-Batch K-Means", "library": "scikit-learn", "rationale": "Streaming-compatible"},
            ],
            "flexible": [
                {"model": "Faiss K-Means", "library": "faiss", "rationale": "GPU-accelerated clustering"},
            ],
        },
    },
    "forecasting": {
        "small": {
            "interpretable": [
                {"model": "ARIMA / SARIMA", "library": "statsmodels", "rationale": "Classical, well-understood, interpretable"},
                {"model": "Exponential Smoothing", "library": "statsmodels", "rationale": "Simple, handles trend + seasonality"},
                {"model": "Prophet", "library": "prophet", "rationale": "Handles holidays, missing data, changepoints"},
            ],
            "flexible": [
                {"model": "Prophet", "library": "prophet", "rationale": "Robust to missing data and outliers"},
                {"model": "ARIMA", "library": "statsmodels", "rationale": "Statistical baseline"},
            ],
        },
        "medium": {
            "interpretable": [
                {"model": "Prophet", "library": "prophet", "rationale": "Decomposable, business-friendly output"},
                {"model": "SARIMAX", "library": "statsmodels", "rationale": "Includes exogenous variables"},
            ],
            "flexible": [
                {"model": "LightGBM (lag features)", "library": "lightgbm", "rationale": "Feature-engineered time series"},
                {"model": "NeuralProphet", "library": "neuralprophet", "rationale": "Prophet + neural network components"},
            ],
        },
        "large": {
            "interpretable": [
                {"model": "Prophet", "library": "prophet", "rationale": "Scales reasonably, interpretable"},
            ],
            "flexible": [
                {"model": "LightGBM (lag features)", "library": "lightgbm", "rationale": "Scales well with engineered features"},
                {"model": "Temporal Fusion Transformer", "library": "pytorch-forecasting", "rationale": "Multi-horizon, attention-based"},
                {"model": "N-BEATS", "library": "pytorch-forecasting", "rationale": "Pure deep learning, no feature engineering"},
            ],
        },
        "very_large": {
            "interpretable": [
                {"model": "LightGBM + SHAP", "library": "lightgbm + shap", "rationale": "Interpretable at scale"},
            ],
            "flexible": [
                {"model": "Temporal Fusion Transformer", "library": "pytorch-forecasting", "rationale": "Handles multiple time series"},
                {"model": "TimesFM / Chronos", "library": "google/amazon", "rationale": "Foundation models for time series"},
            ],
        },
    },
    "anomaly_detection": {
        "small": {
            "interpretable": [
                {"model": "Z-Score / IQR", "library": "scipy / numpy", "rationale": "Simple statistical thresholds"},
                {"model": "Isolation Forest", "library": "scikit-learn", "rationale": "Feature importance for anomalies"},
            ],
            "flexible": [
                {"model": "Isolation Forest", "library": "scikit-learn", "rationale": "Handles high-dimensional data"},
                {"model": "Local Outlier Factor", "library": "scikit-learn", "rationale": "Density-based, local context"},
                {"model": "One-Class SVM", "library": "scikit-learn", "rationale": "Effective boundary learning"},
            ],
        },
        "medium": {
            "interpretable": [
                {"model": "Isolation Forest + SHAP", "library": "scikit-learn + shap", "rationale": "Explainable anomaly scores"},
            ],
            "flexible": [
                {"model": "Isolation Forest", "library": "scikit-learn", "rationale": "Scales linearly"},
                {"model": "Autoencoder", "library": "PyTorch / TensorFlow", "rationale": "Learns normal patterns, reconstruction error as score"},
            ],
        },
        "large": {
            "interpretable": [
                {"model": "Isolation Forest + SHAP", "library": "scikit-learn + shap", "rationale": "Scalable with explanations"},
            ],
            "flexible": [
                {"model": "Autoencoder", "library": "PyTorch", "rationale": "Deep learning for complex patterns"},
                {"model": "Isolation Forest", "library": "scikit-learn", "rationale": "Memory-efficient"},
            ],
        },
        "very_large": {
            "interpretable": [
                {"model": "Statistical Process Control", "library": "custom", "rationale": "Simple rules, streaming-compatible"},
            ],
            "flexible": [
                {"model": "Streaming Autoencoder", "library": "PyTorch", "rationale": "Online learning for anomaly detection"},
            ],
        },
    },
}


def recommend(task_input: dict) -> dict:
    task_type = task_input.get("task_type", "classification")
    data_size = task_input.get("data_size", "medium")
    interpretability = task_input.get("interpretability_required", False)
    feature_types = task_input.get("feature_types", ["numeric"])

    key = "interpretable" if interpretability else "flexible"

    if task_type not in MODEL_CATALOG:
        return {"error": f"Unknown task type: {task_type}. Supported: {list(MODEL_CATALOG.keys())}"}

    size_catalog = MODEL_CATALOG[task_type]
    if data_size not in size_catalog:
        data_size = "medium"

    recommendations = size_catalog[data_size].get(key, size_catalog[data_size].get("flexible", []))

    # Add notes based on feature types
    notes = []
    if "text" in feature_types:
        notes.append("Text features detected: consider TF-IDF or sentence embeddings as preprocessing")
    if "categorical" in feature_types:
        notes.append("Categorical features: CatBoost handles natively; others need encoding")
    if "image" in feature_types:
        notes.append("Image features: consider CNN feature extraction or transfer learning")
    if "mixed" in feature_types:
        notes.append("Mixed feature types: gradient boosting methods handle this well")

    return {
        "task_type": task_type,
        "data_size": data_size,
        "interpretability_required": interpretability,
        "recommendations": recommendations,
        "baseline": recommendations[-1] if recommendations else None,
        "notes": notes,
        "evaluation_metrics": get_metrics(task_type),
    }


def get_metrics(task_type: str) -> list:
    metrics = {
        "classification": ["accuracy", "precision", "recall", "F1", "AUC-ROC", "log_loss"],
        "regression": ["RMSE", "MAE", "MAPE", "R2", "adjusted_R2"],
        "clustering": ["silhouette_score", "calinski_harabasz", "davies_bouldin", "inertia"],
        "forecasting": ["MAPE", "RMSE", "MAE", "SMAPE", "MASE"],
        "anomaly_detection": ["precision@k", "recall@k", "F1@k", "AUC-PR"],
        "ranking": ["NDCG", "MAP", "MRR", "precision@k"],
    }
    return metrics.get(task_type, ["task-specific metrics needed"])


def main():
    parser = argparse.ArgumentParser(description="Recommend ML models for a task")
    parser.add_argument("--input", help="JSON string or file path with task specification")
    args = parser.parse_args()

    if args.input:
        try:
            task_input = json.loads(args.input)
        except json.JSONDecodeError:
            with open(args.input) as f:
                task_input = json.load(f)
    else:
        task_input = json.load(sys.stdin)

    result = recommend(task_input)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
