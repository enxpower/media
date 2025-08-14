# EnergizeOS™ News Aggregator

🌍 A multilingual, auto-updating energy news aggregator — curated from global sources in sectors like solar, wind, storage, EV charging, and power electronics.

![screenshot](./assets/screenshot.png)

---

## 🔍 Features

- ✅ **Automated Fetching & Summarization**  
  Pulls latest RSS headlines and uses OpenAI to summarize them in English and Chinese.

- 🌐 **Language Toggle**  
  Seamlessly switch between English and Chinese summaries with one click.

- 🧠 **Tag-based Categorization**  
  Auto-classifies each post into categories like `PV`, `Wind`, `Storage`, `Charger`, etc.

- 📱 **Responsive & Mobile-Friendly**  
  Modern UI with clean Apple-style typography, responsive layout, and lightweight design.

- 🕒 **Hourly GitHub Action Automation**  
  Automatically updates every hour via scheduled GitHub workflows.

---

## 🧱 Tech Stack

| Layer        | Tech Used                          |
| ------------ | ---------------------------------- |
| Frontend     | HTML, CSS, JavaScript              |
| Backend Task | Python 3, `newspaper3k`, `feedparser`, `OpenAI API` |
| Automation   | GitHub Actions                     |
| Deployment   | GitHub Pages                       |
| Styling      | Custom CSS (Apple-style), Icons via FontAwesome |

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/enxpower/media.git
cd media

2. Install dependencies
pip install -r requirements.txt

3. Set your OpenAI API Key
export OPENAI_API_KEY=your_key_here

4. Run the aggregator locally (optional)
python scripts/aggregator.py

🔁 Automation: GitHub Actions

update-content.yml workflow automatically:

Fetches new RSS articles

Summarizes using GPT

Categorizes and saves paginated HTML (posts/pageX.html)

Commits changes to the repository

Manual run

You can manually trigger it on GitHub via the "Actions" tab → Update News Content → Run workflow.

📁 Project Structure
media/
├── posts/                   # Auto-generated news pages
├── scripts/
│   ├── aggregator.py        # Main fetch/summarize script
│   └── openai_summary.py    # GPT summarization logic
├── components/              # JS modules for UI (lang toggle, search, pagination, footer)
├── styles/                  # CSS files
├── feeds.json               # RSS feed sources
├── index.html               # Main page
├── .github/workflows/       # GitHub Actions automation
└── requirements.txt         # Python dependencies

🌐 Deployment

This site is hosted via GitHub Pages:

Branch: main

Path: ./index.html

Automatic builds triggered on content update

To preview locally:

python3 -m http.server
# Visit http://localhost:8000

📡 Feed Sources

See feeds.json for curated industry sources from:

⚡ Energy Storage

☀️ Solar / PV

🌬️ Wind Power

🔌 EV Charging

🔋 Power Electronics

🇨🇳 Chinese industry media (CNEVPost, 电车资源, etc.)

Want to contribute sources? Submit a pull request!

🛡 License
Copyright © 2025 Energize Solutions Inc.

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License.
See LICENSE for details.

✉️ Contact

For feedback, partnerships, or inquiries:

📫 info@energizeos.com
🐙 GitHub – enxpower
