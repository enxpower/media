import json, math, html
import feedparser
from datetime import datetime, timezone
from pathlib import Path
from openai_summary import summarize
from newspaper import Article
from collections import deque

POSTS_DIR = "posts"
ITEMS_PER_PAGE = 50
MAX_TOTAL = 300
PER_FEED_LIMIT = 3  # 每个来源最多抓几条

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

def fetch_articles(feeds, per_feed_limit=PER_FEED_LIMIT, max_total=MAX_TOTAL):
    collected = []

    for f in feeds:
        d = feedparser.parse(f["url"])
        entries = d.entries
        count = 0

        for e in entries:
            if count >= per_feed_limit:
                break  # 每个来源最多 N 条
            if len(collected) >= max_total:
                return collected  # 总抓取上限

            try:
                title = e.title
                link = e.link
                fallback_summary = html.unescape(e.get("summary", "")[:400])
                preview = extract_preview(link, fallback_summary)
                source = d.feed.get("title", "Unknown Source")
                published = e.get("published", "Unknown Date")
                collected.append((title, link, preview, source, published))
                count += 1
            except Exception as err:
                print(f"[SKIPPED] Bad entry from {f['url']}: {err}")

    return collected

def interleave_round_robin(items, source_index, per_round=1):
    """
    轮询混排：保持每个来源内部原有顺序，但在全局交错输出
    items: list[tuple]
    source_index: tuple 中 source 的索引位置
    per_round: 每轮每个来源最多取几条（通常 1）
    """
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
        if dq:  # 该来源还有剩余，排到队尾
            q.append((s, dq))
    return mixed

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
    articles = fetch_articles(feeds)

    Path(POSTS_DIR).mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"[INFO] Processing {len(articles)} articles...")

    # 先汇总并摘要（不带 idx），等混排后再编号
    processed = []
    for (title, link, preview, source, published) in articles:
        try:
            summary_en, summary_zh = summarize(title, link)
            tags = detect_tags(f"{title} {summary_en}")
            processed.append((title, link, preview, summary_en, summary_zh, tags, source, published))
        except Exception as e:
            print(f"[SKIPPED] {title}: {e}")

    # ★ 关键：在分页前先做轮询混排
    # 当前结构: (title, link, preview, summary_en, summary_zh, tags, source, published)
    mixed = interleave_round_robin(processed, source_index=6, per_round=1)

    total_pages = math.ceil(len(mixed) / ITEMS_PER_PAGE)
    for pg in range(1, total_pages + 1):
        start = (pg - 1) * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        chunk = mixed[start:end]

        html_content = f"<!-- Last Updated: {ts} -->\n"
        # 用全局序号渲染（避免每页都从 1 开始）
        for global_idx, item in enumerate(chunk, start=start + 1):
            title, link, preview, summary_en, summary_zh, tags, source, published = item
            html_content += build_html_snippet(
                global_idx, title, link, preview, summary_en, summary_zh, tags, source, published
            )

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
