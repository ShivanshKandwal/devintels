"""
Merge Longitudinal Surveys.

Merge 2022-2024 Stack Overflow survey data into a single longitudinal
DataFrame with a ``survey_year`` column.

Usage:
    python -m src.data.merge_longitudinal
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def _extract_year_from_filename(filename: str) -> int | None:
    """Try to extract a 4-digit year from a filename."""
    import re

    match = re.search(r"(20\d{2})", filename)
    return int(match.group(1)) if match else None


def merge_surveys(
    raw_dir: Path | None = None,
    output_dir: Path | None = None,
    output_filename: str = "longitudinal_merged.parquet",
) -> Path:
    """Load all CSVs, tag with survey_year, and merge.

    The merge uses an outer join on the union of all columns so that
    year-specific columns are retained (with NaN where absent).

    Parameters
    ----------
    raw_dir:
        Directory containing raw CSVs.
    output_dir:
        Where to write the merged file.
    output_filename:
        Name of the output file.

    Returns
    -------
    Path to the merged file.
    """
    raw_dir = raw_dir or RAW_DIR
    output_dir = output_dir or PROCESSED_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(raw_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found in {raw_dir}. "
            "Run `python -m src.data.demo_data` to generate synthetic data."
        )

    frames: list[pd.DataFrame] = []
    for csv_path in csv_files:
        logger.info("Loading %s", csv_path.name)
        df = pd.read_csv(csv_path, low_memory=False)

        # Ensure survey_year column exists
        if "survey_year" not in df.columns:
            year = _extract_year_from_filename(csv_path.name)
            if year is None:
                year = 2024  # fallback
                logger.warning(
                    "Could not extract year from %s — defaulting to %d",
                    csv_path.name,
                    year,
                )
            df["survey_year"] = year

        frames.append(df)

    merged = pd.concat(frames, axis=0, ignore_index=True, sort=False)

    # Deduplicate if the same ResponseId appears in multiple files
    # (shouldn't happen with real data, but guard against demo re-runs)
    if "ResponseId" in merged.columns:
        before = len(merged)
        merged = merged.drop_duplicates(subset=["ResponseId", "survey_year"], keep="first")
        dropped = before - len(merged)
        if dropped:
            logger.info("Dropped %d duplicate rows by (ResponseId, survey_year)", dropped)

    # Summary
    year_counts = merged["survey_year"].value_counts().sort_index()
    logger.info(
        "Merged %d total rows across %d years: %s",
        len(merged),
        len(year_counts),
        year_counts.to_dict(),
    )

    # Identify columns not present in every year
    per_year_cols: dict[int, set[str]] = {}
    for year, group in merged.groupby("survey_year"):
        non_null_cols = set(group.columns[group.notna().any()])
        per_year_cols[int(year)] = non_null_cols

    all_years_cols = set.intersection(*per_year_cols.values()) if per_year_cols else set()
    some_years_cols = set.union(*per_year_cols.values()) - all_years_cols if per_year_cols else set()
    if some_years_cols:
        logger.info(
            "%d columns appear in only some years: %s",
            len(some_years_cols),
            sorted(some_years_cols)[:10],
        )

    output_path = output_dir / output_filename
    merged.to_parquet(output_path, index=False)
    logger.info("Saved merged dataset to %s", output_path)

    return output_path


# ── CLI ───────────────────────────────────────────────────────────────────


def main() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    try:
        path = merge_surveys()
        print(f"\n✅  Longitudinal merge complete → {path}")
    except FileNotFoundError as exc:
        print(f"\n❌  {exc}")


if __name__ == "__main__":
    main()
