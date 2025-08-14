import json, math, html
import feedparser
from datetime import datetime, timezone
from pathlib import Path
from openai_summary import summarize
from newspaper import Article

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
    try:
        article = Article(link)
        article.download()
        article.parse()
        paragraphs = [p.strip() for p in article.text.split("\n") if p.strip()]
        preview = " ".join(paragraphs[:2])
        if len(preview) > 400:
            preview = preview[:380] + "..."
        return preview
    except Exception as e:
        print(f"[WARN] Failed to fetch preview from {link}: {e}")
        return fallback_summary[:400]

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
            fallback_summary = html.unescape(e.get("summary", "")[:400])
            preview = extract_preview(link, fallback_summary)
            source = d.feed.get("title", "Unknown Source")
            published = e.get("published", "Unknown Date")
            results.append((title, link, preview, source, published))
    return results

def build_html_snippet(idx, title, link, preview, summary_en, summary_zh, tags, source, published):
    title = html.escape(title)
    link = html.escape(link)
    preview = html.escape(preview)
    summary_en = html.escape(summary_en)
    summary_zh = html.escape(summary_zh)
    tag_html = " ".join(f"#{tag}" for tag in tags)
    category = tags[0]
    source = html.escape(source)
    published = html.escape(published)

    return f'''
<div class="news-post" data-category="{category}" data-title="{title.lower()}" data-summary="{summary_en.lower()}">
  <h3>{idx}. <a href="{link}" target="_blank" class="news-link">{title}</a></h3>
  <div class="meta"><span class="source">{source}</span> | <span class="date">{published}</span></div>
  <p class="preview">{preview}</p>
  <p class="summary" data-summary-en="{summary_en}" data-summary-zh="{summary_zh}">{summary_en}</p>
  <div class="tags">{tag_html}</div>
</div>
'''

def main():
    feeds = load_feeds()
    articles = fetch_articles(feeds)[:500]

    Path(POSTS_DIR).mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"[INFO] Processing {len(articles)} articles...")

    processed = []
    for idx, (title, link, preview, source, published) in enumerate(articles, start=1):
        try:
            summary_en, summary_zh = summarize(title, link)
            tags = detect_tags(f"{title} {summary_en}")
            processed.append((idx, title, link, preview, summary_en, summary_zh, tags, source, published))
        except Exception as e:
            print(f"[SKIPPED] {title}: {e}")

    total_pages = math.ceil(len(processed) / ITEMS_PER_PAGE)
    for pg in range(1, total_pages + 1):
        start = (pg - 1) * ITEMS_PER_PAGE
        chunk = processed[start:start + ITEMS_PER_PAGE]
        html_content = f"<!-- Last Updated: {ts} -->\n"
        for item in chunk:
            html_content += build_html_snippet(*item)

        html_content += """
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
        Path(f"{POSTS_DIR}/page{pg}.html").write_text(html_content, encoding="utf-8")
        print(f"[INFO] Wrote page{pg}.html with {len(chunk)} posts.")

if __name__ == "__main__":
    main()
