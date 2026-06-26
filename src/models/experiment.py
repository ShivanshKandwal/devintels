"""
Experimentation Module.

Causal inference experiments to measure the impact of AI tool adoption:
- Propensity score matching (AI tool users vs non-users)
- Pre/post match balance tables (SMD)
- Hypothesis testing (t-test, Mann-Whitney, chi-square, Bonferroni)
- Uplift modeling (CausalForestDML from econml)
- Results saved to models/experiment_results.json

Usage:
    python -m src.models.experiment
"""

from __future__ import annotations

import json
import logging
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FEATURES_DIR = PROJECT_ROOT / "data" / "features"
MODELS_DIR = PROJECT_ROOT / "models"

# Treatment: AI tool user vs non-user
TREATMENT_COL = "uses_ai_tools"

# Confounders for propensity score model
CONFOUNDERS: list[str] = [
    "years_code_pro_num", "experience_gap",
    "lang_count", "db_count", "stack_diversity_score",
    "learning_diversity", "is_remote", "org_size_num",
    "is_large_org", "ed_level_num", "is_high_income_country",
    "is_employed",
]

# Outcome variables
OUTCOMES: list[str] = [
    "job_sat_score",
    "is_high_earner",
    "so_engagement_score",
    "stack_diversity_score",
]


def _load_data(features_dir: Path) -> pd.DataFrame:
    """Load and concatenate feature parquet files."""
    parquet_files = sorted(features_dir.glob("*_features.parquet"))
    if not parquet_files:
        raise FileNotFoundError(f"No feature files in {features_dir}")
    dfs = [pd.read_parquet(f) for f in parquet_files]
    return pd.concat(dfs, ignore_index=True)


def compute_propensity_scores(
    df: pd.DataFrame,
    treatment_col: str = TREATMENT_COL,
    confounders: list[str] | None = None,
) -> pd.Series:
    """Fit logistic regression to estimate propensity scores.

    Parameters
    ----------
    df:
        DataFrame with treatment and confounder columns.
    treatment_col:
        Binary treatment column.
    confounders:
        List of confounder columns.

    Returns
    -------
    Series of propensity scores (P(treatment=1 | confounders)).
    """
    confounders = confounders or CONFOUNDERS
    available = [c for c in confounders if c in df.columns]

    X = df[available].copy().fillna(0)
    y = df[treatment_col].astype(int)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = LogisticRegression(max_iter=1000, C=1.0, random_state=42)
    model.fit(X_scaled, y)

    propensity = model.predict_proba(X_scaled)[:, 1]
    logger.info(
        "Propensity score distribution: mean=%.3f, std=%.3f",
        propensity.mean(),
        propensity.std(),
    )

    return pd.Series(propensity, index=df.index, name="propensity_score")


