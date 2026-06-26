"""
Developer Segmentation Module.

- UMAP dimensionality reduction
- HDBSCAN clustering
- Cluster profiling and automatic naming
- RFM-equivalent scoring for developers
- Saves cluster labels, UMAP coordinates, and profiles

Usage:
    python -m src.models.segmentation
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FEATURES_DIR = PROJECT_ROOT / "data" / "features"
MODELS_DIR = PROJECT_ROOT / "models"

# Feature columns used for segmentation
SEGMENTATION_FEATURES: list[str] = [
    "years_code_pro_num", "experience_gap",
    "lang_count", "db_count", "stack_diversity_score",
    "ai_tool_count", "uses_python", "uses_cloud", "uses_ai_tools",
    "learning_diversity", "learns_online",
    "is_remote", "org_size_num", "is_large_org",
    "job_sat_score", "so_engagement_score", "ai_sentiment_score",
    "is_high_income_country",
]


# ── Cluster Naming Heuristics ────────────────────────────────────────────

CLUSTER_NAMING_RULES: list[tuple[str, dict[str, Any]]] = [
    ("AI Power Users", {"uses_ai_tools": (">", 0.6), "ai_tool_count": (">", 2)}),
    ("Cloud-Native Seniors", {"uses_cloud": (">", 0.6), "years_code_pro_num": (">", 8)}),
    ("Full-Stack Generalists", {"stack_diversity_score": (">", 12), "lang_count": (">", 4)}),
    ("Remote Knowledge Workers", {"is_remote": (">", 0.6), "learning_diversity": (">", 5)}),
    ("Enterprise Veterans", {"is_large_org": (">", 0.6), "years_code_pro_num": (">", 10)}),
    ("Emerging Developers", {"years_code_pro_num": ("<", 3), "learning_diversity": (">", 4)}),
    ("Satisfied Specialists", {"job_sat_score": (">", 4), "stack_diversity_score": ("<", 8)}),
    ("Disengaged At-Risk", {"job_sat_score": ("<", 2.5), "so_engagement_score": ("<", 2)}),
]


def _auto_name_cluster(profile: dict[str, float]) -> str:
    """Assign a human-readable name to a cluster based on its mean profile."""
    best_name = "General Developers"
    best_score = 0

    for name, rules in CLUSTER_NAMING_RULES:
        score = 0
        for feature, (op, threshold) in rules.items():
            val = profile.get(feature, 0)
            if op == ">" and val > threshold:
                score += 1
            elif op == "<" and val < threshold:
                score += 1
        if score > best_score:
            best_score = score
            best_name = name

    return best_name


# ── RFM-Equivalent Scoring ───────────────────────────────────────────────


def compute_rfm_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Compute Recency-Frequency-Monetary equivalent scores for developers.

    Mapping:
    - **Recency** → ``so_engagement_score`` (how recently / frequently they engage)
    - **Frequency** → ``stack_diversity_score`` (breadth of tech usage = engagement depth)
    - **Monetary** → ``ConvertedCompYearly`` or ``log_salary`` (earning power)

    Each is bucketed into quintiles (1-5).
    """
    df = df.copy()

    # Recency
    if "so_engagement_score" in df.columns:
        df["rfm_recency"] = pd.qcut(
            df["so_engagement_score"].rank(method="first"),
            q=5, labels=[1, 2, 3, 4, 5],
        ).astype(float).fillna(3)
    else:
        df["rfm_recency"] = 3

    # Frequency
    if "stack_diversity_score" in df.columns:
        df["rfm_frequency"] = pd.qcut(
            df["stack_diversity_score"].rank(method="first"),
            q=5, labels=[1, 2, 3, 4, 5],
        ).astype(float).fillna(3)
    else:
        df["rfm_frequency"] = 3

    # Monetary
    salary_col = "log_salary" if "log_salary" in df.columns else "ConvertedCompYearly"
    if salary_col in df.columns:
        valid = df[salary_col].dropna()
        if len(valid) > 10:
            df["rfm_monetary"] = pd.qcut(
                df[salary_col].rank(method="first"),
                q=5, labels=[1, 2, 3, 4, 5],
            ).astype(float).fillna(3)
        else:
            df["rfm_monetary"] = 3
    else:
        df["rfm_monetary"] = 3

    df["rfm_total"] = df["rfm_recency"] + df["rfm_frequency"] + df["rfm_monetary"]
    return df


# ── Main Segmentation Pipeline ───────────────────────────────────────────


