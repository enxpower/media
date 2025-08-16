import json, math, html, os, re, time, random, asyncio, hashlib
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

# 每次运行最多处理多少篇文章（0=不限制）——为“质量优先”保持默认0（不限）
MAX_ARTICLES_PER_RUN = int(os.getenv("MAX_ARTICLES_PER_RUN", "0"))

# OpenAI 模型与超时/重试设置
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # ✅ 更省钱且质量好
OPENAI_TIMEOUT = float(os.getenv("OPENAI_TIMEOUT", "60"))
OPENAI_MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "5"))
OPENAI_MIN_BACKOFF = float(os.getenv("OPENAI_MIN_BACKOFF", "2.0"))
OPENAI_MAX_BACKOFF = float(os.getenv("OPENAI_MAX_BACKOFF", "30.0"))

# 受控并发（摘要阶段）
SUMMARIZE_CONCURRENCY = int(os.getenv("SUMMARIZE_CONCURRENCY", "4"))

# 缓存目录（正文缓存 + 摘要缓存），避免重复下载与重复调用API
CACHE_DIR = Path(".cache/aggregator")
CONTENT_CACHE = CACHE_DIR / "content.jsonl"   # 每行: {"url":..., "sha":..., "text":...}
SUMMARY_CACHE = CACHE_DIR / "summaries.jsonl" # 每行: {"key":..., "model":..., "title":..., "url":..., "en":..., "zh":...}


# =============== 简易 JSONL 缓存 ===============

def _sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()

def _load_jsonl(path: Path) -> dict:
    d = {}
    if not path.exists():
        return d
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                # 对 content.jsonl：用 url 做 key；对 summaries.jsonl：用 key 做 key
                if path == CONTENT_CACHE and "url" in obj:
                    d[obj["url"]] = obj
                elif path == SUMMARY_CACHE and "key" in obj:
                    d[obj["key"]] = obj
            except Exception:
                continue
    return d

