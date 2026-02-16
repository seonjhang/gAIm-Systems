# Predicting NHL Draft Success Using Interview Language (LIWC) + Pre-draft Signals

This repository contains a research pipeline built as part of a startup-led academic project to replicate/adapt Farrell et al. (2024) in the NHL context.
It combines:
- Pre-draft interview transcripts (scraped from ASAP Sports)
- Linguistic features (LIWC)
- Draft metadata / outcomes
to predict draft success and related career outcomes.

## Project Goal
Predict whether a prospect makes the NHL (and related measures such as longevity/impact) using:
1) Pre-draft interviews → LIWC features  
2) Draft / performance covariates

Reference document: see `/docs/project_overview.md`.

---

## Repository Structure
- `src/scraping/` : interview scraping + transcript extraction
- `src/nlp/` : LIWC feature extraction utilities
- `notebooks/` : EDA / cleansing / modeling experiments
- `docs/` : project overview, data dictionary, runbook
- `data/` : raw/processed datasets (not committed to Git by default)

---

## Data Sources
- ASAP Sports interview transcripts (public webpages)
- Draft metadata (see `Draft.xlsx`)

> Note: Raw datasets may contain large text fields and are excluded from Git history via `.gitignore`.

---

## Quickstart
### 1) Setup
```bash
python -m venv .venv
source .venv/bin/activate   # mac/linux
# .venv\Scripts\activate    # windows

pip install -r requirements.txt
```

### 2) Run Pipeline (high-level)

#### 1. Scrape interviews:
```bash
python -m src.scraping.asap_scraper --out data/raw/asap_hockey.csv
```

#### 2. Clean/standardize transcripts (optional if using existing cleaned file):
```bash
python -m src.preprocessing.build_dataset --in data/raw/asap_hockey.csv --out data/processed/asap_hockey_clean.csv
```

#### 3. LIWC feature extraction:
```bash
python -m src.nlp.liwc_analysis --in data/processed/asap_hockey_clean.csv --out data/processed/liwc_results.csv
```

#### 4. Modeling:
Open notebooks/02_prediction_model_liwc.ipynb.

## Key Outputs

data/raw/asap_hockey.csv: raw scraped transcripts

data/processed/asap_hockey_clean.csv: cleaned transcripts + metadata

data/processed/liwc_results.csv: LIWC features merged with transcript rows

data/processed/liwc_player_mean.csv: aggregated player-level LIWC features

---
### Handover Notes

If you are taking over this project, start with:
- /docs/pipeline_runbook.md
- /docs/data_dictionary.md
- notebooks/01_data_cleansing.ipynb
