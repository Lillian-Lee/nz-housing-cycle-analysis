"""Regression tests for the repository's verified local source data."""

from pathlib import Path
import unittest

from src.clean import (
    NZ_REGIONS,
    clean_m10,
    clean_ocr_decisions,
    clean_regional_consents,
    expand_ocr_monthly,
)
from src.features import build_national_quarterly
from src.models import run_lagged_ols


ROOT = Path(__file__).resolve().parents[1]


class PipelineTest(unittest.TestCase):
    """Check schema, grain, and model-output invariants."""

    def test_verified_pipeline_inputs(self) -> None:
        """Validate official input parsing and expected geographic coverage."""
        housing = clean_m10(ROOT / "data/raw/hm10.xlsx")
        consents = clean_regional_consents(
            ROOT / "data/reference/regional_consents_annual.csv"
        )
        self.assertTrue(housing["date"].is_monotonic_increasing)
        self.assertEqual(set(consents["region"]), set(NZ_REGIONS))
        self.assertTrue((consents.groupby("date").size() == 16).all())

    def test_feature_and_model_outputs(self) -> None:
        """Confirm quarterly alignment and four pre-specified lag models."""
        housing = clean_m10(ROOT / "data/raw/hm10.xlsx")
        housing = housing.loc[housing["date"].dt.year >= 2010].copy()
        decisions = clean_ocr_decisions(ROOT / "data/reference/ocr_decisions.csv")
        ocr = expand_ocr_monthly(
            decisions, "2010-01-01", housing["date"].max().strftime("%Y-%m-%d")
        )
        quarterly = build_national_quarterly(housing, ocr)
        results = run_lagged_ols(quarterly)
        self.assertEqual(len(results), 4)
        self.assertEqual(set(results["lag_quarters"]), {1, 2, 3, 4})
        self.assertFalse(quarterly["house_price_index"].isna().all())


if __name__ == "__main__":
    unittest.main()
