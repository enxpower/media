# -*- coding: utf-8 -*-
"""
Hourly Aggregator – hardened against 403 + noisy logs

改进要点：
1) 预览抓取优先走 requests + 浏览器 UA，失败再回退 newspaper3k；
2) feedparser 与网页请求统一使用浏览器 User-Agent，减少 403；
3) 失败重试（指数退避）、超时与“按 host 去重告警”，日志更干净；
4) 依旧保证“每源上限抓取 + 全局上限 + 均衡输入”的策略；
5) 标签检测沿用你的分类并补强 Tender 线索。
"""
import json, math, html, time, re
import feedparser
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from openai_summary import summarize
from newspaper import Article

# ------------------- 参数 -------------------
POSTS_DIR = "posts"
ITEMS_PER_PAGE = 50
MAX_TOTAL = 300
PER_FEED_LIMIT = 3  # 每个来源最多抓几条

REQ_TIMEOUT = 10  # 秒
MAX_RETRIES = 2   # 轻量重试（总共 1 次 + 1 次重试）
BACKOFF_BASE = 0.75  # 指数退避基数

# 浏览器 UA，尽量减少 403
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

REQUEST_HEADERS = {
    "User-Agent": BROWSER_UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "close",
}

# ------------------- 类目 & 关键词 -------------------
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

# ------------------- 日志工具（host 去重告警） -------------------
_warned_hosts = set()

def warn_once(link: str, msg: str):
    try:
        host = urlparse(link).netloc.lower()
    except Exception:
        host = ""
    key = f"{host}:{msg.split(' ')[0]}"
    if key in _warned_hosts:
        return
    _warned_hosts.add(key)
    print(f"[WARN] {host} -> {msg}")

# ------------------- 标签检测 -------------------
def detect_tags(text, source_title="", link=""):
    """
    根据标题/摘要/预览文本、来源标题、链接综合打标签。
    - 关键词命中类目（包含 Tender）
    - 来源标题或域名命中提示则补强 #Tender
    - 无命中时回退为 General
    """
    tags = set()
    t = (text or "").lower()
    for cat, keywords in CATEGORIES.items():
        if any(kw in t for kw in keywords):
            tags.add(cat)

    st = (source_title or "").lower()
    host = urlparse(link).netloc.lower() if link else ""
    if any(hint in st for hint in TENDER_HINT_SOURCES) or any(h in host for h in TENDER_HINT_HOSTS):
        tags.add("Tender")

    if not tags:
        tags.add("General")
    # 固定顺序输出，避免 data-category 抖动
    order = ["Tender", "Storage", "PV", "Wind", "Charger", "PowerElectronics", "General"]
    return [t for t in order if t in tags]

