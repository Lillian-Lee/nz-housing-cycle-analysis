# Power BI dashboard handoff

This repository produces a Power BI-ready star model under `data/processed/powerbi/`.
Power BI Desktop must be used to create the final `.pbix`; Microsoft does not provide a
supported cross-platform text format for generating a `.pbix` directly in this repository.

## Load and relate the tables

Use **Get data > Text/CSV** and load every CSV in `data/processed/powerbi/`.
Set all `date` fields to Date. Create these one-to-many, single-direction relationships:

| One side | Many side | Key |
|---|---|---|
| `dim_date` | `fact_national_quarterly` | `date` |
| `dim_date` | `fact_ocr_monthly` | `date` |
| `dim_date` | `fact_regional_consents_annual` | `date` |
| `dim_region` | `fact_regional_consents_annual` | `region` |

Mark `dim_date` as the date table. Import `powerbi_theme.json`, then create the measures
in `measures.dax`.

## Recommended pages

1. **Executive overview** — latest HPI, HPI YoY, OCR, sales, and HPI/OCR time series.
2. **Policy transmission** — lag coefficients with 95% intervals and OCR event table.
3. **Regional supply** — consents per 1,000 ranking, annual trend, and region/year slicers.
4. **Data quality** — grains, latest dates, row counts, limitations, and source URLs.

## Scope boundary

- M10 is national and quarterly, not 16-region monthly median prices.
- The regional page compares building consents only; it cannot claim regional price recovery.
- Consents are approvals, not completions. Regional migration is not included because no
  validated region-level series is present in the repository.
- Lagged OLS and event summaries show association, not causal OCR effects.

Refresh by running `python run_pipeline.py`, then choose **Refresh** in Power BI.
