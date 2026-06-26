"""
Data Cleaning Pipeline.

Full cleaning pipeline for Stack Overflow Developer Survey data:
- Multi-select column explosion (semicolon-separated → binary indicators)
- Ordinal encoding (YearsCode, EdLevel, OrgSize)
- Salary cleaning (cap at 99th percentile, log-transform)
- Target variable engineering
- Missing-value strategy (documented inline)

Usage:
    python -m src.data.clean
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# ── ordinal encoding maps ─────────────────────────────────────────────────

YEARS_CODE_MAP: dict[str, float] = {
    "Less than 1 year": 0.5,
    "More than 50 years": 51.0,
}
# Numeric strings ("1", "2", …) are handled dynamically.

ED_LEVEL_MAP: dict[str, int] = {
    "Primary/elementary school": 1,
    "Secondary school (e.g. American high school, German Realschule or Gymnasium, etc.)": 2,
    "Some college/university study without earning a degree": 3,
    "Associate degree (A.A., A.S., etc.)": 4,
    "Bachelor's degree (B.A., B.S., B.Eng., etc.)": 5,
    "Master's degree (M.A., M.S., M.Eng., MBA, etc.)": 6,
    "Professional degree (JD, MD, Ph.D, Ed.D, etc.)": 7,
    "Something else": 3,
}

ORG_SIZE_MAP: dict[str, int] = {
    "Just me - I am a freelancer, sole proprietor, etc.": 1,
    "2 to 9 employees": 2,
    "10 to 19 employees": 3,
    "20 to 99 employees": 4,
    "100 to 499 employees": 5,
    "500 to 999 employees": 6,
    "1,000 to 4,999 employees": 7,
    "5,000 to 9,999 employees": 8,
    "10,000 or more employees": 9,
    "I don't know": np.nan,  # type: ignore[dict-item]
}

JOB_SAT_MAP: dict[str, int] = {
    "Very dissatisfied": 1,
    "Slightly dissatisfied": 2,
    "Neither satisfied nor dissatisfied": 3,
    "Slightly satisfied": 4,
    "Very satisfied": 5,
}

# Multi-select columns that should be exploded into binary indicators
MULTI_SELECT_COLUMNS: list[str] = [
    "LanguageHaveWorkedWith",
    "LanguageWantToWorkWith",
    "DatabaseHaveWorkedWith",
    "DatabaseWantToWorkWith",
    "PlatformHaveWorkedWith",
    "MiscTechHaveWorkedWith",
    "ToolsTechHaveWorkedWith",
    "NEWCollabToolsHaveWorkedWith",
    "AISearchHaveWorkedWith",
    "AIDevHaveWorkedWith",
    "LearnCode",
    "LearnCodeOnline",
    "LearnCodeCoursesCert",
    "CodingActivities",
    "AIToolCurrentlyUsing",
    "AIToolInterested",
    "DevType",
]


# ── helper functions ──────────────────────────────────────────────────────


def _safe_col_name(text: str) -> str:
    """Convert a raw value into a safe column suffix.

    ``"Amazon Web Services (AWS)"`` → ``"amazon_web_services_aws"``
    """
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def explode_multi_select(
    df: pd.DataFrame,
    column: str,
    prefix: str | None = None,
    drop_original: bool = True,
    top_n: int | None = 50,
) -> pd.DataFrame:
    """Explode a semicolon-separated column into binary indicator columns.

    Parameters
    ----------
    df:
        Input DataFrame.
    column:
        The multi-select column.
    prefix:
        Column name prefix. Defaults to the original column name.
    drop_original:
        Whether to drop the original column.
    top_n:
        Keep only the top_n most frequent values. ``None`` keeps all.

    Returns
    -------
    DataFrame with new binary columns.

    Decision
    --------
    We use binary indicators rather than count-encoding because downstream
    ML models benefit from interpretable binary features, and the cardinality
    of each item set is already captured by the ``*_count`` features in
    :mod:`src.features.engineer`.
    """
    if column not in df.columns:
        logger.warning("Column %s not in DataFrame — skipping.", column)
        return df

    pfx = prefix or column
    series = df[column].fillna("")

    # Collect all unique values
    all_values: set[str] = set()
    for cell in series:
        if cell:
            for item in str(cell).split(";"):
                item = item.strip()
                if item:
                    all_values.add(item)

    # Optionally limit to top_n
    if top_n is not None and len(all_values) > top_n:
        counts: dict[str, int] = {}
        for cell in series:
            if cell:
                for item in str(cell).split(";"):
                    item = item.strip()
                    if item:
                        counts[item] = counts.get(item, 0) + 1
        sorted_items = sorted(counts, key=counts.get, reverse=True)  # type: ignore[arg-type]
        all_values = set(sorted_items[:top_n])

    # Build binary columns
    for value in sorted(all_values):
        col_name = f"{pfx}__{_safe_col_name(value)}"
        df[col_name] = series.apply(lambda x, v=value: int(v in str(x).split(";")))

    if drop_original:
        df = df.drop(columns=[column])

    return df


def encode_years_code(series: pd.Series) -> pd.Series:
    """Convert YearsCode / YearsCodePro strings to numeric.

    Decision: "Less than 1 year" → 0.5, "More than 50 years" → 51,
    numeric strings → int, NaN stays NaN.
    """

    def _convert(val: Any) -> float:
        if pd.isna(val):
            return np.nan
        val_str = str(val).strip()
        if val_str in YEARS_CODE_MAP:
            return YEARS_CODE_MAP[val_str]
        try:
            return float(val_str)
        except ValueError:
            return np.nan

    return series.apply(_convert)


def clean_salary(df: pd.DataFrame, col: str = "ConvertedCompYearly") -> pd.DataFrame:
    """Cap salary at 99th percentile and add log-transformed column.

    Decision
    --------
    - Values ≤ 0 are set to NaN (nonsensical).
    - We cap at the 99th percentile to limit extreme outlier influence
      while retaining enough variance for modelling.
    - Log-transform uses ``log1p`` to handle the (unlikely) edge-case of
      salary == 0 after capping.
    """
    if col not in df.columns:
        logger.warning("Salary column %s not found — skipping.", col)
        return df

    df[col] = pd.to_numeric(df[col], errors="coerce")
    df.loc[df[col] <= 0, col] = np.nan

    cap = df[col].quantile(0.99)
    if pd.notna(cap) and cap > 0:
        df[col] = df[col].clip(upper=cap)
        logger.info("Salary capped at 99th percentile: $%,.0f", cap)

    df["log_salary"] = np.log1p(df[col])
    return df


def engineer_targets(df: pd.DataFrame) -> pd.DataFrame:
    """Create target / label columns for downstream modelling.

    Targets created
    ---------------
    - ``is_ai_ml_developer``: DevType contains 'data scientist' or 'machine learning'.
    - ``is_high_earner``: ConvertedCompYearly ≥ 75th percentile (among non-null).
    - ``is_satisfied``: JobSat ∈ {Very satisfied, Slightly satisfied}.
    - ``churn_risk``: Composite flag — dissatisfied AND (looking for work OR low pay).

    Decision: churn_risk is an *approximate* label because we lack actual
    attrition data; it is useful for modelling relative risk, not absolute.
    """
    # is_ai_ml_developer
    if "DevType" in df.columns:
        devtype_str = df["DevType"].fillna("").str.lower()
        df["is_ai_ml_developer"] = (
            devtype_str.str.contains("data scientist|machine learning", regex=True)
        ).astype(int)
    else:
        # If DevType was already exploded, look for indicator columns
        ai_cols = [c for c in df.columns if "data_scientist" in c or "machine_learning" in c]
        if ai_cols:
            df["is_ai_ml_developer"] = df[ai_cols].max(axis=1).astype(int)
        else:
            df["is_ai_ml_developer"] = 0

    # is_high_earner
    salary_col = "ConvertedCompYearly"
    if salary_col in df.columns:
        p75 = df[salary_col].quantile(0.75)
        df["is_high_earner"] = (df[salary_col] >= p75).astype(int)
        # NaN salary → 0 (conservative: unknown ≠ high earner)
        df["is_high_earner"] = df["is_high_earner"].fillna(0).astype(int)
    else:
        df["is_high_earner"] = 0

    # is_satisfied
    if "JobSat" in df.columns:
        df["is_satisfied"] = df["JobSat"].isin(
            ["Very satisfied", "Slightly satisfied"]
        ).astype(int)
    elif "job_sat_score" in df.columns:
        df["is_satisfied"] = (df["job_sat_score"] >= 4).astype(int)
    else:
        df["is_satisfied"] = 0

    # churn_risk — composite
    dissatisfied = 0
    if "JobSat" in df.columns:
        dissatisfied = df["JobSat"].isin(
            ["Slightly dissatisfied", "Very dissatisfied"]
        ).astype(int)
    elif "job_sat_score" in df.columns:
        dissatisfied = (df["job_sat_score"] <= 2).astype(int)

    looking = 0
    if "Employment" in df.columns:
        looking = df["Employment"].str.contains("looking", case=False, na=False).astype(int)

    low_pay = 0
    if salary_col in df.columns:
        p25 = df[salary_col].quantile(0.25)
        low_pay = (df[salary_col] < p25).astype(int).fillna(0)

    df["churn_risk"] = ((dissatisfied == 1) & ((looking == 1) | (low_pay == 1))).astype(int)

    return df


def handle_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Apply missing-value strategy.

    Strategy (documented per column type)
    --------------------------------------
    - **Numeric columns**: median imputation. Rationale — preserves central
      tendency without distortion from outliers.
    - **Categorical/object columns**: fill with ``"Unknown"``. Rationale —
      preserves missingness as a distinct category that may carry signal
      (e.g., privacy-conscious respondents).
    - **Binary indicator columns** (0/1): fill with 0. Rationale — absence
      of a response implies non-usage.
    - **Target columns**: left as-is (handled by model training logic).
    """
    target_cols = {"is_ai_ml_developer", "is_high_earner", "is_satisfied", "churn_risk"}

    for col in df.columns:
        if col in target_cols:
            continue

        if df[col].dtype in ("float64", "float32", "int64", "int32"):
            # Check if it's a binary indicator
            unique_vals = df[col].dropna().unique()
            if set(unique_vals).issubset({0, 1, 0.0, 1.0}):
                df[col] = df[col].fillna(0).astype(int)
            else:
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
        elif df[col].dtype == object:
            df[col] = df[col].fillna("Unknown")

    return df


