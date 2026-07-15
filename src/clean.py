"""Cleaning utilities for official RBNZ and Stats NZ source data."""

from pathlib import Path

import pandas as pd


NZ_REGIONS = (
    "Northland",
    "Auckland",
    "Waikato",
    "Bay of Plenty",
    "Gisborne",
    "Hawke's Bay",
    "Taranaki",
    "Manawatū-Whanganui",
    "Wellington",
    "Tasman",
    "Nelson",
    "Marlborough",
    "West Coast",
    "Canterbury",
    "Otago",
    "Southland",
)


def _parse_excel_dates(values: pd.Series) -> pd.Series:
    """Parse a column containing Excel serial dates or date-like values."""
    numeric_values = pd.to_numeric(values, errors="coerce")
    parsed_numeric = pd.to_datetime(
        numeric_values, unit="D", origin="1899-12-30", errors="coerce"
    )
    parsed_text = pd.to_datetime(values, errors="coerce")
    return parsed_numeric.fillna(parsed_text)


def clean_m10(path: Path) -> pd.DataFrame:
    """Read the national quarterly RBNZ M10 workbook into a tidy table."""
    raw = pd.read_excel(path, sheet_name="Data", header=None, engine="openpyxl")
    if raw.shape[1] < 5:
        raise ValueError(f"M10 workbook has {raw.shape[1]} columns; expected at least 5.")

    cleaned = raw.iloc[5:, :5].copy()
    cleaned.columns = [
        "date",
        "house_sales_count",
        "house_price_index",
        "housing_stock_value_nzd_m",
        "residential_investment_real_nzd_m",
    ]
    cleaned["date"] = _parse_excel_dates(cleaned["date"])
    numeric_columns = cleaned.columns.drop("date")
    for column in numeric_columns:
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce").astype(float)

    cleaned = cleaned.dropna(subset=["date"]).sort_values("date")
    cleaned["date"] = pd.to_datetime(cleaned["date"])
    cleaned.loc[:, "geography"] = "New Zealand"
    return cleaned.reset_index(drop=True)


def clean_ocr_decisions(path: Path) -> pd.DataFrame:
    """Read curated official OCR decision dates and validate their values."""
    decisions = pd.read_csv(path, parse_dates=["decision_date"])
    required = {"decision_date", "ocr_rate_pct", "source_url"}
    missing = required.difference(decisions.columns)
    if missing:
        raise ValueError(f"OCR decisions file is missing columns: {sorted(missing)}")

    decisions.loc[:, "ocr_rate_pct"] = pd.to_numeric(
        decisions["ocr_rate_pct"], errors="raise"
    )
    return decisions.sort_values("decision_date").drop_duplicates(
        "decision_date", keep="last"
    )


def expand_ocr_monthly(
    decisions: pd.DataFrame, start_date: str, end_date: str
) -> pd.DataFrame:
    """Expand decision-date OCR values to a month-start step series."""
    month_starts = pd.date_range(start=start_date, end=end_date, freq="MS")
    month_ends = month_starts + pd.offsets.MonthEnd(0)
    monthly = pd.DataFrame({"date": month_starts, "month_end": month_ends})
    decision_values = decisions.loc[:, ["decision_date", "ocr_rate_pct"]].copy()
    monthly = pd.merge_asof(
        monthly.sort_values("month_end"),
        decision_values.sort_values("decision_date"),
        left_on="month_end",
        right_on="decision_date",
        direction="backward",
    )
    monthly.loc[:, "ocr_change_pp"] = monthly["ocr_rate_pct"].diff()
    return monthly.drop(columns=["month_end", "decision_date"])


def clean_regional_consents(path: Path) -> pd.DataFrame:
    """Read annual regional dwelling-consent facts and validate 16 regions."""
    consents = pd.read_csv(path, parse_dates=["date"])
    required = {
        "date",
        "region",
        "new_dwellings_consented",
        "consents_per_1000_residents",
        "source_url",
    }
    missing = required.difference(consents.columns)
    if missing:
        raise ValueError(f"Regional consents file is missing columns: {sorted(missing)}")

    unknown = set(consents["region"]).difference(NZ_REGIONS)
    if unknown:
        raise ValueError(f"Unknown region labels: {sorted(unknown)}")
    return consents.sort_values(["date", "region"]).reset_index(drop=True)
