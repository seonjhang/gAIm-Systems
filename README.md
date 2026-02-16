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
