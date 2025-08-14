# scripts/aggregator.py
import json, math, html
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
    for cat, keywords in CATEGORIES.items():
        if any(kw in t for kw in keywords):
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
            title = e.title
            link = e.link
            results.append((title, link))
    return results

def build_html_snippet(idx, title, link, summary_en, summary_zh, category):
    title_html = html.escape(title)
    link_html = html.escape(link)
    summary_en_html = html.escape(summary_en)
    summary_zh_html = html.escape(summary_zh)

    return f'''
<div class="news-post" data-category="{category}" data-title="{title_html.lower()}" data-summary="{summary_en_html.lower()}">
  <h3>{idx}. <a href="{link_html}" target="_blank" class="news-link">{title_html}</a></h3>
  <p class="summary" data-summary-en="{summary_en_html}" data-summary-zh="{summary_zh_html}">{summary_en_html}</p>
  <div class="category-label">{category}</div>
</div>
'''

def main():
    feeds = load_feeds()
    articles = fetch_articles(feeds)[:500]

    Path(POSTS_DIR).mkdir(exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    print(f"📰 Processing {len(articles)} articles...")

    processed = []
    for idx, (title, link) in enumerate(articles, start=1):
        try:
            summary_en, summary_zh = summarize(title, link)
            category = detect_category(title + " " + summary_en)
            processed.append((idx, title, link, summary_en, summary_zh, category))
        except Exception as e:
            print(f"⚠️ Skipped {title}: {e}")

    total_pages = math.ceil(len(processed) / ITEMS_PER_PAGE)

    for page_num in range(1, total_pages + 1):
        start = (page_num - 1) * ITEMS_PER_PAGE
        chunk = processed[start:start + ITEMS_PER_PAGE]
        html_content = f"<!-- Last Updated: {timestamp} -->\n"
        for item in chunk:
            html_content += build_html_snippet(*item)

        # Inject language switching script
        html_content += """
<script>
window.addEventListener("message", (event) => {
  if (!event.data) return;
  const summaries = document.querySelectorAll(".summary");
  if (event.data === "switch-lang-zh") {
    summaries.forEach(el => el.textContent = el.dataset.summaryZh || el.dataset.summaryEn);
  }
  if (event.data === "switch-lang-en") {
    summaries.forEach(el => el.textContent = el.dataset.summaryEn || "");
  }
});
</script>
"""
        Path(f"{POSTS_DIR}/page{page_num}.html").write_text(html_content, encoding="utf-8")
        print(f"✅ Wrote page{page_num}.html with {len(chunk)} items")

if __name__ == "__main__":
    main()
