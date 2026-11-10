"""Validate the MCERT regional HPI and export comparable year-end changes."""

from pathlib import Path

import pandas as pd

from src.clean import NZ_REGIONS

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "data/raw/nz-mcert-hpi.xlsx"
OUTPUT = ROOT / "data/processed/powerbi"
MONTHS = pd.date_range("2010-01-01", "2025-12-01", freq="MS")


def load_regional_hpi(path: Path) -> pd.DataFrame:
    """Read monthly, all-value regional observations onto a complete calendar."""
    columns = ["stat_type", "area_type", "area", "period", "value_quartile",
               "residential_sales_used_for_HPI", "house_price_index"]
    raw = pd.read_excel(path, sheet_name="House Price Index", usecols=columns)
    selected = raw.loc[
        raw["stat_type"].eq("Monthly") & raw["area_type"].eq("Region")
        & raw["value_quartile"].eq("All")
    ].copy()
    selected["region"] = selected["area"].replace(
        {"Manawatu-Wanganui": "Manawatū-Whanganui"}
    )
    if set(selected["region"]) != set(NZ_REGIONS):
        raise ValueError("Source regions do not match the project's 16 regions.")
    selected["date"] = pd.to_datetime(selected["period"], errors="raise")
    if selected["date"].isna().any() or not selected["date"].dt.is_month_start.all():
        raise ValueError("Regional HPI periods must be month-start dates.")
    selected = selected.loc[selected["date"].isin(MONTHS)]
    measures = ["house_price_index", "residential_sales_used_for_HPI"]
    for column in measures:
        selected[column] = pd.to_numeric(selected[column], errors="raise")
    if selected["house_price_index"].dropna().le(0).any():
        raise ValueError("HPI values must be positive.")
    grid = pd.MultiIndex.from_product([NZ_REGIONS, MONTHS], names=["region", "date"])
    panel = selected.set_index(["region", "date"])[measures]
    if not panel.index.is_unique:
        raise ValueError("Duplicate region-month observations in the source.")
    panel = panel.reindex(grid).reset_index()
    prior = panel.groupby("region")["house_price_index"].shift(12)
    panel["hpi_yoy_pct"] = (panel["house_price_index"] / prior - 1) * 100
    return panel


def year_end_comparison(panel: pd.DataFrame) -> pd.DataFrame:
    """Compare identical calendar months and leave unavailable ranks blank."""
    hpi = panel.pivot(index="region", columns="date", values="house_price_index")
    result = hpi.loc[:, ["2024-12-01", "2025-12-01"]].copy()
    result.columns = ["hpi_dec_2024", "hpi_dec_2025"]
    result["hpi_change_pct"] = (result["hpi_dec_2025"] / result["hpi_dec_2024"] - 1) * 100
    result["rank"] = result["hpi_change_pct"].rank(ascending=False, method="min").astype("Int64")
    result["status"] = result["hpi_change_pct"].notna().map(
        {True: "Comparable", False: "Missing endpoint"}
    )
    return result.sort_values("rank").reset_index()


def main() -> None:
    """Export the regional HPI fact and the comparison audit table."""
    panel = load_regional_hpi(SOURCE)
    comparison = year_end_comparison(panel)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    panel.to_csv(OUTPUT / "fact_regional_hpi_monthly.csv", index=False, encoding="utf-8-sig")
    comparison.to_csv(OUTPUT / "analysis_regional_hpi_2025.csv", index=False, encoding="utf-8-sig")
    print(f"Comparable regions: {comparison['rank'].count()}/{len(comparison)}")
    print(f"Available index values: {panel['house_price_index'].count()}/{len(panel)}")


if __name__ == "__main__":
    main()
