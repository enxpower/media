import json, math, html, os, re
import feedparser
from datetime import datetime, timezone
from pathlib import Path
from newspaper import Article
from collections import deque, defaultdict
from openai_summary import summarize

POSTS_DIR = "posts"
ITEMS_PER_PAGE = 50
MAX_TOTAL = 300
PER_FEED_LIMIT = 3
PER_SOURCE_PAGE_CAP = 2

CATEGORIES = {
    "Storage": ["storage", "battery", "energy storage", "bess"],
    "PV": ["solar", "photovoltaic", "pv"],
    "Wind": ["wind"],
    "Charger": ["charger", "charging", "ev"],
    "PowerElectronics": ["inverter", "converter", "power electronics"]
}

def detect_tags(text: str):
    tags = []
    t = text.lower()
    for cat, keywords in CATEGORIES.items():
        if any(kw in t for kw in keywords):
            tags.append(cat)
    return tags or ["General"]

def strip_tags(s: str) -> str:
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return " ".join(s.split())

def extract_preview(link, fallback_summary=""):
    try:
        article = Article(link)
        article.download()
        article.parse()
        paragraphs = [p.strip() for p in article.text.split("\n") if p.strip()]
        preview = " ".join(paragraphs[:2])
    except Exception:
        preview = strip_tags(fallback_summary)
    return preview[:380] + "..." if len(preview) > 400 else preview

def load_feeds(json_file="feeds.json"):
    with open(json_file, "r", encoding="utf-8") as f:
        return json.load(f)

def fetch_articles(feeds, per_feed_limit=PER_FEED_LIMIT, max_total=MAX_TOTAL):
    collected = []
    seen_links = set()

    for f in feeds:
        d = feedparser.parse(f["url"])
        entries = d.entries
        count = 0

        for e in entries:
            if count >= per_feed_limit or len(collected) >= max_total:
                break
            try:
                title = e.title
                link = e.link
                if link in seen_links:
                    continue
                seen_links.add(link)
                raw_summary = e.get("summary", "")
                clean_summary = strip_tags(raw_summary)[:400]
                preview = extract_preview(link, clean_summary)
                source = d.feed.get("title", "Unknown Source")
                published = e.get("published", "Unknown Date")
                collected.append((title, link, preview, source, published))
                count += 1
            except Exception as err:
                print(f"[SKIPPED] Bad entry from {f['url']}: {err}")
    return collected

def interleave_round_robin(items, source_index, per_round=1):
    buckets = {}
    for it in items:
        s = it[source_index]
        buckets.setdefault(s, deque()).append(it)
    q = deque(buckets.items())
    mixed = []
    while q:
        s, dq = q.popleft()
        take = 0
        while dq and take < per_round:
            mixed.append(dq.popleft())
            take += 1
        if dq:
            q.append((s, dq))
    return mixed

def paginate_with_cap(mixed, page_size=ITEMS_PER_PAGE, per_source_cap=PER_SOURCE_PAGE_CAP):
    pages = []
    i = 0
    n = len(mixed)
    while i < n:
        page = []
        cnt = defaultdict(int)
        in_page_set = set()
        j = i
        while j < n and len(page) < page_size:
            item = mixed[j]
            src = item[6]
            link = item[1]
            if cnt[src] < per_source_cap and link not in in_page_set:
                page.append(item)
                cnt[src] += 1
                in_page_set.add(link)
            j += 1
        if len(page) < page_size:
            j = i
            while j < n and len(page) < page_size:
                item = mixed[j]
                link = item[1]
                if link not in in_page_set:
                    page.append(item)
                    in_page_set.add(link)
                j += 1
        pages.append(page)
        i += len(page)
    return pages

