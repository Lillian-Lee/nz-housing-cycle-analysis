"""Feature engineering for the NZ housing-cycle analysis."""

import numpy as np
import pandas as pd


def build_national_quarterly(
    housing: pd.DataFrame, ocr_monthly: pd.DataFrame
) -> pd.DataFrame:
    """Align national quarterly housing metrics with quarter-end OCR values."""
    quarterly_ocr = ocr_monthly.copy()
    quarterly_ocr.loc[:, "quarter"] = quarterly_ocr["date"].dt.to_period("Q")
    quarterly_ocr = quarterly_ocr.groupby("quarter", as_index=False).tail(1)
    quarterly_ocr.loc[:, "date"] = quarterly_ocr["quarter"].dt.to_timestamp("Q")
    quarterly_ocr = quarterly_ocr.loc[:, ["date", "ocr_rate_pct"]]

    featured = housing.merge(quarterly_ocr, on="date", how="left", validate="one_to_one")
    featured.loc[:, "hpi_qoq_pct"] = featured["house_price_index"].pct_change() * 100
    featured.loc[:, "hpi_yoy_pct"] = featured["house_price_index"].pct_change(4) * 100
    featured.loc[:, "sales_yoy_pct"] = featured["house_sales_count"].pct_change(4) * 100
    featured.loc[:, "investment_yoy_pct"] = (
        featured["residential_investment_real_nzd_m"].pct_change(4) * 100
    )
    featured.loc[:, "ocr_change_pp"] = featured["ocr_rate_pct"].diff()
    featured.loc[:, "time_trend"] = np.arange(len(featured), dtype=float)
    for lag_quarters in (1, 2, 3, 4):
        featured.loc[:, f"ocr_lag_{lag_quarters}q"] = featured["ocr_rate_pct"].shift(
            lag_quarters
        )
        featured.loc[:, f"hpi_forward_{lag_quarters}q_pct"] = (
            featured["house_price_index"].shift(-lag_quarters)
            / featured["house_price_index"]
            - 1
        ) * 100
    return featured


def build_date_dimension(start_date: str, end_date: str) -> pd.DataFrame:
    """Create a Power BI date dimension at daily grain."""
    dates = pd.DataFrame({"date": pd.date_range(start_date, end_date, freq="D")})
    dates.loc[:, "year"] = dates["date"].dt.year
    dates.loc[:, "quarter"] = "Q" + dates["date"].dt.quarter.astype(str)
    dates.loc[:, "year_quarter"] = dates["date"].dt.to_period("Q").astype(str)
    dates.loc[:, "month_number"] = dates["date"].dt.month
    dates.loc[:, "month_name"] = dates["date"].dt.strftime("%b")
    dates.loc[:, "year_month"] = dates["date"].dt.strftime("%Y-%m")
    dates.loc[:, "is_quarter_end"] = dates["date"].dt.is_quarter_end
    return dates
