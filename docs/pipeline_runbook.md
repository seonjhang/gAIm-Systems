# Pipeline Runbook

## 1) Setup
- python -m venv .venv
- pip install -r requirements.txt

## 2) Scrape transcripts
- Script: src/scraping/asap_scraper.py
- Output: data/raw/asap_hockey.csv

## 3) Run LIWC feature extraction
- Script: src/nlp/liwc_analysis.py
- Input: data/raw/asap_hockey.csv (or cleaned)
- Output: data/processed/liwc_results.csv

## 4) Modeling (notebooks)
- notebooks/...
