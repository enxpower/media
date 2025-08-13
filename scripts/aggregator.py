from pathlib import Path

# Define the updated aggregator.py again after code execution reset
aggregator_code = """
import json, os, math
import feedparser
from datetime import datetime
from openai_summary import summarize

POSTS_DIR = "posts"
ITEMS_PER_PAGE = 50

CATEGORIES = {
    "Storage": ["storage", "battery", "bess", "energy storage"],
    "PV": ["solar", "photovoltaic", "pv"],
    "Wind": ["wind"],
    "Charger": ["charger", "charging", "ev charging"],
    "PowerElectronics": ["inverter", "converter", "power electronics"]
}

def detect_category(title, summary):
    combined = (title + " " + summary).lower()
    for category, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw in combined:
                return category
    return "General"

def load_feeds(file="feeds.json"):
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

def fetch_articles(feed_urls):
    articles = []
    for feed in feed_urls:
        d = feedparser.parse(feed["url"])
        for entry in d.entries:
            articles.append((entry.title, entry.link))
    return articles

def build_post_html(index, title, link, summary_en, summary_zh, category):
    return f'''
<div class="news-post" data-title="{title}" data-summary="{summary_en}" data-category="{category}">
  <h3><a href="{link}" target="_blank" class="news-link">{index+1}. {title}</a></h3>
  <p class="summary" data-summary-en="{summary_en}" data-summary-zh="{summary_zh}">{summary_en}</p>
  <div class="category-label">{category}</div>
</div>
'''

def main():
    feed_urls = load_feeds()
    raw_articles = fetch_articles(feed_urls)
    articles = raw_articles[:500]  # Safety cap

    Path(POSTS_DIR).mkdir(exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    print(f"⏳ Processing {len(articles)} articles...")

    processed = []
    for i, (title, link) in enumerate(articles):
        try:
            summary_en, summary_zh = summarize(title, link)
            category = detect_category(title, summary_en)
            processed.append((title, link, summary_en, summary_zh, category))
        except Exception as e:
            print(f"⚠️ Skipped '{title}': {e}")

    pages = math.ceil(len(processed) / ITEMS_PER_PAGE)
    for page in range(pages):
        chunk = processed[page*ITEMS_PER_PAGE:(page+1)*ITEMS_PER_PAGE]
        page_html = f"<!-- Last Updated: {timestamp} -->\\n"
        for idx, (title, link, summary_en, summary_zh, category) in enumerate(chunk):
            page_html += build_post_html(idx + page*ITEMS_PER_PAGE, title, link, summary_en, summary_zh, category)
        with open(f"{POSTS_DIR}/page{page+1}.html", "w", encoding="utf-8") as f:
            f.write(page_html)
        print(f"✅ Wrote page {page+1} with {len(chunk)} posts.")

if __name__ == "__main__":
    main()
"""

# Write the updated aggregator.py to disk
aggregator_path = Path("/mnt/data/scripts/aggregator.py")
aggregator_path.parent.mkdir(parents=True, exist_ok=True)
aggregator_path.write_text(aggregator_code.strip())

aggregator_path.name  # Return just the filename for confirmation
