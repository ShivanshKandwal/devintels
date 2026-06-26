"""
Feature Engineering Module.

Creates 35+ features across six groups from cleaned survey data:
- Career maturity
- Tech stack richness
- Learning behavior
- Work context
- Engagement
- Geographic

Usage:
    python -m src.features.engineer
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
FEATURES_DIR = PROJECT_ROOT / "data" / "features"

# ── country → continent mapping ──────────────────────────────────────────

CONTINENT_MAP: dict[str, str] = {
    "United States of America": "North America",
    "Canada": "North America",
    "Mexico": "North America",
    "Brazil": "South America",
    "Argentina": "South America",
    "United Kingdom of Great Britain and Northern Ireland": "Europe",
    "Germany": "Europe",
    "France": "Europe",
    "Netherlands": "Europe",
    "Poland": "Europe",
    "Spain": "Europe",
    "Italy": "Europe",
    "Sweden": "Europe",
    "Switzerland": "Europe",
    "Ukraine": "Europe",
    "Russian Federation": "Europe",
    "Turkey": "Europe",
    "Israel": "Asia",
    "India": "Asia",
    "Japan": "Asia",
    "China": "Asia",
    "South Korea": "Asia",
    "Indonesia": "Asia",
    "Pakistan": "Asia",
    "Philippines": "Asia",
    "Australia": "Oceania",
    "Nigeria": "Africa",
    "South Africa": "Africa",
}

HIGH_INCOME_COUNTRIES: set[str] = {
    "United States of America",
    "Canada",
    "United Kingdom of Great Britain and Northern Ireland",
    "Germany",
    "France",
    "Netherlands",
    "Sweden",
    "Switzerland",
    "Australia",
    "Japan",
    "South Korea",
    "Israel",
    "Italy",
    "Spain",
}

# ── industry encoding ────────────────────────────────────────────────────

INDUSTRY_ENCODING: dict[str, int] = {
    "Information Services, IT, Software Development, or other Technology": 1,
    "Financial Services": 2,
    "Manufacturing, Transportation, or Supply Chain": 3,
    "Healthcare": 4,
    "Retail and Consumer Services": 5,
    "Higher Education": 6,
    "Insurance": 7,
    "Wholesale": 8,
    "Oil & Gas": 9,
    "Advertising Services": 10,
    "Legal Services": 11,
    "Unknown": 0,
}


# ── feature helpers ───────────────────────────────────────────────────────


def _count_binary_cols(df: pd.DataFrame, prefix: str) -> pd.Series:
    """Sum binary indicator columns matching *prefix*."""
    cols = [c for c in df.columns if c.startswith(prefix)]
    if not cols:
        return pd.Series(0, index=df.index, dtype=int)
    return df[cols].sum(axis=1).astype(int)


def _has_any(df: pd.DataFrame, prefix: str, *substrings: str) -> pd.Series:
    """Return 1 if any binary column matching prefix + substring is 1."""
    for sub in substrings:
        cols = [c for c in df.columns if c.startswith(prefix) and sub in c.lower()]
        if cols:
            mask = df[cols].max(axis=1) > 0
            if mask.any():
                return mask.astype(int)
    return pd.Series(0, index=df.index, dtype=int)


# ── feature groups ────────────────────────────────────────────────────────


def add_career_maturity(df: pd.DataFrame) -> pd.DataFrame:
    """Add career-maturity features.

    Features:
        years_code_num, years_code_pro_num, experience_gap, career_stage
    """
    if "YearsCode_num" in df.columns:
        df["years_code_num"] = df["YearsCode_num"]
    elif "YearsCode" in df.columns:
        from ..data.clean import encode_years_code
        df["years_code_num"] = encode_years_code(df["YearsCode"])
    else:
        df["years_code_num"] = np.nan

    if "YearsCodePro_num" in df.columns:
        df["years_code_pro_num"] = df["YearsCodePro_num"]
    elif "YearsCodePro" in df.columns:
        from ..data.clean import encode_years_code
        df["years_code_pro_num"] = encode_years_code(df["YearsCodePro"])
    else:
        df["years_code_pro_num"] = np.nan

    df["experience_gap"] = df["years_code_num"] - df["years_code_pro_num"]
    df["experience_gap"] = df["experience_gap"].clip(lower=0)

    # Career stage buckets
    bins = [-1, 2, 5, 10, 20, 100]
    labels = ["novice", "junior", "mid", "senior", "veteran"]
    df["career_stage"] = pd.cut(
        df["years_code_pro_num"],
        bins=bins,
        labels=labels,
        right=True,
    ).astype(str)
    df["career_stage"] = df["career_stage"].replace("nan", "unknown")

    return df


def add_tech_stack(df: pd.DataFrame) -> pd.DataFrame:
    """Add tech-stack richness features.

    Features:
        lang_count, db_count, platform_count, misc_tech_count, tool_count,
        ai_tool_count, stack_diversity_score, uses_python, uses_javascript,
        uses_cloud, uses_ai_tools
    """
    df["lang_count"] = _count_binary_cols(df, "LanguageHaveWorkedWith__")
    df["db_count"] = _count_binary_cols(df, "DatabaseHaveWorkedWith__")
    df["platform_count"] = _count_binary_cols(df, "PlatformHaveWorkedWith__")
    df["misc_tech_count"] = _count_binary_cols(df, "MiscTechHaveWorkedWith__")
    df["tool_count"] = _count_binary_cols(df, "ToolsTechHaveWorkedWith__")
    df["ai_tool_count"] = (
        _count_binary_cols(df, "AIDevHaveWorkedWith__")
        + _count_binary_cols(df, "AISearchHaveWorkedWith__")
    )
    df["collab_tool_count"] = _count_binary_cols(df, "NEWCollabToolsHaveWorkedWith__")

    # Diversity score = total unique tech across all categories
    df["stack_diversity_score"] = (
        df["lang_count"]
        + df["db_count"]
        + df["platform_count"]
        + df["misc_tech_count"]
        + df["tool_count"]
    )

    # Boolean flags
    df["uses_python"] = _has_any(df, "LanguageHaveWorkedWith__", "python")
    df["uses_javascript"] = _has_any(df, "LanguageHaveWorkedWith__", "javascript")
    df["uses_cloud"] = _has_any(
        df,
        "PlatformHaveWorkedWith__",
        "aws", "azure", "google_cloud",
    )
    df["uses_ai_tools"] = (df["ai_tool_count"] > 0).astype(int)

    return df


def add_learning(df: pd.DataFrame) -> pd.DataFrame:
    """Add learning-behavior features.

    Features:
        learns_online, uses_docs_as_primary, learning_diversity,
        learn_source_count, learn_online_count
    """
    df["learn_source_count"] = _count_binary_cols(df, "LearnCode__")
    df["learn_online_count"] = _count_binary_cols(df, "LearnCodeOnline__")
    df["learning_diversity"] = df["learn_source_count"] + df["learn_online_count"]

    df["learns_online"] = _has_any(
        df,
        "LearnCodeOnline__",
        "stack_overflow", "blogs", "how_to_videos", "written_tutorials",
    )

    df["uses_docs_as_primary"] = _has_any(
        df,
        "LearnCodeOnline__",
        "technical_documentation",
    )

    return df


def add_work_context(df: pd.DataFrame) -> pd.DataFrame:
    """Add work-context features.

    Features:
        is_remote, is_hybrid, org_size_num, is_large_org,
        industry_encoded, is_employed
    """
    if "RemoteWork" in df.columns:
        df["is_remote"] = (df["RemoteWork"] == "Remote").astype(int)
        df["is_hybrid"] = df["RemoteWork"].str.contains("Hybrid", case=False, na=False).astype(int)
    else:
        df["is_remote"] = 0
        df["is_hybrid"] = 0

    if "org_size_num" not in df.columns:
        if "OrgSize" in df.columns:
            from ..data.clean import ORG_SIZE_MAP
            df["org_size_num"] = df["OrgSize"].map(ORG_SIZE_MAP)
        else:
            df["org_size_num"] = np.nan

    df["org_size_num"] = pd.to_numeric(df["org_size_num"], errors="coerce")
    df["is_large_org"] = (df["org_size_num"] >= 7).astype(int)

    if "Industry" in df.columns:
        df["industry_encoded"] = df["Industry"].map(INDUSTRY_ENCODING).fillna(0).astype(int)
    elif "industry_encoded" not in df.columns:
        df["industry_encoded"] = 0

    if "Employment" in df.columns:
        df["is_employed"] = df["Employment"].str.contains(
            "Employed|contractor|self-employed", case=False, na=False, regex=True
        ).astype(int)
    else:
        df["is_employed"] = 0

    return df


def add_engagement(df: pd.DataFrame) -> pd.DataFrame:
    """Add engagement features.

    Features:
        job_sat_score, is_actively_looking, so_engagement_score,
        ai_sentiment_score
    """
    if "job_sat_score" not in df.columns:
        if "JobSat" in df.columns:
            from ..data.clean import JOB_SAT_MAP
            df["job_sat_score"] = df["JobSat"].map(JOB_SAT_MAP)
        else:
            df["job_sat_score"] = np.nan

    df["job_sat_score"] = pd.to_numeric(df["job_sat_score"], errors="coerce").fillna(3)

    if "Employment" in df.columns:
        df["is_actively_looking"] = df["Employment"].str.contains(
            "looking", case=False, na=False
        ).astype(int)
    else:
        df["is_actively_looking"] = 0

    # SO engagement score
    so_freq_map = {
        "Multiple times per day": 5,
        "Daily or almost daily": 4,
        "A few times per week": 3,
        "A few times per month or weekly": 2,
        "Less than once per month or monthly": 1,
        "I have never visited Stack Overflow": 0,
    }
    if "SOVisitFreq" in df.columns:
        df["so_engagement_score"] = df["SOVisitFreq"].map(so_freq_map).fillna(2)
    else:
        df["so_engagement_score"] = 2

    # AI sentiment score
    ai_sent_map = {
        "Very favorable": 5,
        "Favorable": 4,
        "Indifferent": 3,
        "Unsure": 2,
        "Unfavorable": 1,
        "Very unfavorable": 0,
    }
    if "AISent" in df.columns:
        df["ai_sentiment_score"] = df["AISent"].map(ai_sent_map).fillna(3)
    else:
        df["ai_sentiment_score"] = 3

    # Time searching proxy (from AI/search tool counts)
    df["time_searching"] = df.get("ai_tool_count", pd.Series(0, index=df.index))

    return df


def add_geographic(df: pd.DataFrame) -> pd.DataFrame:
    """Add geographic features.

    Features:
        continent, is_high_income_country
    """
    if "Country" in df.columns:
        df["continent"] = df["Country"].map(CONTINENT_MAP).fillna("Other")
        df["is_high_income_country"] = df["Country"].isin(HIGH_INCOME_COUNTRIES).astype(int)
    else:
        df["continent"] = "Unknown"
        df["is_high_income_country"] = 0

    return df


# ── main pipeline ─────────────────────────────────────────────────────────

FEATURE_GROUPS = [
    add_career_maturity,
    add_tech_stack,
    add_learning,
    add_work_context,
    add_engagement,
    add_geographic,
]


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Run all feature-engineering groups on *df*.

    Parameters
    ----------
    df:
        Cleaned DataFrame (output of :func:`src.data.clean.clean_survey_data`).

    Returns
    -------
    DataFrame with 35+ new feature columns.
    """
    logger.info("Engineering features — starting with %d cols", len(df.columns))

    for fn in FEATURE_GROUPS:
        df = fn(df)
        logger.debug("After %s: %d cols", fn.__name__, len(df.columns))

    new_features = [
        "years_code_num", "years_code_pro_num", "experience_gap", "career_stage",
        "lang_count", "db_count", "platform_count", "misc_tech_count",
        "tool_count", "ai_tool_count", "collab_tool_count",
        "stack_diversity_score", "uses_python", "uses_javascript",
        "uses_cloud", "uses_ai_tools",
        "learn_source_count", "learn_online_count", "learning_diversity",
        "learns_online", "uses_docs_as_primary",
        "is_remote", "is_hybrid", "org_size_num", "is_large_org",
        "industry_encoded", "is_employed",
        "job_sat_score", "is_actively_looking", "so_engagement_score",
        "ai_sentiment_score", "time_searching",
        "continent", "is_high_income_country",
    ]

    present = [f for f in new_features if f in df.columns]
    logger.info("Feature engineering complete — %d new features, %d total cols",
                len(present), len(df.columns))

    return df