def run_segmentation(
    features_dir: Path | None = None,
    models_dir: Path | None = None,
    n_components: int = 2,
    min_cluster_size: int = 50,
    min_samples: int = 15,
) -> dict[str, Any]:
    """Run the full segmentation pipeline.

    Parameters
    ----------
    features_dir:
        Directory with feature parquet files.
    models_dir:
        Where to save models and outputs.
    n_components:
        UMAP output dimensions (2 for visualization).
    min_cluster_size:
        HDBSCAN parameter.
    min_samples:
        HDBSCAN parameter.

    Returns
    -------
    Dict with keys: n_clusters, cluster_profiles, umap_path, labels_path.
    """
    try:
        import umap
        import hdbscan
    except ImportError as exc:
        logger.error("Missing dependency: %s. Install umap-learn and hdbscan.", exc)
        raise

    features_dir = features_dir or FEATURES_DIR
    models_dir = models_dir or MODELS_DIR
    models_dir.mkdir(parents=True, exist_ok=True)

    # Load feature data
    parquet_files = sorted(features_dir.glob("*_features.parquet"))
    if not parquet_files:
        raise FileNotFoundError(f"No feature files found in {features_dir}")

    dfs = [pd.read_parquet(f) for f in parquet_files]
    df = pd.concat(dfs, ignore_index=True)
    logger.info("Loaded %d rows for segmentation", len(df))

    # Select features
    available = [f for f in SEGMENTATION_FEATURES if f in df.columns]
    if len(available) < 5:
        raise ValueError(f"Too few features available ({len(available)}): {available}")

    X = df[available].copy()
    X = X.fillna(X.median())

    # Standardise
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    joblib.dump(scaler, models_dir / "seg_scaler.pkl")

    # UMAP
    logger.info("Running UMAP (n_components=%d)", n_components)
    reducer = umap.UMAP(
        n_components=n_components,
        n_neighbors=30,
        min_dist=0.1,
        metric="euclidean",
        random_state=42,
    )
    embedding = reducer.fit_transform(X_scaled)
    joblib.dump(reducer, models_dir / "seg_umap.pkl")

    df["umap_x"] = embedding[:, 0]
    df["umap_y"] = embedding[:, 1]

    # HDBSCAN
    logger.info("Running HDBSCAN (min_cluster_size=%d)", min_cluster_size)
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric="euclidean",
        cluster_selection_method="eom",
    )
    labels = clusterer.fit_predict(embedding)
    df["cluster_id"] = labels
    joblib.dump(clusterer, models_dir / "seg_hdbscan.pkl")

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    noise_pct = (labels == -1).mean() * 100
    logger.info("Found %d clusters (%.1f%% noise)", n_clusters, noise_pct)

    # RFM scoring
    df = compute_rfm_scores(df)

    # Cluster profiling
    profiles: list[dict[str, Any]] = []
    for cid in sorted(set(labels)):
        if cid == -1:
            continue
        mask = df["cluster_id"] == cid
        cluster_df = df.loc[mask, available]
        profile = cluster_df.mean().to_dict()
        profile["cluster_id"] = int(cid)
        profile["size"] = int(mask.sum())
        profile["name"] = _auto_name_cluster(profile)

        # Top languages / databases
        lang_cols = [c for c in df.columns if c.startswith("LanguageHaveWorkedWith__")]
        if lang_cols:
            lang_means = df.loc[mask, lang_cols].mean().sort_values(ascending=False)
            profile["top_languages"] = list(lang_means.head(5).index)

        profiles.append(profile)

    # Save outputs
    umap_path = models_dir / "umap_coordinates.parquet"
    cols_to_save = ["umap_x", "umap_y", "cluster_id", "rfm_recency",
                    "rfm_frequency", "rfm_monetary", "rfm_total"]
    if "ResponseId" in df.columns:
        cols_to_save.insert(0, "ResponseId")
    df[cols_to_save].to_parquet(umap_path, index=False)

    profiles_path = models_dir / "cluster_profiles.json"
    with open(profiles_path, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2, default=str)

    logger.info("Saved UMAP coordinates to %s", umap_path)
    logger.info("Saved cluster profiles to %s", profiles_path)

    return {
        "n_clusters": n_clusters,
        "noise_pct": noise_pct,
        "cluster_profiles": profiles,
        "umap_path": str(umap_path),
        "profiles_path": str(profiles_path),
    }


# ── CLI ───────────────────────────────────────────────────────────────────


def main() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    try:
        result = run_segmentation()
        print(f"\n✅  Segmentation complete — {result['n_clusters']} clusters found.")
    except FileNotFoundError as exc:
        print(f"\n❌  {exc}")


if __name__ == "__main__":
    main()
