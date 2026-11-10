# Analysis pipeline

The national and regional pipelines read local source files and export tables for reporting.

| Entry point | Inputs | Outputs |
|---|---|---|
| [National pipeline](../run_pipeline.py) | RBNZ M10, curated OCR decisions and Stats NZ regional consents | Quarterly housing facts, monthly OCR, annual consents, lag estimates, event summaries and charts |
| [Regional pipeline](../run_regional_analysis.py) | MCERT monthly regional HPI workbook | Regional monthly HPI and matched December 2024 to December 2025 comparisons |

The date dimension links facts at their native reporting frequency. The region dimension filters regional consents and regional HPI. See the [Power BI setup](../dashboard/README.md) for relationships and chart design.
