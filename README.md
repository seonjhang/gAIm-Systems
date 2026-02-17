# 🏒 Hockey Draft Interview Collection Pipeline
## Overview

This project collects pre-draft YouTube interviews of NHL players,
extracts video transcripts, and isolates only the player's speech using GPT-4o-mini.

The final output is a structured dataset (TSV / JSONL) that can be used for:

- NLP research
- Player personality modeling
- Draft analysis
- Language pattern studies
- ML training data

## 🎯 What This Project Does (In 4 Steps)
```bash
Draft.xlsx (player list)
        ↓
YouTube Interview Search (YouTube Data API)
        ↓
Transcript Extraction (youtube-transcript-api)
        ↓
Player Speech Filtering (GPT-4o-mini)
        ↓
Structured Dataset Export (TSV / JSONL)
```

## 📁 Project Structure
```bash
hockey-interview-agent/
│
├── batch_youtube_transcripts_from_drafted.py
├── hockey_interview_collector.py
├── youtube_interview_finder.py
├── youtube_transcript_extractor.py
├── player_speech_extractor.py
├── nhl_article_parser.py
│
├── requirements.txt
├── SETUP.md
├── README.md
│
└── data/
    ├── raw/
    │   ├── transcript/
    │   └── player_speech/
    └── processed/
```

## 🗂 Data Folder Explanation
```bash
data/raw/
```
Contains original collected data.

### 1️⃣ Collection JSON

Full collection results for each player.

Includes:
- interview metadata
- sources
- transcript flags
- extraction results

### 2️⃣ data/raw/transcript/

Each file contains:
```bash
{
  "video_id": "...",
  "full_text": "...",
  "transcript": [
    {"text": "...", "start": 0.0, "duration": 2.4}
  ],
  "word_count": 487,
  "language": "en",
  "is_generated": true
}
```

This is the complete YouTube transcript.

### 3️⃣ data/raw/player_speech/

This contains GPT-filtered speech:
```bash
{
  "player_name": "...",
  "player_speech_text": "...",
  "word_count": 312,
  "original_word_count": 487,
  "reduction_ratio": 0.64,
  "model": "gpt-4o-mini"
}
```

This removes:
- Interviewer questions
- Non-player speakers
- Noise

```bash
data/processed/
```
Final structured export used for modeling.

Format (TSV):
```bash
player_name    text
Connor McDavid   I think it's been exciting...
```
This is the recommended dataset for analysis.

## ⚙️ Installation
### 1️⃣ Install dependencies
```bash
pip install -r requirements.txt
```
Dependencies include:
- openai
- requests
- beautifulsoup4
- python-dotenv
- youtube-transcript-api
- pandas

### 2️⃣ Setup Environment Variables

Create a .env file:
```bash
OPENAI_API_KEY=your_openai_key
YOUTUBE_API_KEY=your_youtube_key

# Optional (for proxy rotation)
PROXY_USERNAME=...
PROXY_PASSWORD=...
```

## 🚀 Usage
### A) Collect Interviews for a Single Player
```bash
python hockey_interview_collector.py "Connor McDavid"
```
This will:
- Search YouTube
- Extract transcript
- Filter player speech (GPT)
- Save results in data/raw/
- Append to data/processed/interviews.jsonl

### B) Batch Collect by Draft Year
```bash
python batch_youtube_transcripts_from_drafted.py \
    --excel data/Draft.xlsx \
    --year 2021 \
    --youtube_top_n 5
```

This will:
- Load all players drafted in the given year
- Collect top N interviews per player
- Export a structured TSV file:
```bash
data/processed/draft_2021_youtube_transcripts_TIMESTAMP.txt
```

## 🧠 Player Speech Extraction Strategy

We use GPT-4o-mini to identify which transcript segments belong to the player.

#### Design Philosophy
- High recall > high precision
- Include all player answers
- Exclude only clear interviewer questions
- Merge adjacent segments
- Fallback to heuristic filtering if GPT fails

Chunking strategy is used for long transcripts.

## 🧪 Reproducibility Checklist
Before sharing the project:
- pip install -r requirements.txt works
- .env.example exists
- Single-player run works
- Batch run works
- Sample data included
- Large raw data excluded via .gitignore

## 🔒 Security Notes
- .env is git-ignored
- API keys must not be committed
- Raw data can be large; only sample data should be included in repo

## ⚠️ Known Limitations
- YouTube API quota limits apply
- Some videos may not have transcripts enabled
- Web scraping fallback may fail due to site restrictions
- GPT extraction cost depends on transcript length

## 📈 Recommended Use of Final Dataset
Use the processed TSV/JSONL export for:
- Sentiment analysis
- Topic modeling
- Linguistic profiling
- Pre-draft psychological signal modeling
- Feature engineering for ML
Do NOT use raw transcript directly unless you want interviewer text included.

## 👨‍🔬 Project Ownership
Originally developed for NHL draft interview analysis.
Core components:
- YouTube Interview Finder
- Transcript Extractor
- GPT-based Player Speech Extractor
- Structured Dataset Exporter

## 🏁 Minimal Quick Start
```bash
pip install -r requirements.txt
python batch_youtube_transcripts_from_drafted.py --year 2021
```
