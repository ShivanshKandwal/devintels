"""
Churn Risk Model.

Train and evaluate multiple classifiers (Logistic Regression, Random Forest,
XGBoost, LightGBM) for developer churn-risk prediction.

Pipeline:
- Stratified 80/20 train/test split
- MLflow experiment tracking
- Evaluation: ROC-AUC, PR-AUC, F1, Lift
- SHAP analysis (global + per-cluster)
- Best model saved to ``models/churn_xgb.pkl``

Usage:
    python -m src.models.churn_model
"""

from __future__ import annotations

import json
import logging
import warnings
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    f1_score,
    precision_recall_curve,
    roc_auc_score,
    auc as sk_auc,
    classification_report,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore", category=FutureWarning)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FEATURES_DIR = PROJECT_ROOT / "data" / "features"
MODELS_DIR = PROJECT_ROOT / "models"

TARGET = "churn_risk"

# Features to use (subset of engineered features — numeric only)
MODEL_FEATURES: list[str] = [
    "years_code_pro_num", "experience_gap",
    "lang_count", "db_count", "stack_diversity_score",
    "ai_tool_count", "uses_python", "uses_cloud", "uses_ai_tools",
    "learning_diversity", "learns_online",
    "is_remote", "org_size_num", "is_large_org",
    "job_sat_score", "so_engagement_score", "ai_sentiment_score",
    "is_high_income_country", "is_employed",
    "platform_count", "tool_count", "collab_tool_count",
    "uses_javascript", "is_hybrid",
    "learn_source_count", "learn_online_count",
]


def _get_available_features(df: pd.DataFrame) -> list[str]:
    """Return model features that actually exist in *df*."""
    return [f for f in MODEL_FEATURES if f in df.columns]


def _load_data(features_dir: Path) -> pd.DataFrame:
    """Load and concatenate feature parquet files."""
    parquet_files = sorted(features_dir.glob("*_features.parquet"))
    if not parquet_files:
        raise FileNotFoundError(f"No feature files in {features_dir}")
    dfs = [pd.read_parquet(f) for f in parquet_files]
    return pd.concat(dfs, ignore_index=True)


def _compute_lift_at_k(y_true: np.ndarray, y_prob: np.ndarray, k: float = 0.1) -> float:
    """Compute lift at top-k% of scored population."""
    n = len(y_true)
    top_k = max(1, int(n * k))
    order = np.argsort(-y_prob)
    top_positives = y_true[order[:top_k]].sum()
    baseline_rate = y_true.mean()
    if baseline_rate == 0:
        return 0.0
    lift = (top_positives / top_k) / baseline_rate
    return float(lift)


def _evaluate(
    name: str,
    model: Any,
    X_test: np.ndarray,
    y_test: np.ndarray,
) -> dict[str, float]:
    """Evaluate a model and return metrics dict."""
    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)

    roc = roc_auc_score(y_test, y_prob)
    prec, rec, _ = precision_recall_curve(y_test, y_prob)
    pr_auc = sk_auc(rec, prec)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    lift = _compute_lift_at_k(y_test, y_prob, k=0.1)

    logger.info(
        "%s — ROC-AUC: %.4f  PR-AUC: %.4f  F1: %.4f  Lift@10%%: %.2f",
        name, roc, pr_auc, f1, lift,
    )

    return {
        "model": name,
        "roc_auc": round(roc, 4),
        "pr_auc": round(pr_auc, 4),
        "f1": round(f1, 4),
        "lift_at_10pct": round(lift, 2),
    }


