"""Run the complete data, analysis, chart, and Power BI export pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from src.clean import (
    NZ_REGIONS,
    clean_m10,
    clean_ocr_decisions,
    clean_regional_consents,
    expand_ocr_monthly,
)
from src.features import build_date_dimension, build_national_quarterly
from src.models import build_ocr_event_study, run_lagged_ols


PROJECT_ROOT = Path(__file__).resolve().parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
REFERENCE_DIR = PROJECT_ROOT / "data" / "reference"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
POWERBI_DIR = PROCESSED_DIR / "powerbi"
CHART_DIR = PROJECT_ROOT / "outputs" / "charts"


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    """Write a stable UTF-8 CSV with ISO-formatted dates."""
    export = frame.copy()
    for column in export.select_dtypes(include=["datetime64[ns]"]).columns:
        export.loc[:, column] = export[column].dt.strftime("%Y-%m-%d")
    export.to_csv(path, index=False, encoding="utf-8-sig")


def _export_charts(
    quarterly: pd.DataFrame, regional_consents: pd.DataFrame
) -> None:
    """Export two presentation-ready charts from verified source data."""
    import matplotlib.pyplot as plt
    import seaborn as sns

    sns.set_theme(style="whitegrid")
    analysis = quarterly.loc[quarterly["date"].dt.year >= 2015].copy()

    figure, hpi_axis = plt.subplots(figsize=(12, 6))
    hpi_axis.plot(
        analysis["date"], analysis["house_price_index"], color="#0B5CAD", linewidth=2.3
    )
    hpi_axis.set_ylabel("House price index", color="#0B5CAD")
    hpi_axis.set_xlabel("")
    ocr_axis = hpi_axis.twinx()
    ocr_axis.step(
        analysis["date"], analysis["ocr_rate_pct"], where="post", color="#E06B38"
    )
    ocr_axis.set_ylabel("OCR (%)", color="#E06B38")
    hpi_axis.set_title("NZ house price index and OCR (national, quarterly)", loc="left")
    figure.tight_layout()
    figure.savefig(CHART_DIR / "national_hpi_ocr.png", dpi=180, bbox_inches="tight")
    plt.close(figure)

    latest_date = regional_consents["date"].max()
    latest = regional_consents.loc[regional_consents["date"].eq(latest_date)].sort_values(
        "consents_per_1000_residents"
    )
    figure, axis = plt.subplots(figsize=(10, 7))
    axis.barh(latest["region"], latest["consents_per_1000_residents"], color="#2A9D8F")
    axis.set_xlabel("New dwellings consented per 1,000 residents")
    axis.set_ylabel("")
    axis.set_title(f"Regional dwelling-consent intensity ({latest_date.year})", loc="left")
    figure.tight_layout()
    figure.savefig(CHART_DIR / "regional_consents_per_1000.png", dpi=180, bbox_inches="tight")
    plt.close(figure)


def run_pipeline(
    start_year: int = 2010, export_charts: bool = True
) -> dict[str, int | float | str | None]:
    """Build cleaned tables, statistical outputs, charts, and Power BI imports."""
    m10_path = RAW_DIR / "hm10.xlsx"
    if not m10_path.exists():
        raise FileNotFoundError(
            "Missing data/raw/hm10.xlsx. Download Housing - M10 (1990-current) "
            "from https://www.rbnz.govt.nz/statistics/series/economic-indicators/housing"
        )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    POWERBI_DIR.mkdir(parents=True, exist_ok=True)
    CHART_DIR.mkdir(parents=True, exist_ok=True)

    housing = clean_m10(m10_path)
    housing = housing.loc[housing["date"].dt.year >= start_year].reset_index(drop=True)
    decisions = clean_ocr_decisions(REFERENCE_DIR / "ocr_decisions.csv")
    ocr_monthly = expand_ocr_monthly(
        decisions, f"{start_year}-01-01", housing["date"].max().strftime("%Y-%m-%d")
    )
    consents = clean_regional_consents(
        REFERENCE_DIR / "regional_consents_annual.csv"
    )
    quarterly = build_national_quarterly(housing, ocr_monthly)
    regressions = run_lagged_ols(quarterly, start_year=start_year)
    events = build_ocr_event_study(quarterly)
    dates = build_date_dimension(
        f"{start_year}-01-01", max(housing["date"].max(), consents["date"].max()).strftime("%Y-%m-%d")
    )
    regions = pd.DataFrame(
        {
            "region_key": range(1, len(NZ_REGIONS) + 1),
            "region": NZ_REGIONS,
            "country": "New Zealand",
        }
    )

    _write_csv(housing, PROCESSED_DIR / "rbnz_m10_housing_cleaned.csv")
    _write_csv(ocr_monthly, PROCESSED_DIR / "rbnz_ocr_history_cleaned.csv")
    _write_csv(consents, PROCESSED_DIR / "stats_regional_consents_cleaned.csv")
    _write_csv(quarterly, POWERBI_DIR / "fact_national_quarterly.csv")
    _write_csv(ocr_monthly, POWERBI_DIR / "fact_ocr_monthly.csv")
    _write_csv(consents, POWERBI_DIR / "fact_regional_consents_annual.csv")
    _write_csv(dates, POWERBI_DIR / "dim_date.csv")
    _write_csv(regions, POWERBI_DIR / "dim_region.csv")
    _write_csv(regressions, POWERBI_DIR / "analysis_lagged_ols.csv")
    _write_csv(events, POWERBI_DIR / "analysis_ocr_events.csv")

    metadata = pd.DataFrame(
        [
            ["fact_national_quarterly", "quarterly", "New Zealand", "RBNZ M10", "National only; not regional median prices"],
            ["fact_ocr_monthly", "monthly", "New Zealand", "RBNZ OCR decisions", "Month-end policy rate expanded from decision dates"],
            ["fact_regional_consents_annual", "annual", "16 regions", "Stats NZ", "Consents lead completed construction; annual release table"],
        ],
        columns=["table_name", "grain", "geography", "source", "limitation"],
    )
    _write_csv(metadata, POWERBI_DIR / "model_metadata.csv")
    if export_charts:
        _export_charts(quarterly, consents)

    latest = quarterly.dropna(subset=["house_price_index"]).iloc[-1]
    summary: dict[str, int | float | str | None] = {
        "latest_housing_date": latest["date"].strftime("%Y-%m-%d"),
        "latest_hpi": float(latest["house_price_index"]),
        "latest_hpi_yoy_pct": None
        if pd.isna(latest["hpi_yoy_pct"])
        else round(float(latest["hpi_yoy_pct"]), 2),
        "latest_ocr_pct": None
        if pd.isna(latest["ocr_rate_pct"])
        else float(latest["ocr_rate_pct"]),
        "quarterly_rows": len(quarterly),
        "regional_consent_rows": len(consents),
        "regression_models": len(regressions),
    }
    (POWERBI_DIR / "pipeline_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return summary


def main() -> None:
    """Parse CLI options and execute the end-to-end pipeline."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-year", type=int, default=2010)
    parser.add_argument(
        "--skip-charts", action="store_true", help="Skip PNG export in minimal runtimes."
    )
    args = parser.parse_args()
    summary = run_pipeline(start_year=args.start_year, export_charts=not args.skip_charts)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
