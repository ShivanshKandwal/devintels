"""
Technology Forecast Module.

Computes annual adoption rates from longitudinal data and trains
Prophet, ARIMA, and Linear models to forecast 2025-2026 adoption.

Usage:
    python -m src.models.forecast
"""

from __future__ import annotations

import json
import logging
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RAW_DIR = PROJECT_ROOT / "data" / "raw"
MODELS_DIR = PROJECT_ROOT / "models"

# Technologies to forecast
TECH_COLUMNS: dict[str, str] = {
    "LanguageHaveWorkedWith": "Language",
    "DatabaseHaveWorkedWith": "Database",
    "PlatformHaveWorkedWith": "Platform",
    "AIDevHaveWorkedWith": "AI Dev Tool",
    "AISearchHaveWorkedWith": "AI Search Tool",
}


def compute_adoption_rates(
    raw_dir: Path | None = None,
) -> pd.DataFrame:
    """Compute annual adoption rate for each technology.

    Returns a DataFrame with columns: year, technology, category, adoption_rate.
    """
    raw_dir = raw_dir or RAW_DIR

    csv_files = sorted(raw_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSVs in {raw_dir}")

    records: list[dict[str, Any]] = []

    for csv_path in csv_files:
        df = pd.read_csv(csv_path, low_memory=False)

        # Determine year
        if "survey_year" in df.columns:
            year = int(df["survey_year"].mode().iloc[0])
        else:
            import re
            match = re.search(r"(20\d{2})", csv_path.name)
            year = int(match.group(1)) if match else 2024

        n_total = len(df)

        for col, category in TECH_COLUMNS.items():
            if col not in df.columns:
                continue

            series = df[col].dropna().astype(str)
            tech_counts: dict[str, int] = {}
            for cell in series:
                for tech in cell.split(";"):
                    tech = tech.strip()
                    if tech:
                        tech_counts[tech] = tech_counts.get(tech, 0) + 1

            for tech_name, count in tech_counts.items():
                records.append({
                    "year": year,
                    "technology": tech_name,
                    "category": category,
                    "adoption_rate": round(count / n_total, 4),
                    "user_count": count,
                })

    adoption_df = pd.DataFrame(records)
    logger.info(
        "Computed adoption rates: %d records for %d technologies",
        len(adoption_df),
        adoption_df["technology"].nunique(),
    )
    return adoption_df


def _forecast_linear(years: np.ndarray, rates: np.ndarray, forecast_years: list[int]) -> list[float]:
    """Simple linear regression forecast."""
    model = LinearRegression()
    model.fit(years.reshape(-1, 1), rates)
    preds = model.predict(np.array(forecast_years).reshape(-1, 1))
    return [max(0, min(1, float(p))) for p in preds]


def _forecast_prophet(years: np.ndarray, rates: np.ndarray, forecast_years: list[int]) -> list[float] | None:
    """Prophet forecast. Returns None if Prophet unavailable or fails."""
    try:
        from prophet import Prophet

        prophet_df = pd.DataFrame({
            "ds": pd.to_datetime([f"{int(y)}-06-01" for y in years]),
            "y": rates,
        })

        model = Prophet(
            yearly_seasonality=False,
            weekly_seasonality=False,
            daily_seasonality=False,
            changepoint_prior_scale=0.5,
        )
        model.fit(prophet_df)

        future = pd.DataFrame({
            "ds": pd.to_datetime([f"{y}-06-01" for y in forecast_years]),
        })
        forecast = model.predict(future)
        return [max(0, min(1, float(v))) for v in forecast["yhat"].values]
    except Exception as exc:
        logger.debug("Prophet failed: %s", exc)
        return None


def _forecast_arima(years: np.ndarray, rates: np.ndarray, forecast_years: list[int]) -> list[float] | None:
    """ARIMA forecast using pmdarima auto_arima. Returns None on failure."""
    try:
        import pmdarima as pm

        n_periods = len(forecast_years)
        model = pm.auto_arima(
            rates,
            start_p=0, start_q=0,
            max_p=2, max_q=2,
            seasonal=False,
            suppress_warnings=True,
            error_action="ignore",
        )
        preds = model.predict(n_periods=n_periods)
        return [max(0, min(1, float(p))) for p in preds]
    except Exception as exc:
        logger.debug("ARIMA failed: %s", exc)
        return None


def run_forecasts(
    raw_dir: Path | None = None,
    models_dir: Path | None = None,
    forecast_years: list[int] | None = None,
    min_data_points: int = 2,
) -> dict[str, Any]:
    """Run adoption-rate forecasts for all technologies.

    Parameters
    ----------
    raw_dir:
        Raw CSV directory.
    models_dir:
        Where to save forecast outputs.
    forecast_years:
        Years to forecast (default [2025, 2026]).
    min_data_points:
        Minimum number of years of data required to forecast a technology.

    Returns
    -------
    Dict with forecasts per technology.
    """
    raw_dir = raw_dir or RAW_DIR
    models_dir = models_dir or MODELS_DIR
    models_dir.mkdir(parents=True, exist_ok=True)
    forecast_years = forecast_years or [2025, 2026]

    adoption = compute_adoption_rates(raw_dir)

    all_forecasts: dict[str, Any] = {}

    for tech in adoption["technology"].unique():
        tech_data = adoption[adoption["technology"] == tech].sort_values("year")

        if len(tech_data) < min_data_points:
            continue

        years = tech_data["year"].values.astype(float)
        rates = tech_data["adoption_rate"].values.astype(float)
        category = tech_data["category"].iloc[0]

        tech_result: dict[str, Any] = {
            "category": category,
            "historical": {
                "years": [int(y) for y in years],
                "rates": [round(float(r), 4) for r in rates],
            },
            "forecasts": {},
        }

        # Linear
        linear_preds = _forecast_linear(years, rates, forecast_years)
        tech_result["forecasts"]["linear"] = {
            "years": forecast_years,
            "rates": [round(r, 4) for r in linear_preds],
        }

        # Prophet
        prophet_preds = _forecast_prophet(years, rates, forecast_years)
        if prophet_preds is not None:
            tech_result["forecasts"]["prophet"] = {
                "years": forecast_years,
                "rates": [round(r, 4) for r in prophet_preds],
            }

        # ARIMA
        arima_preds = _forecast_arima(years, rates, forecast_years)
        if arima_preds is not None:
            tech_result["forecasts"]["arima"] = {
                "years": forecast_years,
                "rates": [round(r, 4) for r in arima_preds],
            }

        # Ensemble (average of available models)
        all_preds = [linear_preds]
        if prophet_preds:
            all_preds.append(prophet_preds)
        if arima_preds:
            all_preds.append(arima_preds)

        ensemble = np.mean(all_preds, axis=0).tolist()
        tech_result["forecasts"]["ensemble"] = {
            "years": forecast_years,
            "rates": [round(r, 4) for r in ensemble],
        }

        # Trend direction
        if len(rates) >= 2:
            trend = "growing" if rates[-1] > rates[0] else ("declining" if rates[-1] < rates[0] else "stable")
        else:
            trend = "unknown"
        tech_result["trend"] = trend

        all_forecasts[tech] = tech_result

    # Save
    output_path = models_dir / "forecasts.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_forecasts, f, indent=2)
    logger.info("Saved forecasts for %d technologies to %s", len(all_forecasts), output_path)

    return all_forecasts


def get_tech_forecast(
    tech: str,
    models_dir: Path | None = None,
) -> dict[str, Any] | None:
    """Retrieve forecast for a specific technology.

    Parameters
    ----------
    tech:
        Technology name (e.g. "Python", "PostgreSQL").
    models_dir:
        Where the forecasts file is saved.

    Returns
    -------
    Forecast dict or None if not found.
    """
    models_dir = models_dir or MODELS_DIR
    forecast_path = models_dir / "forecasts.json"

    if not forecast_path.exists():
        return None

    with open(forecast_path) as f:
        forecasts = json.load(f)

    # Try exact match first, then case-insensitive
    if tech in forecasts:
        return forecasts[tech]

    tech_lower = tech.lower()
    for key, value in forecasts.items():
        if key.lower() == tech_lower:
            return value

    return None


# ── CLI ───────────────────────────────────────────────────────────────────


def main() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    try:
        forecasts = run_forecasts()
        print(f"\n✅  Forecasted {len(forecasts)} technologies.")
        # Show top growing
        growing = [(k, v) for k, v in forecasts.items() if v.get("trend") == "growing"]
        if growing:
            print("\n📈 Top Growing Technologies:")
            for name, data in sorted(growing, key=lambda x: x[1]["historical"]["rates"][-1], reverse=True)[:10]:
                latest = data["historical"]["rates"][-1]
                print(f"   {name}: {latest:.1%}")
    except FileNotFoundError as exc:
        print(f"\n❌  {exc}")


if __name__ == "__main__":
    main()
