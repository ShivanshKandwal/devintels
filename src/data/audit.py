"""
Data Audit Module — Inspects raw CSV data and produces a markdown audit report.

Run directly:
    python -m src.data.audit

The report is written to ``data_audit_report.md`` in the project root.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
REPORT_PATH = PROJECT_ROOT / "data_audit_report.md"
SEMICOLON_THRESHOLD = 0.10  # fraction of non-null values containing ";"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _detect_multi_select(series: pd.Series, threshold: float = SEMICOLON_THRESHOLD) -> bool:
    """Return True if a string column likely contains semicolon-separated lists."""
    if series.dtype != object:
        return False
    non_null = series.dropna()
    if len(non_null) == 0:
        return False
    frac_with_semi = non_null.astype(str).str.contains(";", regex=False).mean()
    return bool(frac_with_semi >= threshold)


def _dtype_summary(series: pd.Series) -> str:
    """Produce a human-readable dtype string."""
    if pd.api.types.is_integer_dtype(series):
        return "integer"
    if pd.api.types.is_float_dtype(series):
        return "float"
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    return "string/object"


def _top_values(series: pd.Series, n: int = 5) -> str:
    """Return a compact string of the top-N most frequent values."""
    counts = series.dropna().value_counts().head(n)
    parts = [f"`{v}` ({c})" for v, c in counts.items()]
    return ", ".join(parts) if parts else "—"


# ---------------------------------------------------------------------------
# Audit a single file
# ---------------------------------------------------------------------------


def audit_file(filepath: Path) -> dict[str, Any]:
    """Audit a single CSV file and return a dict of metrics.

    Parameters
    ----------
    filepath:
        Absolute path to a CSV file.

    Returns
    -------
    dict with keys: filename, rows, cols, columns (list of per-column dicts),
    multi_select_cols, dtypes_summary.
    """
    logger.info("Auditing %s", filepath.name)
    df = pd.read_csv(filepath, low_memory=False)

    col_details: list[dict[str, Any]] = []
    multi_select_cols: list[str] = []

    for col in df.columns:
        null_pct = round(df[col].isna().mean() * 100, 2)
        unique_count = int(df[col].nunique())
        is_multi = _detect_multi_select(df[col])
        if is_multi:
            multi_select_cols.append(col)

        col_details.append(
            {
                "column": col,
                "dtype": _dtype_summary(df[col]),
                "null_pct": null_pct,
                "unique": unique_count,
                "multi_select": is_multi,
                "top_values": _top_values(df[col]),
            }
        )

    dtypes_summary = df.dtypes.apply(_dtype_summary).value_counts().to_dict()

    return {
        "filename": filepath.name,
        "rows": len(df),
        "cols": len(df.columns),
        "columns": col_details,
        "multi_select_cols": multi_select_cols,
        "dtypes_summary": dtypes_summary,
        "column_names": list(df.columns),
    }


# ---------------------------------------------------------------------------
# Cross-year comparison
# ---------------------------------------------------------------------------


def find_common_columns(audits: list[dict[str, Any]]) -> list[str]:
    """Find columns that appear in every audited file."""
    if not audits:
        return []
    sets = [set(a["column_names"]) for a in audits]
    common = sets[0]
    for s in sets[1:]:
        common &= s
    return sorted(common)


def find_all_columns(audits: list[dict[str, Any]]) -> list[str]:
    """Union of all column names across files."""
    if not audits:
        return []
    all_cols: set[str] = set()
    for a in audits:
        all_cols.update(a["column_names"])
    return sorted(all_cols)


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


def _render_file_section(audit: dict[str, Any]) -> str:
    """Render a markdown section for a single file audit."""
    lines: list[str] = []
    lines.append(f"## {audit['filename']}\n")
    lines.append(f"- **Rows:** {audit['rows']:,}")
    lines.append(f"- **Columns:** {audit['cols']}")
    lines.append(f"- **Dtype breakdown:** {audit['dtypes_summary']}")
    lines.append(
        f"- **Multi-select columns ({len(audit['multi_select_cols'])}):** "
        + (", ".join(f"`{c}`" for c in audit["multi_select_cols"]) or "None detected")
    )
    lines.append("")

    # Column detail table
    lines.append("| Column | Type | Null % | Unique | Multi-select | Top Values |")
    lines.append("|--------|------|--------|--------|--------------|------------|")
    for c in audit["columns"]:
        ms = "✓" if c["multi_select"] else ""
        lines.append(
            f"| `{c['column']}` | {c['dtype']} | {c['null_pct']}% "
            f"| {c['unique']} | {ms} | {c['top_values']} |"
        )
    lines.append("")
    return "\n".join(lines)


def generate_report(audits: list[dict[str, Any]], output_path: Path) -> None:
    """Write a full markdown audit report.

    Parameters
    ----------
    audits:
        List of audit dicts (one per file).
    output_path:
        Where to write the report.
    """
    lines: list[str] = []
    lines.append("# DevIntel — Data Audit Report\n")
    lines.append(f"*Generated by `src.data.audit` — {pd.Timestamp.now():%Y-%m-%d %H:%M:%S}*\n")

    # Summary
    lines.append("## Summary\n")
    lines.append(f"- **Files audited:** {len(audits)}")
    total_rows = sum(a["rows"] for a in audits)
    lines.append(f"- **Total rows (all files):** {total_rows:,}")

    common = find_common_columns(audits)
    lines.append(f"- **Columns common to all files ({len(common)}):** "
                 + (", ".join(f"`{c}`" for c in common[:30]) or "N/A"))
    if len(common) > 30:
        lines.append(f"  - *…and {len(common) - 30} more*")

    all_cols = find_all_columns(audits)
    only_some = sorted(set(all_cols) - set(common))
    lines.append(f"- **Columns NOT in every file ({len(only_some)}):** "
                 + (", ".join(f"`{c}`" for c in only_some[:20]) or "None"))
    lines.append("")

    # Per-file sections
    for audit in sorted(audits, key=lambda a: a["filename"]):
        lines.append(_render_file_section(audit))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Audit report written to %s", output_path)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def run_audit(raw_dir: Path | None = None, report_path: Path | None = None) -> list[dict[str, Any]]:
    """Execute the full audit pipeline.

    Parameters
    ----------
    raw_dir:
        Directory containing CSV files. Defaults to ``data/raw/``.
    report_path:
        Output path for the report. Defaults to ``data_audit_report.md``.

    Returns
    -------
    List of per-file audit dicts.
    """
    raw_dir = raw_dir or RAW_DIR
    report_path = report_path or REPORT_PATH

    csv_files = sorted(raw_dir.glob("*.csv"))
    if not csv_files:
        logger.warning("No CSV files found in %s — generating report for zero files.", raw_dir)

    audits = [audit_file(f) for f in csv_files]
    generate_report(audits, report_path)

    print(f"\n✅  Audit complete — {len(audits)} file(s) processed.")
    print(f"📄  Report: {report_path}")
    return audits


def main() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    run_audit()


if __name__ == "__main__":
    main()
