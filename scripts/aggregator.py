import json, math
import feedparser
from datetime import datetime
from pathlib import Path
from openai_summary import summarize

POSTS_DIR = "posts"
ITEMS_PER_PAGE = 50

CATEGORIES = {
    "Storage": ["storage", "battery", "energy storage", "bess"],
    "PV": ["solar", "photovoltaic", "pv"],
    "Wind": ["wind"],
    "Charger": ["charger", "charging", "ev"],
    "PowerElectronics": ["inverter", "converter", "power electronics"]
}

def detect_category(text):
    t = text.lower()
    for cat, kw_list in CATEGORIES.items():
        for kw in kw_list:
            if kw in t:
                return cat
    return "General"

def load_feeds(json_file="feeds.json"):
    with open(json_file, "r", encoding="utf-8") as f:
        return json.load(f)

def fetch_articles(feeds):
    results = []
    for f in feeds:
        d = feedparser.parse(f["url"])
        for e in d.entries:
            results.append((e.title, e.link))
    return results

def build_html_snippet(idx, title, link, summary_en, summary_zh, category):
    return f'''
<div class="news-post" data-category="{category}">
  <h3>{idx}. <a href="{link}" target="_blank" class="news-link">{title}</a></h3>
  <p class="summary" data-summary-en="{summary_en}" data-summary-zh="{summary_zh}">{summary_en}</p>
  <div class="category-label">{category}</div>
</div>
'''

def main():
    feeds = load_feeds()
    articles = fetch_articles(feeds)[:500]

    Path(POSTS_DIR).mkdir(exist_ok=True)
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    print(f"⏳ Colors processing {len(articles)} articles...")

    processed = []
    for idx, (t, l) in enumerate(articles, start=1):
        try:
            en, zh = summarize(t, l)
            cat = detect_category(t + " " + en)
            processed.append((idx, t, l, en, zh, cat))
        except Exception as ex:
            print(f"⚠️ Skipped {t}: {ex}")

    pages = math.ceil(len(processed) / ITEMS_PER_PAGE)
    for pg in range(1, pages+1):
        start = (pg-1)*ITEMS_PER_PAGE
        chunk = processed[start:start+ITEMS_PER_PAGE]
        html = f"<!-- Last Updated: {ts} -->\n"
        for item in chunk:
            html += build_html_snippet(*item)
        Path(f"{POSTS_DIR}/page{pg}.html").write_text(html, encoding="utf-8")
        print(f"✅ Wrote page{pg}.html with {len(chunk)} posts.")

if __name__ == "__main__":
    main()