def get_model_features(df: pd.DataFrame) -> list[str]:
    """Return the list of numeric feature columns suitable for ML models.

    Parameters
    ----------
    df:
        DataFrame with engineered features.

    Returns
    -------
    Sorted list of numeric column names (excluding targets and IDs).
    """
    exclude = {
        "ResponseId", "survey_year",
        "is_ai_ml_developer", "is_high_earner", "is_satisfied", "churn_risk",
        "ConvertedCompYearly", "log_salary",
        "career_stage", "continent",  # categorical, not numeric
    }
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    features = sorted(set(numeric_cols) - exclude)
    return features


def run_feature_engineering(
    processed_dir: Path | None = None,
    output_dir: Path | None = None,
) -> list[Path]:
    """Load cleaned data, engineer features, save to data/features/.

    Parameters
    ----------
    processed_dir:
        Directory with cleaned parquet files.
    output_dir:
        Where to write feature files.

    Returns
    -------
    List of written file paths.
    """
    processed_dir = processed_dir or PROCESSED_DIR
    output_dir = output_dir or FEATURES_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    parquet_files = sorted(processed_dir.glob("*_clean.parquet"))
    if not parquet_files:
        logger.warning("No cleaned parquet files in %s", processed_dir)
        return []

    written: list[Path] = []
    for pq_path in parquet_files:
        logger.info("Engineering features for %s", pq_path.name)
        df = pd.read_parquet(pq_path)
        df = engineer_features(df)

        out_name = pq_path.stem.replace("_clean", "_features") + ".parquet"
        out_path = output_dir / out_name
        df.to_parquet(out_path, index=False)
        logger.info("Saved %s (%d rows, %d cols)", out_path.name, len(df), len(df.columns))
        written.append(out_path)

    return written


# ── CLI ───────────────────────────────────────────────────────────────────


def main() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    paths = run_feature_engineering()
    print(f"\n✅  Engineered features for {len(paths)} file(s).")
    for p in paths:
        print(f"   📄 {p}")


if __name__ == "__main__":
    main()
