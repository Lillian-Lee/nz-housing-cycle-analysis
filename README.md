# NZ Housing Market Cycle Analysis

> **An executive analytics project** – understanding how OCR, supply, and migration shape regional house prices (2015–2025)

---

## Business Context

| Stakeholder | Core Question This Analysis Answers |
|-------------|--------------------------------------|
| **Policymakers** (RBNZ, Treasury) | How long does OCR policy take to affect regional house prices? Is the transmission lag uniform across NZ? |
| **Banks** (ANZ, ASB, Westpac) | Which regions show the highest price sensitivity to interest rate changes – where is mortgage risk concentrated? |
| **First‑home buyers** | Is Christchurch or Auckland more supply‑constrained right now? Where does affordability improve fastest after OCR cuts? |

**Core analytical question:**  
> *“Has the OCR easing since late 2024 reversed the 2022–2023 price decline, and how does the response vary across 16 NZ regions?”*

---

## Data Sources (100% public & free)

| Source | Dataset | Link |
|--------|---------|------|
| RBNZ | M10 Housing (regional median price, sales) | [RBNZ M10](https://www.rbnz.govt.nz/statistics/m10) |
| RBNZ | OCR historical (monthly) | [RBNZ OCR](https://www.rbnz.govt.nz/monetary-policy/official-cash-rate) |
| Stats NZ | Building Consents (monthly, by region) | [Stats NZ CSV](https://www.stats.govt.nz/large-datasets/csv-files-for-download/) |
| Stats NZ | Regional population & migration (annual) | [Stats NZ Population](https://www.stats.govt.nz/topics/population) |

---

## Data Limitations (Honest Reflection)

> *“No dataset is perfect – transparency is part of professional analytics.”*

- **Building consents ≠ actual construction** – there is a 3–12 month gap between consent and completion. This is treated as a *leading indicator* with acknowledged lag.
- **Migration data is annual** – we use it as a regional control variable, not a monthly driver. Intra‑year migration surges are not captured.
- **Regional aggregation** masks micro‑variation (e.g., within Canterbury). Findings apply to regional level, not suburbs.
- **OCR changes are not purely exogenous** – they may be correlated with unobserved global shocks (COVID, global inflation). Causality is not claimed; we use event study + lagged regression to support inference.

---

## Analytical Assumptions

| Assumption | Justification |
|------------|----------------|
| OCR impacts house prices with a **2‑3 month lag** | Based on literature and preliminary cross‑correlation test |
| **National trends exist**, but regional heterogeneity is the primary object of interest | We report both national and region‑disaggregated results |
| **Correlation ≠ causation** | We use event study around OCR announcement dates to strengthen internal validity |
| House prices are seasonally adjusted | Raw data shows December/January dip – we apply X‑13 seasonal adjustment where relevant |

---

## Analytics Pipeline
Public Economic Data (RBNZ + Stats NZ)
↓
Python ETL (pandas)
↓
Data Cleaning & Harmonisation (regional keys, date alignment)
↓
Feature Engineering (lags, rolling averages, regional dummies)
↓
Statistical Analysis (statsmodels: OLS with lagged variables, event study)
↓
Tableau Public Semantic Model
↓
Interactive Dashboard (3 pages)
↓
Business Interpretation & Policy Insights


**Pipeline diagram:** see `architecture/pipeline.png` (drawn with draw.io).

---

## Key Insights (Executive Summary)

*To be updated after analysis – placeholder structure:*

1. **OCR lag:** A 1% OCR increase is associated with a **0.3–0.5% price moderation 2 months later**, but the effect varies **3x across regions**.
2. **Regional divergence:** Christchurch recovered faster than Auckland in 2024–2025, partly due to higher consent‑per‑capita.
3. **Supply matters:** Regions with building consents above the national average saw **smaller price spikes** after OCR cuts.
4. **What this means for a first‑home buyer today:** [Your conclusion here – e.g., "Christchurch offers better affordability with similar growth potential"]

---

## Reproducibility

Run the notebooks **in order**:

| Notebook | Purpose |
|----------|---------|
| `01_fetch_data.ipynb` | Download raw data from RBNZ & Stats NZ |
| `02_clean_align.ipynb` | Clean, align dates, merge regional datasets |
| `03_analysis.ipynb` | Lagged regression, event study, regional ranking |

```bash
pip install -r requirements.txt
jupyter notebook
```
## Project Structure

nz-housing-cycle-analysis/
├── data/
│   ├── raw/                 (ignored, download manually)
│   └── processed/           (cleaned CSV)
├── notebooks/
│   ├── 01_fetch_data.ipynb
│   ├── 02_clean_align.ipynb
│   └── 03_analysis.ipynb
├── src/
│   ├── clean.py
│   ├── features.py
│   └── models.py
├── outputs/
│   └── charts/              (PNG files for LinkedIn & portfolio)
├── dashboard/
│   └── README.md            (Tableau Public link + screenshot)
├── architecture/
│   └── pipeline.png
├── screenshots/             (dashboard previews)
├── .gitignore
├── requirements.txt
└── README.md


## Author & Use Case
Purpose: Portfolio project for Data Analyst / BI Analyst roles – targeting banks (ANZ/ASB/Westpac), Treasury, RBNZ, and property consultancies.

License: MIT – feel free to reuse with attribution.