# ── main cleaning pipeline ────────────────────────────────────────────────


def clean_survey_data(
    df: pd.DataFrame,
    explode_multiselect: bool = True,
) -> pd.DataFrame:
    """Run the full cleaning pipeline on a raw survey DataFrame.

    Parameters
    ----------
    df:
        Raw DataFrame (from CSV).
    explode_multiselect:
        Whether to explode multi-select columns into binary indicators.

    Returns
    -------
    Cleaned DataFrame.
    """
    logger.info("Starting cleaning pipeline — %d rows, %d cols", len(df), len(df.columns))

    # 1. Ordinal encodings
    for yc_col in ("YearsCode", "YearsCodePro"):
        if yc_col in df.columns:
            df[f"{yc_col}_num"] = encode_years_code(df[yc_col])

    if "EdLevel" in df.columns:
        df["ed_level_num"] = df["EdLevel"].map(ED_LEVEL_MAP)

    if "OrgSize" in df.columns:
        df["org_size_num"] = df["OrgSize"].map(ORG_SIZE_MAP)

    if "JobSat" in df.columns:
        df["job_sat_score"] = df["JobSat"].map(JOB_SAT_MAP)

    # 2. Salary cleaning
    df = clean_salary(df)

    # 3. Target engineering (before dropping raw columns)
    df = engineer_targets(df)

    # 4. Explode multi-select columns
    if explode_multiselect:
        for col in MULTI_SELECT_COLUMNS:
            if col in df.columns:
                df = explode_multi_select(df, col)

    # 5. Missing-value handling
    df = handle_missing(df)

    logger.info("Cleaning complete — %d rows, %d cols", len(df), len(df.columns))
    return df


