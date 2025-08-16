import json, math, html, os, re, time, random, asyncio
import feedparser
from datetime import datetime, timezone
from pathlib import Path
from newspaper import Article
from collections import deque, defaultdict
from asyncio import Semaphore

# ================================
# 可调参数（也支持用环境变量覆盖）
# ================================
POSTS_DIR = "posts"
ITEMS_PER_PAGE = 50
MAX_TOTAL = 300
PER_FEED_LIMIT = 3
PER_SOURCE_PAGE_CAP = 2

# 每次运行最多处理多少篇文章（0=不限制）
MAX_ARTICLES_PER_RUN = int(os.getenv("MAX_ARTICLES_PER_RUN", "0"))

# OpenAI 模型与超时/重试设置
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # ✅ 默认 4o-mini（更省钱）
OPENAI_TIMEOUT = float(os.getenv("OPENAI_TIMEOUT", "60"))  # 每次请求超时秒数
OPENAI_MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "5"))
OPENAI_MIN_BACKOFF = float(os.getenv("OPENAI_MIN_BACKOFF", "2.0"))  # 初始退避秒
OPENAI_MAX_BACKOFF = float(os.getenv("OPENAI_MAX_BACKOFF", "30.0")) # 最大退避秒

# 受控并发：建议 3~5，根据配额与速率调整
SUMMARIZE_CONCURRENCY = int(os.getenv("SUMMARIZE_CONCURRENCY", "4"))

CATEGORIES = {
    "Storage": ["storage", "battery", "energy storage", "bess"],
    "PV": ["solar", "photovoltaic", "pv"],
    "Wind": ["wind"],
    "Charger": ["charger", "charging", "ev"],
    "PowerElectronics": ["inverter", "converter", "power electronics"]
}

# ================================
# OpenAI 摘要实现（内置 429 重试与退避）
# ================================
def summarize(title: str, url: str):
    """
    返回 (summary_en, summary_zh)
    使用 gpt-4o-mini；对 429/暂时性错误做指数退避重试。
    """
    try:
        # 新版 SDK（pip install openai>=1.0）
        from openai import OpenAI
        client = OpenAI(timeout=OPENAI_TIMEOUT)
    except Exception as e:
        raise RuntimeError(f"OpenAI SDK import/init failed: {e}")

    system_prompt = (
        "You are a concise news summarizer for energy/cleantech topics. "
        "Write two short, factual summaries (2–3 sentences each): one in EN, one in Simplified Chinese. "
        "Do not add opinions. Keep numbers and proper nouns accurate. Output JSON with keys 'en' and 'zh'."
    )
    user_prompt = (
        f"Title: {title}\n"
        f"URL: {url}\n\n"
        "Please read the page and produce the summaries."
    )

    backoff = OPENAI_MIN_BACKOFF
    for attempt in range(OPENAI_MAX_RETRIES):
        try:
            resp = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )
            content = resp.choices[0].message.content.strip()
            # 期望是 JSON；容错解析
            try:
                data = json.loads(content)
                en = str(data.get("en", "")).strip()
                zh = str(data.get("zh", "")).strip()
                if not en or not zh:
                    # 兜底：若不是 JSON，就直接把文本一分为二
                    raise ValueError("JSON missing fields")
            except Exception:
                # 非 JSON 格式时的简单提取：按分隔线或换行切
                parts = re.split(r"\n[-–—]+\n|\n{2,}", content)
                en = (parts[0] if parts else content).strip()
                zh = (parts[1] if len(parts) > 1 else "").strip()
            return en, zh
        except Exception as e:
            msg = str(e).lower()
            # 针对限流/服务器等临时性错误退避重试
            transient = any(k in msg for k in [
                "rate limit", "429", "temporarily", "timeout", "overloaded",
                "service unavailable", "502", "503", "504"
            ])
            if attempt < OPENAI_MAX_RETRIES - 1 and transient:
                sleep_s = min(OPENAI_MAX_BACKOFF, backoff * (2 ** attempt)) + random.uniform(0, 0.5)
                print(f"[WARN] OpenAI call failed (attempt {attempt+1}/{OPENAI_MAX_RETRIES}): {e}. "
                      f"Retrying in {sleep_s:.1f}s...")
                time.sleep(sleep_s)
                continue
            raise

# —— 将同步 summarize 封装为“受控并发”调用 —— #
async def _summarize_task(sema: Semaphore, title: str, link: str):
    loop = asyncio.get_event_loop()
    async with sema:
        # 不改你现有 summarize 的实现，丢到线程池里并发执行
        return await loop.run_in_executor(None, summarize, title, link)

def summarize_parallel(articles):
    """
    articles: [(title, link, preview, source, published), ...]
    return:   [(en, zh, err or None), ...] 与 articles 对齐
    """
    sema = Semaphore(SUMMARIZE_CONCURRENCY)

    async def runner():
        tasks = []
        for (title, link, *_rest) in articles:
            tasks.append(asyncio.create_task(_summarize_task(sema, title, link)))
        results = []
        for i, task in enumerate(tasks):
            try:
                en, zh = await task
                results.append((en, zh, None))
            except Exception as e:
                results.append(("", "", e))
        return results

    return asyncio.run(runner())

# ================================
# 其余业务逻辑（保持你原来的风格）
# ================================
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

    # 可选：限制每次运行的处理数量（防止打满配额）
    if MAX_ARTICLES_PER_RUN and MAX_ARTICLES_PER_RUN > 0:
        articles = articles[:MAX_ARTICLES_PER_RUN]

    Path(POSTS_DIR).mkdir(exist_ok=True)
    clear_old_pages()

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"[INFO] Processing {len(articles)} articles...")

    # —— 并发摘要（速度↑），且受 SUMMARIZE_CONCURRENCY 控制 —— #
    results = summarize_parallel(articles)

    processed = []
    for (article, res) in zip(articles, results):
        title, link, preview, source, published = article
        en, zh, err = res
        if err:
            print(f"[SKIPPED] {title}: {err}")
            continue
        tags = detect_tags(f"{title} {en}")
        processed.append((title, link, preview, en, zh, tags, source, published))

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
