EnergizeOS™ News Aggregator

A multilingual, auto-updating energy news site covering PV, wind, storage, EV charging, and power electronics.

Features

Hourly RSS fetch + English/Chinese summaries

One-click language toggle

Tagging (PV / Wind / Storage / Charger / Power Electronics)

Lightweight, responsive UI

Automated via GitHub Actions; deployed on GitHub Pages

Tech Stack

Frontend: HTML, CSS, JavaScript

Tasks: Python 3 (feedparser, newspaper3k, OpenAI API)

CI/CD: GitHub Actions

Hosting: GitHub Pages
Quick Start
```bash
git clone https://github.com/enxpower/media.git
cd media
pip install -r requirements.txt
export OPENAI_API_KEY=your_key_here
python scripts/aggregator.py   # optional local run
```

Automation

Workflow (e.g., update-content.yml) runs hourly:

Fetch RSS → summarize → categorize → write posts/pageX.html → commit.

Manual trigger: GitHub “Actions” → Update workflow → Run.