def _run_shap_analysis(
    model: Any,
    X_df: pd.DataFrame,
    models_dir: Path,
    cluster_labels: pd.Series | None = None,
) -> dict[str, Any]:
    """Run SHAP analysis and save results.

    Returns dict with global feature importances and per-cluster breakdowns.
    """
    try:
        import shap
    except ImportError:
        logger.warning("shap not installed — skipping SHAP analysis.")
        return {}

    # Use a sample for speed
    sample_size = min(500, len(X_df))
    X_sample = X_df.sample(n=sample_size, random_state=42)

    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_sample)
    except Exception:
        explainer = shap.Explainer(model, X_sample)
        shap_values = explainer(X_sample).values

    if isinstance(shap_values, list):
        # Binary classification — use class-1 SHAP values
        shap_values = shap_values[1]
    elif isinstance(shap_values, np.ndarray) and len(shap_values.shape) == 3:
        # Binary classification (samples, features, classes) — use class-1
        shap_values = shap_values[:, :, 1]

    # Global importances
    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    importance = dict(zip(X_df.columns, mean_abs_shap.tolist()))
    importance = dict(sorted(importance.items(), key=lambda x: -x[1]))

    result: dict[str, Any] = {"global_importance": importance}

    # Per-cluster SHAP
    if cluster_labels is not None:
        per_cluster: dict[str, dict[str, float]] = {}
        for cid in sorted(cluster_labels.unique()):
            if cid == -1:
                continue
            mask = cluster_labels.values[X_sample.index] == cid  # type: ignore[index]
            if mask.sum() < 5:
                continue
            cluster_shap = np.abs(shap_values[mask]).mean(axis=0)
            per_cluster[str(cid)] = dict(zip(X_df.columns, cluster_shap.tolist()))
        result["per_cluster"] = per_cluster

    # Save
    shap_path = models_dir / "churn_shap.json"
    with open(shap_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)
    logger.info("SHAP analysis saved to %s", shap_path)

    return result


def train_churn_models(
    features_dir: Path | None = None,
    models_dir: Path | None = None,
    use_mlflow: bool = False,
) -> dict[str, Any]:
    """Train and evaluate churn-risk models.

    Parameters
    ----------
    features_dir:
        Directory with feature parquet files.
    models_dir:
        Where to save trained models.
    use_mlflow:
        Whether to log to MLflow.

    Returns
    -------
    Dict with best model name, metrics, and paths.
    """
    features_dir = features_dir or FEATURES_DIR
    models_dir = models_dir or MODELS_DIR
    models_dir.mkdir(parents=True, exist_ok=True)

    df = _load_data(features_dir)
    features = _get_available_features(df)

    if TARGET not in df.columns:
        raise ValueError(f"Target '{TARGET}' not found in data.")

    if len(features) < 5:
        raise ValueError(f"Too few features available: {features}")

    # Prepare X, y
    X = df[features].copy().fillna(0)
    y = df[TARGET].values.astype(int)

    logger.info("Data: %d rows, %d features, target prevalence: %.2f%%",
                len(X), len(features), y.mean() * 100)

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y,
    )

    # Scale for logistic regression
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    joblib.dump(scaler, models_dir / "churn_scaler.pkl")

    # Define models
    models: dict[str, Any] = {
        "LogisticRegression": LogisticRegression(
            max_iter=1000, C=1.0, class_weight="balanced", random_state=42,
        ),
        "RandomForest": RandomForestClassifier(
            n_estimators=200, max_depth=10, class_weight="balanced",
            random_state=42, n_jobs=-1,
        ),
    }

    # Try XGBoost
    try:
        from xgboost import XGBClassifier
        scale_pos = max(1.0, (y == 0).sum() / max((y == 1).sum(), 1))
        models["XGBoost"] = XGBClassifier(
            n_estimators=300, max_depth=6, learning_rate=0.1,
            scale_pos_weight=scale_pos,
            eval_metric="logloss", random_state=42,
            use_label_encoder=False, verbosity=0,
        )
    except ImportError:
        logger.warning("xgboost not installed — skipping.")

    # Try LightGBM
    try:
        from lightgbm import LGBMClassifier
        models["LightGBM"] = LGBMClassifier(
            n_estimators=300, max_depth=6, learning_rate=0.1,
            is_unbalance=True, random_state=42, verbose=-1,
        )
    except ImportError:
        logger.warning("lightgbm not installed — skipping.")

    # Train and evaluate
    all_metrics: list[dict[str, float]] = []
    trained_models: dict[str, Any] = {}

    # Optionally set up MLflow
    mlflow_active = False
    if use_mlflow:
        try:
            import mlflow
            mlflow.set_tracking_uri(str(PROJECT_ROOT / "mlflow"))
            mlflow.set_experiment("churn_risk")
            mlflow_active = True
        except ImportError:
            logger.warning("mlflow not installed — skipping tracking.")

    for name, model in models.items():
        logger.info("Training %s...", name)

        # Use scaled data for LR, raw for tree models
        if name == "LogisticRegression":
            model.fit(X_train_scaled, y_train)
            metrics = _evaluate(name, model, X_test_scaled, y_test)
        else:
            model.fit(X_train, y_train)
            metrics = _evaluate(name, model, X_test, y_test)

        all_metrics.append(metrics)
        trained_models[name] = model

        if mlflow_active:
            try:
                import mlflow
                with mlflow.start_run(run_name=name):
                    mlflow.log_params({"model": name, "n_features": len(features)})
                    mlflow.log_metrics({k: v for k, v in metrics.items() if k != "model"})
            except Exception as exc:
                logger.warning("MLflow logging failed for %s: %s", name, exc)

    # Pick best model by ROC-AUC
    best = max(all_metrics, key=lambda m: m["roc_auc"])
    best_name = best["model"]
    best_model = trained_models[best_name]
    logger.info("Best model: %s (ROC-AUC: %.4f)", best_name, best["roc_auc"])

    # Save best model
    model_path = models_dir / "churn_xgb.pkl"
    joblib.dump(best_model, model_path)
    logger.info("Saved best model to %s", model_path)

    # Save feature names
    feature_path = models_dir / "churn_features.json"
    with open(feature_path, "w") as f:
        json.dump(features, f)

    # Save all metrics
    metrics_path = models_dir / "churn_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(all_metrics, f, indent=2)

    # SHAP analysis on best tree model
    tree_models = {k: v for k, v in trained_models.items() if k != "LogisticRegression"}
    if tree_models:
        shap_model = trained_models.get(best_name, list(tree_models.values())[0])
        cluster_labels = df.get("cluster_id")
        _run_shap_analysis(shap_model, X, models_dir, cluster_labels)

    return {
        "best_model": best_name,
        "best_metrics": best,
        "all_metrics": all_metrics,
        "model_path": str(model_path),
        "features": features,
    }


