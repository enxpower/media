import os
import json
import math
import html
from pathlib import Path
from collections import deque, defaultdict
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser
from newspaper import Article

from openai_summary import summarize


# =========================
# 配置
# =========================
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
    "PowerElectronics": ["inverter", "converter", "power electronics"],
}


# =========================
# 工具函数：时间/URL/分类
# =========================
def _to_ts(v):
    """将常见的时间字符串/数值转换为UTC秒级时间戳；失败返回0。"""
    if not v:
        return 0
    if isinstance(v, (int, float)):
        return int(v)
    s = str(v).strip()

    # RFC822 / RSS（e.g. "Sat, 16 Aug 2025 06:12:29 GMT"）
    try:
        dt = parsedate_to_datetime(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except Exception:
        pass

    # ISO8601（e.g. "2025-08-16T06:12:29Z" 或 "...+00:00"）
    try:
        s2 = s.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s2)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except Exception:
        return 0


def best_ts(entry_dict):
    """
    取一个条目的“最佳时间戳”：max(published, updated, pubDate, lastBuildDate, date)
    entry_dict 可为 feedparser 的 entry 或我们内部的 dict。
    """
    candidates = [
        entry_dict.get("published"),
        entry_dict.get("updated"),
        entry_dict.get("pubDate"),
        entry_dict.get("lastBuildDate"),
        entry_dict.get("date"),
        entry_dict.get("published_ts"),
        entry_dict.get("updated_ts"),
    ]
    return max((_to_ts(x) for x in candidates), default=0)


def normalize_url(url: str) -> str:
    """简单规范化URL：去掉常见utm参数与结尾斜杠，便于去重。"""
    try:
        from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

        p = urlparse(url)
        q = parse_qsl(p.query, keep_blank_values=True)

        # 过滤跟踪参数
        drop_keys = {
            "utm_source", "utm_medium", "utm_campaign", "utm_term",
            "utm_content", "utm_id", "fbclid", "gclid", "mc_cid", "mc_eid"
        }
        q2 = [(k, v) for (k, v) in q if k.lower() not in drop_keys]
        query = urlencode(q2)

        # 去掉结尾斜杠
        path = p.path.rstrip("/") or "/"

        return urlunparse((p.scheme, p.netloc, path, p.params, query, p.fragment))
    except Exception:
        return url.strip()


def detect_tags(text):
    tags = []
    t = text.lower()
    for cat, keywords in CATEGORIES.items():
        if any(kw in t for kw in keywords):
            tags.append(cat)
    return tags or ["General"]


def extract_preview(link, fallback_summary=""):
    """用 newspaper3k 抓正文前两段，失败则回退到 feed 的 summary。"""
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


