import json, math, html, os, re
import feedparser
from datetime import datetime, timezone
from pathlib import Path
from newspaper import Article
from collections import deque, defaultdict

# === 你项目里的摘要函数（保持不变，如无此模块可自行实现或改为占位） ===
from openai_summary import summarize

POSTS_DIR = "posts"
ITEMS_PER_PAGE = 50
MAX_TOTAL = 300
PER_FEED_LIMIT = 3          # 每个来源最多抓几条
PER_SOURCE_PAGE_CAP = 2     # 每页同一来源最多显示几条

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
    """移除 HTML 标签 -> 文本，并压缩空白"""
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", s)  # 去标签
    s = html.unescape(s)
    return " ".join(s.split())

def extract_preview(link, fallback_summary=""):
    """优先抓正文前两段；失败则使用清洗后的 summary"""
    try:
        article = Article(link)
        article.download()
        article.parse()
        paragraphs = [p.strip() for p in article.text.split("\n") if p.strip()]
        preview = " ".join(paragraphs[:2])
    except Exception:
        preview = strip_tags(fallback_summary)

    if len(preview) > 400:
        preview = preview[:380] + "..."
    return preview

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
            if count >= per_feed_limit:
                break
            if len(collected) >= max_total:
                return collected

            try:
                title = e.title
                link = e.link
                if link in seen_links:
                    continue
                seen_links.add(link)

                # 清洗 summary（去 HTML）
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

        # 第一轮：严格限制每源条数
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

        # 第二轮：回填
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

    # 构建分享链接（注意 URL 编码）
    title_q = urllib.parse.quote_plus(title)
    link_q = urllib.parse.quote_plus(link)

    

    


def clear_old_pages():
    """删除 posts 目录下所有 pageX.html，防止旧页面残留"""
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
            html_content += build_html_snippet(
                start_index + offset, title, link, preview, summary_en, summary_zh, tags, source, published
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
    # === 自动生成 sitemap.xml ===
    print("[INFO] Generating sitemap.xml...")

    domain = "https://media.energizeos.com"
    today = datetime.utcnow().strftime("%Y-%m-%d")

    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')

        # 首页
        f.write("  <url>\n")
        f.write(f"    <loc>{domain}/</loc>\n")
        f.write(f"    <lastmod>{today}</lastmod>\n")
        f.write("  </url>\n")

        # 每个分页页面
        for i in range(1, len(pages) + 1):
            f.write("  <url>\n")
            f.write(f"    <loc>{domain}/page{i}.html</loc>\n")
            f.write(f"    <lastmod>{today}</lastmod>\n")
            f.write("  </url>\n")

        f.write("</urlset>\n")

    print("[INFO] Sitemap generated.")


if __name__ == "__main__":
    main()