def build_html_snippet(idx, title, link, preview, summary_en, summary_zh, tags, source, published):
    import urllib.parse
    title_esc = html.escape(title)
    link_esc = html.escape(link)
    preview = html.escape(preview)
    summary_en = html.escape(summary_en)
    summary_zh = html.escape(summary_zh)
    tag_html = " ".join(f"#{tag}" for tag in tags)
    category = tags[0]
    source = html.escape(source)
    published = html.escape(published)
    title_q = urllib.parse.quote_plus(title)
    link_q = urllib.parse.quote_plus(link)
    share_html = f'''
    <div class="share-buttons">
      <a href="https://twitter.com/intent/tweet?text={title_q}&url={link_q}" target="_blank" aria-label="Share on Twitter" class="share-link" data-platform="Twitter">
        <i class="fab fa-twitter"></i>
      </a>
      <a href="https://www.linkedin.com/shareArticle?mini=true&url={link_q}&title={title_q}" target="_blank" aria-label="Share on LinkedIn" class="share-link" data-platform="LinkedIn">
        <i class="fab fa-linkedin"></i>
      </a>
      <a href="https://www.reddit.com/submit?url={link_q}&title={title_q}" target="_blank" aria-label="Share on Reddit" class="share-link" data-platform="Reddit">
        <i class="fab fa-reddit"></i>
      </a>
    </div>
    '''
    return f'''
<div class="news-post" data-category="{category}" data-title="{title_esc.lower()}" data-summary="{summary_en.lower()}">
  <h3>{idx}. <a href="{link_esc}" target="_blank" class="news-link">{title_esc}</a></h3>
  <div class="meta"><span class="source">{source}</span> | <span class="date">{published}</span></div>
  <p class="preview">{preview}</p>
  <p class="summary" data-summary-en="{summary_en}" data-summary-zh="{summary_zh}">{summary_en}</p>
  <div class="tags">{tag_html}</div>
  {share_html}
</div>
'''

def clear_old_pages():
    path = Path(POSTS_DIR)
    if not path.exists():
        return
    for file in path.glob("page*.html"):
        try:
            file.unlink()
            print(f"[INFO] Deleted old page: {file.name}")
        except Exception as e:
            print(f"[WARN] Could not delete {file}: {e}")

def main():
    feeds = load_feeds()
    articles = fetch_articles(feeds)
    Path(POSTS_DIR).mkdir(exist_ok=True)
    clear_old_pages()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"[INFO] Processing {len(articles)} articles...")
    processed = []
    for (title, link, preview, source, published) in articles:
        try:
            summary_en, summary_zh = summarize(title, link)
            tags = detect_tags(f"{title} {summary_en}")
            processed.append((title, link, preview, summary_en, summary_zh, tags, source, published))
        except Exception as e:
            print(f"[SKIPPED] {title}: {e}")
    mixed = interleave_round_robin(processed, source_index=6, per_round=1)
    pages = paginate_with_cap(mixed, page_size=ITEMS_PER_PAGE, per_source_cap=PER_SOURCE_PAGE_CAP)
    for pg, chunk in enumerate(pages, start=1):
        html_content = f"<!-- Last Updated: {ts} -->\n"
        start_index = (pg - 1) * ITEMS_PER_PAGE + 1
        for offset, item in enumerate(chunk):
            title, link, preview, summary_en, summary_zh, tags, source, published = item
            html_content += build_html_snippet(start_index + offset, title, link, preview, summary_en, summary_zh, tags, source, published)
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

    # === 自动生成 sitemap.xml ===
    print("[INFO] Generating sitemap.xml...")
    domain = "https://media.energizeos.com"
    today = datetime.utcnow().strftime("%Y-%m-%d")
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        f.write("  <url>\n")
        f.write(f"    <loc>{domain}/</loc>\n")
        f.write(f"    <lastmod>{today}</lastmod>\n")
        f.write("  </url>\n")
        for i in range(1, len(pages) + 1):
            f.write("  <url>\n")
            f.write(f"    <loc>{domain}/page{i}.html</loc>\n")
            f.write(f"    <lastmod>{today}</lastmod>\n")
            f.write("  </url>\n")
        f.write("</urlset>\n")
    print("[INFO] Sitemap generated.")

if __name__ == "__main__":
    main()