def run_cleaning(
    raw_dir: Path | None = None,
    output_dir: Path | None = None,
) -> list[Path]:
    """Execute the cleaning pipeline on all CSVs in *raw_dir*.

    Parameters
    ----------
    raw_dir:
        Directory with raw CSVs. Defaults to ``data/raw/``.
    output_dir:
        Where to write cleaned parquet files. Defaults to ``data/processed/``.

    Returns
    -------
    List of written file paths.
    """
    raw_dir = raw_dir or RAW_DIR
    output_dir = output_dir or PROCESSED_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(raw_dir.glob("*.csv"))
    if not csv_files:
        logger.warning("No CSV files in %s. Run demo_data first.", raw_dir)
        return []

    written: list[Path] = []
    for csv_path in csv_files:
        logger.info("Processing %s", csv_path.name)
        df = pd.read_csv(csv_path, low_memory=False)
        df_clean = clean_survey_data(df)

        stem = csv_path.stem
        out_path = output_dir / f"{stem}_clean.parquet"
        df_clean.to_parquet(out_path, index=False)
        logger.info("Saved %s (%d rows, %d cols)", out_path.name, len(df_clean), len(df_clean.columns))
        written.append(out_path)

    return written


# ── CLI ───────────────────────────────────────────────────────────────────


def main() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    paths = run_cleaning()
    print(f"\n✅  Cleaned {len(paths)} file(s).")
    for p in paths:
        print(f"   📄 {p}")


if __name__ == "__main__":
    main()
