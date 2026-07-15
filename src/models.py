"""Econometric models for descriptive housing-cycle inference."""

from math import erfc, sqrt

import numpy as np
import pandas as pd

try:
    import statsmodels.api as sm
except ModuleNotFoundError:  # pragma: no cover - used only in constrained runtimes
    sm = None


def _numpy_hac_fit(
    sample: pd.DataFrame, predictor: str
) -> dict[str, float | int | str]:
    """Fit OLS with a Newey-West covariance fallback when statsmodels is unavailable."""
    response = sample["hpi_yoy_pct"].to_numpy(dtype=float)
    design = np.column_stack(
        [np.ones(len(sample)), sample[predictor], sample["time_trend"]]
    ).astype(float)
    inverse_xx = np.linalg.inv(design.T @ design)
    coefficients = inverse_xx @ design.T @ response
    residuals = response - design @ coefficients
    meat = np.zeros((design.shape[1], design.shape[1]))
    for row in range(len(sample)):
        vector = design[row][:, None]
        meat += residuals[row] ** 2 * (vector @ vector.T)
    max_lags = min(4, len(sample) - 1)
    for lag in range(1, max_lags + 1):
        weight = 1 - lag / (max_lags + 1)
        for row in range(lag, len(sample)):
            current = design[row][:, None]
            prior = design[row - lag][:, None]
            cross = residuals[row] * residuals[row - lag] * (current @ prior.T)
            meat += weight * (cross + cross.T)
    covariance = inverse_xx @ meat @ inverse_xx
    standard_error = float(np.sqrt(max(covariance[1, 1], 0)))
    coefficient = float(coefficients[1])
    statistic = coefficient / standard_error if standard_error else np.nan
    p_value = erfc(abs(statistic) / sqrt(2)) if np.isfinite(statistic) else np.nan
    total_ss = float(((response - response.mean()) ** 2).sum())
    residual_ss = float((residuals**2).sum())
    return {
        "ocr_coefficient": coefficient,
        "standard_error": standard_error,
        "p_value": p_value,
        "ci_95_low": coefficient - 1.96 * standard_error,
        "ci_95_high": coefficient + 1.96 * standard_error,
        "r_squared": 1 - residual_ss / total_ss,
        "observations": len(sample),
        "estimator": "numpy OLS + Newey-West fallback",
    }


def run_lagged_ols(
    quarterly: pd.DataFrame, start_year: int = 2010
) -> pd.DataFrame:
    """Estimate separate HAC-robust HPI-growth models for OCR lags of 1–4 quarters."""
    results: list[dict[str, float | int | str]] = []
    analysis = quarterly.loc[quarterly["date"].dt.year >= start_year].copy()
    for lag_quarters in (1, 2, 3, 4):
        predictor = f"ocr_lag_{lag_quarters}q"
        sample = analysis.loc[:, ["hpi_yoy_pct", predictor, "time_trend"]].dropna()
        if len(sample) < 12:
            continue
        if sm is None:
            estimates = _numpy_hac_fit(sample, predictor)
        else:
            design = sm.add_constant(sample.loc[:, [predictor, "time_trend"]])
            model = sm.OLS(sample["hpi_yoy_pct"], design).fit(
                cov_type="HAC", cov_kwds={"maxlags": 4}
            )
            confidence = model.conf_int().loc[predictor]
            estimates = {
                "ocr_coefficient": model.params[predictor],
                "standard_error": model.bse[predictor],
                "p_value": model.pvalues[predictor],
                "ci_95_low": confidence.iloc[0],
                "ci_95_high": confidence.iloc[1],
                "r_squared": model.rsquared,
                "observations": int(model.nobs),
                "estimator": "statsmodels OLS + HAC(4)",
            }
        results.append(
            {
                "lag_quarters": lag_quarters,
                "lag_months_approx": lag_quarters * 3,
                **estimates,
                "interpretation_unit": "HPI YoY percentage points per 1pp OCR",
            }
        )
    return pd.DataFrame(results)


def build_ocr_event_study(quarterly: pd.DataFrame) -> pd.DataFrame:
    """Summarise subsequent HPI changes around quarters with an OCR change."""
    events = quarterly.loc[quarterly["ocr_change_pp"].fillna(0).ne(0)].copy()
    events.loc[:, "event_direction"] = events["ocr_change_pp"].map(
        lambda value: "Tightening" if value > 0 else "Easing"
    )
    columns = ["date", "ocr_rate_pct", "ocr_change_pp", "event_direction"]
    columns.extend(f"hpi_forward_{lag}q_pct" for lag in (1, 2, 3, 4))
    return events.loc[:, columns].reset_index(drop=True)
