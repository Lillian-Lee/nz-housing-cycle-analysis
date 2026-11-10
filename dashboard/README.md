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
- The supply page compares building consents. The regional HPI extension supports a separate price growth comparison.
- Consents are approvals, not completions. Regional migration is not included because no
  validated region-level series is present in the repository.
- Lagged OLS and event summaries show association, not causal OCR effects.

Refresh by running `python run_pipeline.py`, then choose **Refresh** in Power BI.

## Regional HPI extension

Download the [MCERT Property and Sales Statistics workbook](https://www.hud.govt.nz/stats-and-insights/property-and-sales-statistics/about-the-dashboard) to `data/raw/nz-mcert-hpi.xlsx`, then run `python run_regional_analysis.py`. Import `fact_regional_hpi_monthly.csv` and relate it to the date and region dimensions by `date` and `region`, respectively. Use a regional HPI growth trend and a December 2024 to December 2025 bar chart from `analysis_regional_hpi_2025.csv`. Show unranked regions separately and label this as a year-end change, not a peak-to-trough recovery measure. The regional HPI uses a different source and series from M10. Use separate visuals or compare percentage changes with the sources clearly identified.