# =========================
# 抓取 & 预处理
# =========================
def load_feeds(json_file="feeds.json"):
    with open(json_file, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_articles(feeds, per_feed_limit=PER_FEED_LIMIT, max_total=MAX_TOTAL):
    """
    返回列表[dict]。每个dict包含：
    title, link, link_norm, source, published, updated, preview, raw_summary, guid, sort_ts
    """
    collected = []
    total = 0

    for f in feeds:
        d = feedparser.parse(f["url"])
        entries = d.entries or []
        source = d.feed.get("title", "Unknown Source")

        cnt = 0
        for e in entries:
            if cnt >= per_feed_limit or total >= max_total:
                break

            try:
                title = e.get("title") or ""
                link = e.get("link") or ""
                if not title or not link:
                    continue

                guid = e.get("id") or e.get("guid") or ""
                raw_summary = e.get("summary", "") or ""
                fallback_summary = html.unescape(raw_summary[:400])

                item = {
                    "title": title,
                    "link": link,
                    "link_norm": normalize_url(link),
                    "source": source,
                    "published": e.get("published") or "",
                    "updated": e.get("updated") or "",
                    "raw_summary": fallback_summary,
                    "preview": None,          # 稍后填
                    "guid": guid,
                    "sort_ts": 0,             # 稍后计算
                    "summary_en": None,       # 稍后填
                    "summary_zh": None,       # 稍后填
                    "tags": None,             # 稍后填
                }

                # 先确定排序时间戳（根据 feed 原数据）
                item["sort_ts"] = best_ts(item)

                # 生成预览
                item["preview"] = extract_preview(link, fallback_summary)

                collected.append(item)
                cnt += 1
                total += 1

            except Exception as err:
                print(f"[SKIPPED] Bad entry from {f['url']}: {err}")

        if total >= max_total:
            break

    return collected


def deduplicate_keep_latest(items):
    """
    去重：优先用 guid/id，其次规范化URL，再其次小写标题；保留 sort_ts 更晚的一条。
    """
    best = {}

    def key_of(it):
        return it.get("guid") or it.get("link_norm") or it.get("title", "").strip().lower()

    for it in items:
        k = key_of(it)
        prev = best.get(k)
        if (prev is None) or (it.get("sort_ts", 0) > prev.get("sort_ts", 0)):
            best[k] = it

    return list(best.values())


# =========================
# 排序/编排/分页
# =========================
def interleave_round_robin_dict(items, per_round=1):
    """按 source 分桶，轮换取数，尽量打散来源。"""
    buckets = {}
    for it in items:
        s = it["source"]
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


def paginate_with_cap_dict(mixed, page_size=ITEMS_PER_PAGE, per_source_cap=PER_SOURCE_PAGE_CAP):
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
            it = mixed[j]
            src = it["source"]
            link = it["link_norm"]
            if cnt[src] < per_source_cap and link not in in_page_set:
                page.append(it)
                cnt[src] += 1
                in_page_set.add(link)
            j += 1

        # 第二轮：回填到满
        if len(page) < page_size:
            j = i
            while j < n and len(page) < page_size:
                it = mixed[j]
                link = it["link_norm"]
                if link not in in_page_set:
                    page.append(it)
                    in_page_set.add(link)
                j += 1

        pages.append(page)
        i += len(page)

    return pages


# =========================
# HTML 生成
# =========================
def build_html_snippet(idx, item):
    title = html.escape(item["title"])
    link = html.escape(item["link"])
    preview = html.escape(item["preview"] or "")
    summary_en = html.escape(item.get("summary_en") or "")
    summary_zh = html.escape(item.get("summary_zh") or "")
    tags = item.get("tags") or ["General"]
    tag_html = " ".join(f"#{t}" for t in tags)
    category = tags[0]
    source = html.escape(item["source"])
    # 优先显示原 published / updated 字符串（已是人类可读）
    published_str = item.get("published") or item.get("updated") or ""

    return f'''
<div class="news-post" data-category="{category}" data-title="{title.lower()}" data-summary="{summary_en.lower()}">
  <h3>{idx}. <a href="{link}" target="_blank" class="news-link">{title}</a></h3>
  <div class="meta"><span class="source">{source}</span> | <span class="date">{html.escape(published_str)}</span></div>
  <p class="preview">{preview}</p>
  <p class="summary" data-summary-en="{summary_en}" data-summary-zh="{summary_zh}">{summary_en}</p>
  <div class="tags">{tag_html}</div>
</div>
'''


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


# =========================
# 主流程
# =========================
def main():
    feeds = load_feeds()
    raw_items = fetch_articles(feeds)

    # —— 去重：保留时间戳更晚的条目
    items = deduplicate_keep_latest(raw_items)

    # —— 全量排序：按 sort_ts 降序（最新在前）
    items.sort(key=lambda x: x.get("sort_ts", 0), reverse=True)

    # —— 生成 AI 摘要与标签（在排序之后做，不影响排序）
    processed = []
    for it in items:
        try:
            # AI 摘要
            sum_en, sum_zh = summarize(it["title"], it["link"])
            it["summary_en"] = sum_en or ""
            it["summary_zh"] = sum_zh or ""
            # TAG
            it["tags"] = detect_tags(f"{it['title']} {it['summary_en']}")
            processed.append(it)
        except Exception as e:
            print(f"[SKIPPED] {it['title']}: {e}")

    # —— 轮换打散来源
    mixed = interleave_round_robin_dict(processed, per_round=1)

    # —— 分页（限制每页同源条数）
    pages = paginate_with_cap_dict(
        mixed,
        page_size=ITEMS_PER_PAGE,
        per_source_cap=PER_SOURCE_PAGE_CAP
    )

    # —— 输出 HTML
    Path(POSTS_DIR).mkdir(exist_ok=True)
    clear_old_pages()  # ☆ 在生成前先清空旧页面

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    total_pages = len(pages)

    for pg, chunk in enumerate(pages, start=1):
        html_content = f"<!-- Last Updated: {ts} -->\n"
        start_index = (pg - 1) * ITEMS_PER_PAGE + 1

        for offset, item in enumerate(chunk):
            html_content += build_html_snippet(start_index + offset, item)

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

    print(f"[DONE] Generated {total_pages} page(s). Last Updated: {ts}")


if __name__ == "__main__":
    main()
