import json, math, html
import feedparser
from datetime import datetime
from pathlib import Path
from openai_summary import summarize

try:
    from newspaper import Article
    NEWSPAPER_AVAILABLE = True
except ImportError:
    print("⚠️ Warning: newspaper3k not available. Preview will fallback to RSS summary.")
    NEWSPAPER_AVAILABLE = False

POSTS_DIR = "posts"
ITEMS_PER_PAGE = 50

CATEGORIES = {
    "Storage": ["storage", "battery", "energy storage", "bess"],
    "PV": ["solar", "photovoltaic", "pv"],
    "Wind": ["wind"],
    "Charger": ["charger", "charging", "ev"],
    "PowerElectronics": ["inverter", "converter", "power electronics"]
}

def detect_tags(text):
    tags = []
    t = text.lower()
    for cat, keywords in CATEGORIES.items():
        if any(kw in t for kw in keywords):
            tags.append(cat)
    return tags or ["General"]

def extract_preview(link, fallback_summary=""):
    if not NEWSPAPER_AVAILABLE:
        return fallback_summary[:400]

    try:
        article = Article(link)
        article.download()
        article.parse()
        paragraphs = [p.strip() for p in article.text.split("\n") if p.strip()]
        preview = " ".join(paragraphs[:2])
        return preview[:380] + "..." if len(preview) > 400 else preview
    except Exception as e:
        print(f"⚠️ Preview fetch failed: {e}")
        return fallback_summary[:400]

def load_feeds(json_file="feeds.json"):
    with open(json_file, "r", encoding="utf-8") as f:
        return json.load(f)

def fetch_articles(feeds):
    results = []
    for feed in feeds:
        d = feedparser.parse(feed["url"])
        for entry in d.entries:
            title = entry.title
            link = entry.link
            fallback_summary = html.unescape(entry.get("summary", "")[:400])
            preview = extract_preview(link, fallback_summary)
            results.append((title, link, preview))
    return results

def build_html_snippet(idx, title, link, preview, summary_en, summary_zh, tags):
    title = html.escape(title)
    link = html.escape(link)
    preview = html.escape(preview)
    summary_en = html.escape(summary_en)
    summary_zh = html.escape(summary_zh)
    tag_html = " ".join(f"#{tag}" for tag in tags)
    category = tags[0]

    return f'''
<div class="news-post" data-category="{category}" data-title="{title.lower()}" data-summary="{summary_en.lower()}">
  <h3>{idx}. <a href="{link}" target="_blank" class="news-link">{title}</a></h3>
  <p class="preview">{preview}</p>
  <p class="summary" data-summary-en="{summary_en}" data-summary-zh="{summary_zh}">{summary_en}</p>
  <div class="category-label">{category}</div>
  <div class="tags">{tag_html}</div>
</div>
'''

def main():
    feeds = load_feeds()
    articles = fetch_articles(feeds)[:500]

    Path(POSTS_DIR).mkdir(exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    print(f"📥 Fetching {len(articles)} articles...")

    processed = []
    for idx, (title, link, preview) in enumerate(articles, start=1):
        try:
            summary_en, summary_zh = summarize(title, link)
            tags = detect_tags(f"{title} {summary_en}")
            processed.append((idx, title, link, preview, summary_en, summary_zh, tags))
        except Exception as e:
            print(f"❌ Skipped {title}: {e}")

    pages = math.ceil(len(processed) / ITEMS_PER_PAGE)
    for pg in range(1, pages + 1):
        start = (pg - 1) * ITEMS_PER_PAGE
        chunk = processed[start:start + ITEMS_PER_PAGE]
        html = f"<!-- Last Updated: {timestamp} -->\n"
        for item in chunk:
            html += build_html_snippet(*item)

        html += """
<!-- Lang toggle support -->
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
        Path(f"{POSTS_DIR}/page{pg}.html").write_text(html, encoding="utf-8")
        print(f"✅ page{pg}.html created with {len(chunk)} posts.")

if __name__ == "__main__":
    main()
