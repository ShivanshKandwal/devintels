"""
Career Value Model.

XGBoost regressor for salary prediction + career_value_score computation
(predicted salary percentile within peer group).

Usage:
    python -m src.models.career_value
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FEATURES_DIR = PROJECT_ROOT / "data" / "features"
MODELS_DIR = PROJECT_ROOT / "models"

TARGET = "log_salary"

CAREER_FEATURES: list[str] = [
    "years_code_pro_num", "experience_gap",
    "lang_count", "db_count", "stack_diversity_score",
    "ai_tool_count", "uses_python", "uses_cloud", "uses_ai_tools",
    "learning_diversity", "learns_online",
    "is_remote", "org_size_num", "is_large_org",
    "job_sat_score", "so_engagement_score", "ai_sentiment_score",
    "is_high_income_country", "is_employed",
    "ed_level_num", "platform_count", "tool_count",
    "uses_javascript", "is_hybrid",
    "collab_tool_count",
]


def _load_data(features_dir: Path) -> pd.DataFrame:
    """Load and concatenate feature parquet files."""
    parquet_files = sorted(features_dir.glob("*_features.parquet"))
    if not parquet_files:
        raise FileNotFoundError(f"No feature files in {features_dir}")
    dfs = [pd.read_parquet(f) for f in parquet_files]
    return pd.concat(dfs, ignore_index=True)


def train_career_model(
    features_dir: Path | None = None,
    models_dir: Path | None = None,
) -> dict[str, Any]:
    """Train the career-value regression model.

    Parameters
    ----------
    features_dir:
        Directory with feature parquet files.
    models_dir:
        Where to save models.

    Returns
    -------
    Dict with metrics, model path, and salary percentile lookup.
    """
    features_dir = features_dir or FEATURES_DIR
    models_dir = models_dir or MODELS_DIR
    models_dir.mkdir(parents=True, exist_ok=True)

    df = _load_data(features_dir)

    # Filter to rows with valid salary
    if TARGET not in df.columns:
        raise ValueError(f"Target '{TARGET}' not found. Run clean.py first.")

    df_valid = df.dropna(subset=[TARGET])
    df_valid = df_valid[df_valid[TARGET] > 0]
    logger.info("Training data: %d rows with valid salary", len(df_valid))

    features = [f for f in CAREER_FEATURES if f in df_valid.columns]
    if len(features) < 5:
        raise ValueError(f"Too few features: {features}")

    X = df_valid[features].copy().fillna(0)
    y = df_valid[TARGET].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42,
    )

    # Train XGBoost regressor
    try:
        from xgboost import XGBRegressor
        model = XGBRegressor(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbosity=0,
        )
    except ImportError:
        from sklearn.ensemble import GradientBoostingRegressor
        logger.warning("xgboost not installed — using sklearn GradientBoosting.")
        model = GradientBoostingRegressor(
            n_estimators=300, max_depth=6, learning_rate=0.1, random_state=42,
        )

    logger.info("Training career-value model...")
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    mae = float(mean_absolute_error(y_test, y_pred))
    r2 = float(r2_score(y_test, y_pred))

    # Also evaluate in dollar space
    y_test_dollars = np.expm1(y_test)
    y_pred_dollars = np.expm1(y_pred)
    rmse_dollars = float(np.sqrt(mean_squared_error(y_test_dollars, y_pred_dollars)))
    mae_dollars = float(mean_absolute_error(y_test_dollars, y_pred_dollars))

    logger.info("RMSE (log): %.4f  MAE (log): %.4f  R²: %.4f", rmse, mae, r2)
    logger.info("RMSE ($): $%,.0f   MAE ($): $%,.0f", rmse_dollars, mae_dollars)

    metrics = {
        "rmse_log": round(rmse, 4),
        "mae_log": round(mae, 4),
        "r2": round(r2, 4),
        "rmse_dollars": round(rmse_dollars, 2),
        "mae_dollars": round(mae_dollars, 2),
        "n_train": len(X_train),
        "n_test": len(X_test),
    }

    # Save model
    model_path = models_dir / "career_value_xgb.pkl"
    joblib.dump(model, model_path)
    logger.info("Saved model to %s", model_path)

    # Save feature list
    features_path = models_dir / "career_features.json"
    with open(features_path, "w") as f:
        json.dump(features, f)

    # Save metrics
    metrics_path = models_dir / "career_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    # Compute salary percentile lookup (for career_value_score)
    all_preds = model.predict(X.fillna(0))
    all_salaries = np.expm1(all_preds)
    percentiles = {
        str(p): float(np.percentile(all_salaries, p))
        for p in range(0, 101, 5)
    }
    percentile_path = models_dir / "salary_percentiles.json"
    with open(percentile_path, "w") as f:
        json.dump(percentiles, f, indent=2)

    return {
        "metrics": metrics,
        "model_path": str(model_path),
        "features": features,
    }


def predict_career_value(
    profile: dict[str, Any],
    models_dir: Path | None = None,
) -> dict[str, Any]:
    """Predict salary and compute career_value_score for a developer profile.

    Parameters
    ----------
    profile:
        Dict of feature values.
    models_dir:
        Where to find saved models.

    Returns
    -------
    Dict with predicted_salary, salary_range, career_value_score,
    percentile, cluster assignment.
    """
    models_dir = models_dir or MODELS_DIR
    model_path = models_dir / "career_value_xgb.pkl"
    features_path = models_dir / "career_features.json"

    if not model_path.exists():
        raise FileNotFoundError(f"Career model not found at {model_path}")

    model = joblib.load(model_path)
    with open(features_path) as f:
        feature_names = json.load(f)

    values = [float(profile.get(f, 0)) for f in feature_names]
    X = np.array([values])

    log_pred = float(model.predict(X)[0])
    predicted_salary = float(np.expm1(log_pred))

    # Salary range (±20%)
    salary_low = predicted_salary * 0.80
    salary_high = predicted_salary * 1.20

    # Career value score from percentiles
    percentile_path = models_dir / "salary_percentiles.json"
    career_value_score = 50.0
    if percentile_path.exists():
        with open(percentile_path) as f:
            percentiles = json.load(f)
        for p_str in sorted(percentiles.keys(), key=int, reverse=True):
            if predicted_salary >= percentiles[p_str]:
                career_value_score = float(p_str)
                break

    # Determine cluster from segmentation if available
    cluster_id = -1
    try:
        umap_path = models_dir / "umap_coordinates.parquet"
        if umap_path.exists():
            coords = pd.read_parquet(umap_path)
            if "cluster_id" in coords.columns:
                cluster_id = int(coords["cluster_id"].mode().iloc[0])
    except Exception:
        pass

    return {
        "predicted_salary": round(predicted_salary, 2),
        "salary_range": {
            "low": round(salary_low, 2),
            "high": round(salary_high, 2),
        },
        "career_value_score": round(career_value_score, 1),
        "percentile": round(career_value_score, 1),
        "cluster_id": cluster_id,
    }


# ── CLI ───────────────────────────────────────────────────────────────────


def main() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    try:
        result = train_career_model()
        print(f"\n✅  Career-value model trained.")
        print(f"   R²: {result['metrics']['r2']}")
        print(f"   RMSE ($): ${result['metrics']['rmse_dollars']:,.0f}")
    except (FileNotFoundError, ValueError) as exc:
        print(f"\n❌  {exc}")


if __name__ == "__main__":
    main()
