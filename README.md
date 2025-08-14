# ⚡ Energy News Aggregator

A modular, OpenAI-powered news aggregation website focused on:

- 🔋 Energy Storage
- ☀️ Solar (PV)
- 🌬️ Wind
- 🚗 EV Charging
- 🔌 Power Electronics

Hosted on GitHub Pages, fully static and automatically updated every hour.

---

## 🚀 Features

- ✅ Modular components (footer, pagination, language switch)
- ✅ RSS feeds (editable via `feeds.json`)
- ✅ Automatic classification
- ✅ AI-generated summaries (OpenAI GPT-4o)
- ✅ English / Chinese toggle
- ✅ Pagination with iframe switching
- ✅ GitHub Actions auto update (`posts/page1.html`, etc.)

---

## 📂 Project Structure

media/
├── feeds.json # RSS feed sources
├── posts/ # Auto-generated paginated HTML (page1.html, ...)
│ └── page1.html
├── scripts/ # Core logic
│ ├── aggregator.py # Main script to fetch + generate pages
│ └── openai_summary.py # GPT-4o summary integration
├── styles/
│ └── main.css # Main styling
├── components/ # JS modules (pagination, footer, lang switch)
│ ├── footer.js
│ ├── pagination.js
│ └── langToggle.js
├── index.html # Main homepage (iframe + dynamic modules)
└── .github/workflows/
└── update.yml # GitHub Actions auto-refresh workflow

---

## 🧠 Requirements

- Python 3.10 or newer
- Python packages:
pip install openai feedparser

- OpenAI API key (used for generating summaries)  
Set via environment variable or GitHub Secret:
```bash
export OPENAI_API_KEY=your_key_here
🛠️ Local Development

To manually run the feed aggregator and generate pages:

python scripts/aggregator.py


Then open index.html in your browser to preview the site locally.

To change or add RSS feeds, simply update:

feeds.json

🌐 Deployment & Automation

This project is intended to run as a fully static GitHub Pages website.

GitHub Actions Automation:

Automatic execution every hour via cron

Builds updated posts/page*.html using OpenAI GPT-4o

Auto-commits and pushes only if content has changed

Requires the following secret:

OPENAI_API_KEY

See .github/workflows/update.yml for full automation logic.

📄 License

MIT License © 2025 EnergizeOS
