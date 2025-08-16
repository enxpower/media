# -*- coding: utf-8 -*-
import json, math, html
import feedparser
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from openai_summary import summarize
from newspaper import Article

POSTS_DIR = "posts"
ITEMS_PER_PAGE = 50
MAX_TOTAL = 300
PER_FEED_LIMIT = 3  # 每个来源最多抓几条

# ---------- 类目 & 关键词 ----------
CATEGORIES = {
    "Storage": ["storage", "battery", "energy storage", "bess"],
    "PV": ["solar", "photovoltaic", "pv"],
    "Wind": ["wind"],
    "Charger": ["charger", "charging", "ev", "charging pile", "charge point"],
    "PowerElectronics": ["inverter", "converter", "power electronics"],
    # 新增：Tender（招标/投标/采购）
    "Tender": [
        "tender", "tenders", "tendering", "procurement", "rfp", "rfq", "rfi",
        "bid", "bids", "bidding", "auction", "solicitation", "contract notice",
        "call for", "award", "招标", "投标", "采购", "比选", "询价", "公告", "中标", "成交", "资格预审"
    ]
}

# 命中这些来源标题片段或域名时，默认补强 #Tender
TENDER_HINT_SOURCES = {
    "contracts finder", "gov.uk", "sam.gov", "tenders.gov.au", "ccgp.gov.cn",
    "energy-storage.news", "tenders", "auction"
}
TENDER_HINT_HOSTS = {
    "contractsfinder.service.gov.uk", "sam.gov", "tenders.gov.au",
    "ccgp.gov.cn", "energy-storage.news"
}

def detect_tags(text, source_title="", link=""):
    """
    根据标题/摘要/预览文本、来源标题、链接综合打标签。
    - 关键词命中类目（包含 Tender）
    - 来源标题或域名命中提示则补强 #Tender
    - 无命中时回退为 General
    """
    tags = set()
    t = (text or "").lower()
    # 1) 关键词命中
    for cat, keywords in CATEGORIES.items():
        if any(kw in t for kw in keywords):
            tags.add(cat)
    # 2) 来源/域名提示 -> Tender
    st = (source_title or "").lower()
    host = urlparse(link).netloc.lower() if link else ""
    if any(hint in st for hint in TENDER_HINT_SOURCES) or any(h in host for h in TENDER_HINT_HOSTS):
        tags.add("Tender")
    # 3) 保底
    if not tags:
        tags.add("General")
    return list(tags)

def extract_preview(link, fallback_summary=""):
    try:
        article = Article(link)
        article.download()
        article.parse()
        paragraphs = [p.strip() for p in article.text.split("\n") if p.strip()]
        preview = " ".join(paragraphs[:2])
        if len(preview) > 400:
            preview = preview[:380] + "..."
        # 若网页实在抓不到文本，回退 RSS summary
        return preview or (fallback_summary[:400] if fallback_summary else "")
    except Exception as e:
        print(f"[WARN] Failed to fetch preview from {link}: {e}")
        return fallback_summary[:400]

def load_feeds(json_file="feeds.json"):
    with open(json_file, "r", encoding="utf-8") as f:
        return json.load(f)

def fetch_articles(feeds, per_feed_limit=PER_FEED_LIMIT, max_total=MAX_TOTAL):
    """按每源上限抓取，尽量均衡，不超过总上限"""
    collected = []
    for f in feeds:
        d = feedparser.parse(f["url"])
        entries = d.entries or []
        count = 0
        for e in entries:
            if count >= per_feed_limit:
                break
            if len(collected) >= max_total:
                return collected
            try:
                title = e.title
                link = e.link
                fallback_summary = html.unescape(e.get("summary", "")[:400])
                preview = extract_preview(link, fallback_summary)
                source = d.feed.get("title", f.get("name") or "Unknown Source")
                # 兼容不同 feed 的时间字段
                published = e.get("published") or e.get("updated") or ""
                collected.append((title, link, preview, source, published))
                count += 1
            except Exception as err:
                print(f"[SKIPPED] Bad entry from {f['url']}: {err}")
    return collected

def build_html_snippet(idx, title, link, preview, summary_en, summary_zh, tags, source, published):
    title_esc = html.escape(title)
    link_esc = html.escape(link)
    preview_esc = html.escape(preview)
    summary_en_esc = html.escape(summary_en)
    summary_zh_esc = html.escape(summary_zh)
    tag_html = " ".join(f"#{t}" for t in tags)
    category = tags[0] if tags else "General"
    source_esc = html.escape(source or "")
    published_esc = html.escape(published or "")

    return f'''
<div class="news-post" data-category="{category}" data-title="{title_esc.lower()}" data-summary="{summary_en_esc.lower()}">
  <h3>{idx}. <a href="{link_esc}" target="_blank" class="news-link">{title_esc}</a></h3>
  <div class="meta"><span class="source">{source_esc}</span> | <span class="date">{published_esc}</span></div>
  <p class="preview">{preview_esc}</p>
  <p class="summary" data-summary-en="{summary_en_esc}" data-summary-zh="{summary_zh_esc}">{summary_en_esc}</p>
  <div class="tags">{tag_html}</div>
</div>
'''

def main():
    feeds = load_feeds()
    articles = fetch_articles(feeds)

    Path(POSTS_DIR).mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"[INFO] Processing {len(articles)} articles...")

    processed = []
    for idx, (title, link, preview, source, published) in enumerate(articles, start=1):
        try:
            summary_en, summary_zh = summarize(title, link)
            # 传入更多上下文以便更准地打标签（含 preview/source/link）
            tags = detect_tags(f"{title} {summary_en} {preview}", source_title=source, link=link)
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

        # 语言切换（保持你的原逻辑）
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