def match_nearest_neighbor(
    df: pd.DataFrame,
    propensity_scores: pd.Series,
    treatment_col: str = TREATMENT_COL,
    caliper: float = 0.05,
    n_neighbors: int = 1,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Perform 1:1 nearest-neighbor matching on propensity scores.

    Parameters
    ----------
    df:
        Input DataFrame.
    propensity_scores:
        Propensity scores.
    treatment_col:
        Binary treatment column.
    caliper:
        Maximum distance for a valid match.
    n_neighbors:
        Number of control matches per treated unit.

    Returns
    -------
    Tuple of (matched_treated, matched_control) DataFrames.
    """
    treated_idx = df[df[treatment_col] == 1].index
    control_idx = df[df[treatment_col] == 0].index

    treated_ps = propensity_scores.loc[treated_idx].values.reshape(-1, 1)
    control_ps = propensity_scores.loc[control_idx].values.reshape(-1, 1)

    nn = NearestNeighbors(n_neighbors=n_neighbors, metric="euclidean")
    nn.fit(control_ps)
    distances, indices = nn.kneighbors(treated_ps)

    # Apply caliper
    valid_mask = distances[:, 0] <= caliper
    matched_treated_idx = treated_idx[valid_mask]
    matched_control_idx = control_idx[indices[valid_mask, 0]]

    logger.info(
        "Matched %d/%d treated units (%.1f%% within caliper=%.3f)",
        len(matched_treated_idx),
        len(treated_idx),
        len(matched_treated_idx) / max(len(treated_idx), 1) * 100,
        caliper,
    )

    return df.loc[matched_treated_idx], df.loc[matched_control_idx]


def compute_smd(
    treated: pd.DataFrame,
    control: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    """Compute Standardized Mean Difference (SMD) for balance assessment.

    Parameters
    ----------
    treated:
        Treated group DataFrame.
    control:
        Control group DataFrame.
    columns:
        Columns to compute SMD for.

    Returns
    -------
    DataFrame with columns: variable, treated_mean, control_mean, smd, balanced.
    """
    records: list[dict[str, Any]] = []
    for col in columns:
        if col not in treated.columns or col not in control.columns:
            continue

        t_vals = pd.to_numeric(treated[col], errors="coerce").dropna()
        c_vals = pd.to_numeric(control[col], errors="coerce").dropna()

        if len(t_vals) == 0 or len(c_vals) == 0:
            continue

        t_mean = t_vals.mean()
        c_mean = c_vals.mean()
        pooled_std = np.sqrt((t_vals.var() + c_vals.var()) / 2)

        smd = abs(t_mean - c_mean) / pooled_std if pooled_std > 0 else 0.0

        records.append({
            "variable": col,
            "treated_mean": round(float(t_mean), 4),
            "control_mean": round(float(c_mean), 4),
            "smd": round(float(smd), 4),
            "balanced": smd < 0.1,
        })

    return pd.DataFrame(records)


def run_hypothesis_tests(
    treated: pd.DataFrame,
    control: pd.DataFrame,
    outcomes: list[str] | None = None,
    alpha: float = 0.05,
) -> list[dict[str, Any]]:
    """Run hypothesis tests on outcomes with Bonferroni correction.

    Tests used:
    - Continuous outcomes: Welch's t-test + Mann-Whitney U
    - Binary outcomes: Chi-square test

    Parameters
    ----------
    treated, control:
        Matched groups.
    outcomes:
        Outcome variables to test.
    alpha:
        Base significance level (before Bonferroni).

    Returns
    -------
    List of test-result dicts.
    """
    outcomes = outcomes or OUTCOMES
    n_tests = len(outcomes)
    bonferroni_alpha = alpha / max(n_tests, 1)

    results: list[dict[str, Any]] = []

    for outcome in outcomes:
        if outcome not in treated.columns or outcome not in control.columns:
            continue

        t_vals = pd.to_numeric(treated[outcome], errors="coerce").dropna().values
        c_vals = pd.to_numeric(control[outcome], errors="coerce").dropna().values

        if len(t_vals) < 10 or len(c_vals) < 10:
            continue

        t_mean = float(t_vals.mean())
        c_mean = float(c_vals.mean())
        effect_size = t_mean - c_mean

        is_binary = set(np.unique(t_vals)).issubset({0, 1}) and set(np.unique(c_vals)).issubset({0, 1})

        test_result: dict[str, Any] = {
            "outcome": outcome,
            "treated_mean": round(t_mean, 4),
            "control_mean": round(c_mean, 4),
            "effect_size": round(effect_size, 4),
            "n_treated": len(t_vals),
            "n_control": len(c_vals),
            "bonferroni_alpha": round(bonferroni_alpha, 6),
        }

        if is_binary:
            # Chi-square test
            contingency = np.array([
                [t_vals.sum(), len(t_vals) - t_vals.sum()],
                [c_vals.sum(), len(c_vals) - c_vals.sum()],
            ])
            chi2, p_chi, _, _ = stats.chi2_contingency(contingency)
            test_result["test"] = "chi-square"
            test_result["statistic"] = round(float(chi2), 4)
            test_result["p_value"] = round(float(p_chi), 6)
            test_result["significant"] = bool(p_chi < bonferroni_alpha)
        else:
            # Welch's t-test
            t_stat, p_ttest = stats.ttest_ind(t_vals, c_vals, equal_var=False)
            # Mann-Whitney U
            u_stat, p_mw = stats.mannwhitneyu(t_vals, c_vals, alternative="two-sided")

            test_result["test_ttest"] = {
                "statistic": round(float(t_stat), 4),
                "p_value": round(float(p_ttest), 6),
                "significant": bool(p_ttest < bonferroni_alpha),
            }
            test_result["test_mannwhitney"] = {
                "statistic": round(float(u_stat), 4),
                "p_value": round(float(p_mw), 6),
                "significant": bool(p_mw < bonferroni_alpha),
            }
            test_result["test"] = "ttest+mannwhitney"
            test_result["p_value"] = round(float(min(p_ttest, p_mw)), 6)
            test_result["significant"] = bool(
                p_ttest < bonferroni_alpha or p_mw < bonferroni_alpha
            )

        # Cohen's d effect size
        pooled_std = np.sqrt((t_vals.var() + c_vals.var()) / 2)
        cohens_d = effect_size / pooled_std if pooled_std > 0 else 0
        test_result["cohens_d"] = round(float(cohens_d), 4)

        results.append(test_result)

    return results


def run_uplift_model(
    df: pd.DataFrame,
    treatment_col: str = TREATMENT_COL,
    outcome_col: str = "job_sat_score",
    confounders: list[str] | None = None,
) -> dict[str, Any] | None:
    """Run CausalForestDML uplift model.

    Parameters
    ----------
    df:
        Full DataFrame (not matched).
    treatment_col:
        Binary treatment.
    outcome_col:
        Continuous outcome.
    confounders:
        Confounder columns.

    Returns
    -------
    Dict with ATE, CATE distribution, or None if econml unavailable.
    """
    try:
        from econml.dml import CausalForestDML
        from sklearn.ensemble import GradientBoostingRegressor, GradientBoostingClassifier
    except ImportError:
        logger.warning("econml not installed — skipping uplift modeling.")
        return None

    confounders = confounders or CONFOUNDERS
    available = [c for c in confounders if c in df.columns]

    if outcome_col not in df.columns or treatment_col not in df.columns:
        return None

    df_model = df[[treatment_col, outcome_col] + available].dropna()
    if len(df_model) < 100:
        logger.warning("Insufficient data for uplift model (%d rows).", len(df_model))
        return None

    X = df_model[available].values
    T = df_model[treatment_col].values.astype(float)
    Y = df_model[outcome_col].values.astype(float)

    try:
        est = CausalForestDML(
            model_y=GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42),
            model_t=GradientBoostingClassifier(n_estimators=100, max_depth=4, random_state=42),
            n_estimators=200,
            random_state=42,
        )
        est.fit(Y, T, X=X)

        ate = float(est.ate(X))
        cate = est.effect(X)
        ate_ci = est.ate_interval(X, alpha=0.05)

        result = {
            "ate": round(ate, 4),
            "ate_ci_lower": round(float(ate_ci[0]), 4),
            "ate_ci_upper": round(float(ate_ci[1]), 4),
            "cate_mean": round(float(cate.mean()), 4),
            "cate_std": round(float(cate.std()), 4),
            "cate_median": round(float(np.median(cate)), 4),
            "n_positive_cate": int((cate > 0).sum()),
            "n_negative_cate": int((cate < 0).sum()),
            "n_total": len(cate),
        }

        logger.info("Uplift ATE: %.4f (95%% CI: [%.4f, %.4f])", ate, ate_ci[0], ate_ci[1])
        return result
    except Exception as exc:
        logger.error("CausalForestDML failed: %s", exc)
        return None


def run_experiment(
    features_dir: Path | None = None,
    models_dir: Path | None = None,
) -> dict[str, Any]:
    """Run the full experiment pipeline.

    Parameters
    ----------
    features_dir:
        Directory with feature files.
    models_dir:
        Where to save results.

    Returns
    -------
    Dict with all experiment results.
    """
    features_dir = features_dir or FEATURES_DIR
    models_dir = models_dir or MODELS_DIR
    models_dir.mkdir(parents=True, exist_ok=True)

    df = _load_data(features_dir)
    logger.info("Loaded %d rows for experimentation", len(df))

    if TREATMENT_COL not in df.columns:
        raise ValueError(f"Treatment column '{TREATMENT_COL}' not found.")

    # 1. Propensity scores
    logger.info("Computing propensity scores...")
    propensity = compute_propensity_scores(df)
    df["propensity_score"] = propensity

    # 2. Pre-match balance
    available_confounders = [c for c in CONFOUNDERS if c in df.columns]
    treated_pre = df[df[TREATMENT_COL] == 1]
    control_pre = df[df[TREATMENT_COL] == 0]
    pre_balance = compute_smd(treated_pre, control_pre, available_confounders)
    logger.info("Pre-match balance: %d/%d variables balanced (SMD<0.1)",
                pre_balance["balanced"].sum(), len(pre_balance))

    # 3. Matching
    logger.info("Running propensity score matching...")
    matched_treated, matched_control = match_nearest_neighbor(df, propensity)

    # 4. Post-match balance
    post_balance = compute_smd(matched_treated, matched_control, available_confounders)
    logger.info("Post-match balance: %d/%d variables balanced (SMD<0.1)",
                post_balance["balanced"].sum(), len(post_balance))

    # 5. Hypothesis tests
    logger.info("Running hypothesis tests...")
    test_results = run_hypothesis_tests(matched_treated, matched_control)

    # 6. Uplift modeling
    logger.info("Running uplift model...")
    uplift_result = run_uplift_model(df)

    # Compile results
    results: dict[str, Any] = {
        "treatment": TREATMENT_COL,
        "n_treated": len(treated_pre),
        "n_control": len(control_pre),
        "n_matched_treated": len(matched_treated),
        "n_matched_control": len(matched_control),
        "pre_match_balance": pre_balance.to_dict(orient="records"),
        "post_match_balance": post_balance.to_dict(orient="records"),
        "hypothesis_tests": test_results,
        "uplift_model": uplift_result,
    }

    # Save
    output_path = models_dir / "experiment_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    logger.info("Experiment results saved to %s", output_path)

    return results


# ── CLI ───────────────────────────────────────────────────────────────────


def main() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    try:
        results = run_experiment()
        print(f"\n✅  Experiment complete.")
        print(f"   Matched {results['n_matched_treated']} treated ↔ {results['n_matched_control']} control")
        sig_tests = [t for t in results["hypothesis_tests"] if t.get("significant")]
        print(f"   Significant outcomes: {len(sig_tests)}/{len(results['hypothesis_tests'])}")
    except (FileNotFoundError, ValueError) as exc:
        print(f"\n❌  {exc}")


if __name__ == "__main__":
    main()