# ── Inference ─────────────────────────────────────────────────────────────


def predict_churn(
    profile: dict[str, Any],
    models_dir: Path | None = None,
) -> dict[str, Any]:
    """Predict churn probability for a single developer profile.

    Parameters
    ----------
    profile:
        Dict of feature values.
    models_dir:
        Where to find the saved model.

    Returns
    -------
    Dict with churn_probability, risk_level, top_drivers.
    """
    models_dir = models_dir or MODELS_DIR

    model_path = models_dir / "churn_xgb.pkl"
    features_path = models_dir / "churn_features.json"

    if not model_path.exists():
        raise FileNotFoundError(f"Churn model not found at {model_path}")

    model = joblib.load(model_path)
    with open(features_path) as f:
        feature_names = json.load(f)

    # Build feature vector
    values = [float(profile.get(f, 0)) for f in feature_names]
    X = np.array([values])

    # Check if model needs scaled input
    scaler_path = models_dir / "churn_scaler.pkl"
    if hasattr(model, "coef_") and scaler_path.exists():
        scaler = joblib.load(scaler_path)
        X = scaler.transform(X)

    prob = float(model.predict_proba(X)[0, 1])

    # Risk level
    if prob >= 0.7:
        risk_level = "high"
    elif prob >= 0.4:
        risk_level = "medium"
    else:
        risk_level = "low"

    # Top drivers from SHAP if available
    shap_path = models_dir / "churn_shap.json"
    top_drivers: list[dict[str, Any]] = []
    if shap_path.exists():
        with open(shap_path) as f:
            shap_data = json.load(f)
        importance = shap_data.get("global_importance", {})
        for feat, imp in list(importance.items())[:5]:
            top_drivers.append({
                "feature": feat,
                "importance": round(imp, 4),
                "value": profile.get(feat, 0),
            })

    return {
        "churn_probability": round(prob, 4),
        "risk_level": risk_level,
        "top_drivers": top_drivers,
    }


# ── CLI ───────────────────────────────────────────────────────────────────


def main() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    try:
        result = train_churn_models()
        print(f"\n✅  Churn model training complete.")
        print(f"   Best model: {result['best_model']}")
        print(f"   ROC-AUC: {result['best_metrics']['roc_auc']}")
    except (FileNotFoundError, ValueError) as exc:
        print(f"\n❌  {exc}")


if __name__ == "__main__":
    main()