# ------------------- HTTP 抓取（带重试） -------------------
def http_get(url: str, headers=None, timeout=REQ_TIMEOUT, max_retries=MAX_RETRIES):
    headers = {**REQUEST_HEADERS, **(headers or {})}
    last_err = None
    for attempt in range(max_retries + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            # 某些站点返回 403/401/406，直接抛异常交给重试
            if resp.status_code >= 400:
                raise requests.HTTPError(f"status={resp.status_code}")
            return resp
        except Exception as e:
            last_err = e
            if attempt < max_retries:
                time.sleep((BACKOFF_BASE ** attempt) + 0.2)  # 轻退避
            else:
                break
    raise last_err

# ------------------- 预览抽取 -------------------
def _soup_preview(html_text: str) -> str:
    soup = BeautifulSoup(html_text, "html.parser")
    # 先尝试常见正文容器
    candidates = []
    for sel in ["article", "main", "[role=main]", ".post", ".entry-content", ".content", ".article"]:
        candidates.extend(soup.select(sel))
    nodes = candidates or [soup]

    texts = []
    for node in nodes:
        for p in node.find_all(["p", "li"], limit=6):
            txt = p.get_text(separator=" ", strip=True)
            if txt and len(txt) > 40:
                texts.append(txt)
        if texts:
            break

    preview = " ".join(texts[:2]) if texts else ""
    preview = re.sub(r"\s+", " ", preview).strip()
    if len(preview) > 400:
        preview = preview[:380] + "..."
    return preview

def extract_preview(link, fallback_summary=""):
    """
    优先使用 requests + 浏览器 UA 获取 HTML 并用 BeautifulSoup 摘要；
    失败再回退 newspaper3k；仍失败则返回 RSS summary。
    """
    # 1) requests + soup
    try:
        resp = http_get(link)
        preview = _soup_preview(resp.text)
        if preview:
            return preview
    except Exception as e:
        warn_once(link, f"requests preview failed: {e}")

    # 2) 回退 newspaper3k（其内部 UA 有时被拦，仍作为兜底）
    try:
        article = Article(link)
        article.download()
        article.parse()
        paragraphs = [p.strip() for p in article.text.split("\n") if p.strip()]
        preview = " ".join(paragraphs[:2])[:400]
        if preview:
            return preview
    except Exception as e:
        warn_once(link, f"newspaper fallback failed: {e}")

    # 3) 最终兜底：RSS summary
    return (fallback_summary or "")[:400]

# ------------------- FEEDS -------------------
def load_feeds(json_file="feeds.json"):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 兼容字符串/对象两种写法
    feeds = []
    for item in data:
        if isinstance(item, str):
            feeds.append({"url": item, "name": ""})
        elif isinstance(item, dict) and "url" in item:
            feeds.append(item)
    return feeds

# ------------------- 抓取与均衡 -------------------
def fetch_articles(feeds, per_feed_limit=PER_FEED_LIMIT, max_total=MAX_TOTAL):
    """
    按每源上限抓取，尽量均衡，不超过总上限。
    对 feedparser 使用浏览器 UA，减少 403。
    """
    collected = []
    for f in feeds:
        try:
            d = feedparser.parse(f["url"], request_headers={"User-Agent": BROWSER_UA})
        except Exception as e:
            print(f"[WARN] feed parse failed: {f['url']} -> {e}")
            continue

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
                # 某些 feed 没有 summary
                fallback_summary = html.unescape(e.get("summary", "")[:400])
                preview = extract_preview(link, fallback_summary)
                source = d.feed.get("title", f.get("name") or "Unknown Source")
                # 兼容不同 feed 的时间字段
                published = e.get("published") or e.get("updated") or ""
                collected.append((title, link, preview, source, published))
                count += 1
            except Exception as err:
                # 单条数据问题跳过，不阻断整源
                print(f"[SKIPPED] Bad entry from {f['url']}: {err}")
    return collected

# ------------------- HTML 构建 -------------------
def build_html_snippet(idx, title, link, preview, summary_en, summary_zh, tags, source, published):
    title_esc = html.escape(title or "")
    link_esc = html.escape(link or "")
    preview_esc = html.escape(preview or "")
    summary_en_esc = html.escape(summary_en or "")
    summary_zh_esc = html.escape(summary_zh or "")
    tag_html = " ".join(f"#{t}" for t in tags)
    category = tags[0] if tags else "General"
    source_esc = html.escape(source or "")
    published_esc = html.escape(published or "")

    return f'''
<div class="news-post" data-category="{category}" data-title="{title_esc.lower()}" data-summary="{summary_en_esc.lower()}">
  <h3>{idx}. <a href="{link_esc}" target="_blank" rel="noopener noreferrer" class="news-link">{title_esc}</a></h3>
  <div class="meta"><span class="source">{source_esc}</span> | <span class="date">{published_esc}</span></div>
  <p class="preview">{preview_esc}</p>
  <p class="summary" data-summary-en="{summary_en_esc}" data-summary-zh="{summary_zh_esc}">{summary_en_esc}</p>
  <div class="tags">{tag_html}</div>
</div>
'''

# ------------------- 主流程 -------------------
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

    total_pages = max(1, math.ceil(len(processed) / ITEMS_PER_PAGE))
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