def _append_jsonl(path: Path, obj: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


# =============== 分类与文本处理 ===============

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

# 高质量：抓正文（用于LLM上下文），但把结果缓存起来，避免每次都下网页
def fetch_fulltext_with_cache(link: str, fallback_summary="") -> tuple[str, str]:
    """
    返回 (preview, full_text)
    - preview: 用于页面显示的导语（保持你原逻辑）
    - full_text: 供 LLM 摘要使用的正文（尽量多，提升质量）
    缓存键：url
    """
    content_db = _load_jsonl(CONTENT_CACHE)
    if link in content_db and content_db[link].get("text"):
        full_text = content_db[link]["text"]
        preview = strip_tags(fallback_summary) if not full_text else " ".join(full_text.split("\n")[:2]).strip() or strip_tags(fallback_summary)
        preview = (preview[:380] + "...") if len(preview) > 400 else preview
        return preview, full_text

    # 未命中缓存：抓取
    full_text = ""
    preview = ""
    try:
        import socket
        socket.setdefaulttimeout(8)  # 给网络库一个总超时，避免长阻塞
        article = Article(link)
        article.download()
        article.parse()
        full_text = article.text.strip()
        paragraphs = [p.strip() for p in full_text.split("\n") if p.strip()]
        preview = " ".join(paragraphs[:2]) if paragraphs else strip_tags(fallback_summary)
    except Exception:
        preview = strip_tags(fallback_summary)

    preview = (preview[:380] + "...") if len(preview) > 400 else preview

    # 写入缓存（即使 full_text 为空也记下，避免下次重复尝试）
    _append_jsonl(CONTENT_CACHE, {
        "url": link,
        "sha": _sha1(link),
        "text": full_text
    })
    return preview, full_text


# =============== OpenAI 摘要（含缓存 + 429退避 + 并发） ===============

def summarize_with_cache(title: str, url: str, article_text: str) -> tuple[str, str]:
    """
    先查摘要缓存；未命中则调用 LLM。
    缓存key = sha1(model + '\n' + title + '\n' + url + '\n' + first_2000_chars(article_text))
    这样一旦页面有实质更新（正文变化），会自动重算摘要，质量不降。
    """
    # 为了稳定token，限制送入 LLM 的正文片段长度（字符近似token，保守取 6000 字符）
    context = article_text.strip()
    if context:
        context = re.sub(r"\s+", " ", context)
    context_cut = context[:6000]

    cache_key_material = f"{OPENAI_MODEL}\n{title}\n{url}\n{context_cut}"
    key = _sha1(cache_key_material)

    summary_db = _load_jsonl(SUMMARY_CACHE)
    hit = summary_db.get(key)
    if hit and hit.get("en") and hit.get("zh"):
        return hit["en"], hit["zh"]

    # 没有命中 → 调用 LLM（带正文上下文，质量↑）
    en, zh = _summarize_llm(title, url, context_cut)

    _append_jsonl(SUMMARY_CACHE, {
        "key": key,
        "model": OPENAI_MODEL,
        "title": title,
        "url": url,
        "en": en,
        "zh": zh
    })
    return en, zh


def _summarize_llm(title: str, url: str, article_text: str) -> tuple[str, str]:
    """
    真正的 LLM 调用（保留你原有的退避/重试逻辑），
    但把“正文精华”一并送进prompt以提升摘要质量。
    """
    try:
        from openai import OpenAI
        client = OpenAI(timeout=OPENAI_TIMEOUT)
    except Exception as e:
        raise RuntimeError(f"OpenAI SDK import/init failed: {e}")

    system_prompt = (
        "You are a concise news summarizer for energy/cleantech topics. "
        "Write two short, factual summaries (2–3 sentences each): one in EN, one in Simplified Chinese. "
        "Use only information supported by the provided article content and title/URL. "
        "Do not add opinions. Keep numbers and proper nouns accurate. Output JSON with keys 'en' and 'zh'."
    )

    # 把正文精华也给模型（质量↑），但控制长度避免超token
    user_prompt = (
        f"Title: {title}\n"
        f"URL: {url}\n\n"
        f"Article content (excerpt, may be truncated):\n"
        f"{article_text}\n\n"
        "Please produce the summaries."
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
            try:
                data = json.loads(content)
                en = str(data.get("en", "")).strip()
                zh = str(data.get("zh", "")).strip()
                if not en or not zh:
                    raise ValueError("JSON missing fields")
            except Exception:
                parts = re.split(r"\n[-–—]+\n|\n{2,}", content)
                en = (parts[0] if parts else content).strip()
                zh = (parts[1] if len(parts) > 1 else "").strip()
            return en, zh
        except Exception as e:
            msg = str(e).lower()
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


# —— 将摘要并行化，速度↑且不降质量 —— #
async def _summarize_task(sema: Semaphore, title: str, link: str, article_text: str):
    loop = asyncio.get_event_loop()
    async with sema:
        # 使用缓存版本，避免重复请求；把正文送进模型以提升质量
        return await loop.run_in_executor(None, summarize_with_cache, title, link, article_text)

def summarize_parallel(articles, fulltext_map: dict):
    """
    articles: [(title, link, preview, source, published), ...]
    fulltext_map: {link: full_text}
    return:   [(en, zh, err or None), ...] 与 articles 对齐
    """
    sema = Semaphore(SUMMARIZE_CONCURRENCY)

    async def runner():
        tasks = []
        for (title, link, *_rest) in articles:
            article_text = fulltext_map.get(link, "")
            tasks.append(asyncio.create_task(_summarize_task(sema, title, link, article_text)))
        results = []
        for task in asyncio.as_completed(tasks):
            # 这里按完成顺序收集，后面我们按顺序回填
            pass
        # 为了按原顺序返回，逐个 await
        ordered = []
        for (title, link, *_rest) in articles:
            article_text = fulltext_map.get(link, "")
            try:
                en, zh = await _summarize_task(sema, title, link, article_text)
                ordered.append((en, zh, None))
            except Exception as e:
                ordered.append(("", "", e))
        return ordered

    return asyncio.run(runner())


# =============== 抓取与分页（与你原版一致，新增了正文缓存调用） ===============

def load_feeds(json_file="feeds.json"):
    with open(json_file, "r", encoding="utf-8") as f:
        return json.load(f)

def fetch_articles(feeds, per_feed_limit=PER_FEED_LIMIT, max_total=MAX_TOTAL):
    """
    返回 (collected, fulltext_map)
    - collected: [(title, link, preview, source, published), ...]  —— 与你原结构一致
    - fulltext_map: {link: full_text}                               —— 给 LLM 用的上下文，不影响 UI
    """
    collected = []
    fulltext_map = {}
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

                # 高质量：抓一次正文并缓存；preview 用两段正文或RSS摘要兜底
                preview, full_text = fetch_fulltext_with_cache(link, clean_summary)

                source = d.feed.get("title", "Unknown Source")
                published = e.get("published", "Unknown Date")
                collected.append((title, link, preview, source, published))
                fulltext_map[link] = full_text
                count += 1
            except Exception as err:
                print(f"[SKIPPED] Bad entry from {f['url']}: {err}")
    return collected, fulltext_map

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
    articles, fulltext_map = fetch_articles(feeds)

    # 可选：限制每次运行的处理数量（保持质量为先，默认不限）
    if MAX_ARTICLES_PER_RUN and MAX_ARTICLES_PER_RUN > 0:
        articles = articles[:MAX_ARTICLES_PER_RUN]

    Path(POSTS_DIR).mkdir(exist_ok=True)
    clear_old_pages()

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"[INFO] Processing {len(articles)} articles... (concurrency={SUMMARIZE_CONCURRENCY})")

    # 并发 + 缓存 + 正文上下文 —— 质量↑，速度↑，费用↓
    results = summarize_parallel(articles, fulltext_map)

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
