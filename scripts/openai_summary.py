# scripts/openai_summary.py
import os
import json
import re
import time
import random
from hashlib import sha256

# OpenAI SDK v1+
from openai import OpenAI

# ========= 配置 =========
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # ✅ 默认 4o-mini，更省钱更稳
OPENAI_TIMEOUT = float(os.getenv("OPENAI_TIMEOUT", "60"))
OPENAI_MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "5"))
OPENAI_MIN_BACKOFF = float(os.getenv("OPENAI_MIN_BACKOFF", "2.0"))
OPENAI_MAX_BACKOFF = float(os.getenv("OPENAI_MAX_BACKOFF", "30.0"))

CACHE_FILE = "summary_cache.json"  # 兼容旧文件名，不改路径
_client = None


def _client_once() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=OPENAI_TIMEOUT)
    return _client


# ========= 缓存 =========
def _load_cache() -> dict:
    """
    兼容旧结构：旧文件是 {key: {en, zh}} 的 dict。
    """
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            # 若存的是 list/其它格式，兜底转 dict
            if isinstance(data, list):
                d = {}
                for it in data:
                    k = it.get("key")
                    if k:
                        d[k] = {"en": it.get("en", ""), "zh": it.get("zh", "")}
                return d
    except Exception:
        pass
    return {}


def _save_cache(cache: dict) -> None:
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        # 不让缓存写入失败影响主流程
        pass


def _normalize_text(s: str, limit_chars: int = 6000) -> str:
    s = (s or "").strip()
    if not s:
        return ""
    s = re.sub(r"\s+", " ", s)
    if len(s) > limit_chars:
        s = s[:limit_chars]
    return s


def _cache_key(title: str, link: str, article_text: str) -> str:
    """
    内容感知缓存：模型 + 标题 + 链接 + 正文片段
    正文更新→自动重算，避免“老摘要”
    """
    material = f"{OPENAI_MODEL}\n{title}\n{link}\n{_normalize_text(article_text)}"
    return sha256(material.encode("utf-8")).hexdigest()


# ========= LLM 摘要 =========
def _summarize_llm(title: str, link: str, article_text: str) -> tuple[str, str]:
    """
    只调用一次模型，同时返回英语+中文两个摘要。
    """
    system_prompt = (
        "You are a concise news summarizer for energy/cleantech topics. "
        "Write two short, factual summaries (2–3 sentences each): one in EN, one in Simplified Chinese. "
        "Use only information supported by the provided article content and title/URL. "
        "Do not add opinions. Keep numbers and proper nouns accurate. "
        "Output JSON with keys 'en' and 'zh'."
    )

    user_prompt = (
        f"Title: {title}\n"
        f"URL: {link}\n\n"
        f"Article content (excerpt, may be truncated):\n"
        f"{_normalize_text(article_text)}\n\n"
        "Please produce the summaries."
    )

    client = _client_once()
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
            content = (resp.choices[0].message.content or "").strip()

            # 期望 JSON；容错解析
            try:
                data = json.loads(content)
                en = str(data.get("en", "")).strip()
                zh = str(data.get("zh", "")).strip()
                if not en or not zh:
                    raise ValueError("JSON missing keys")
            except Exception:
                # 如果不是 JSON，简单切分两段做兜底
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
            # 最终失败抛出，让上层决定如何展示
            raise


# ========= 对外接口（兼容旧调用） =========
def summarize(title: str, link: str, article_text: str = "") -> tuple[str, str]:
    """
    兼容旧接口：老代码只会传 (title, link)。
    若可传入 article_text（正文片段），摘要质量更高。
    """
    cache = _load_cache()
    key = _cache_key(title, link, article_text)

    if key in cache:
        hit = cache[key]
        return hit.get("en", ""), hit.get("zh", "")

    try:
        en, zh = _summarize_llm(title, link, article_text)
        cache[key] = {"en": en, "zh": zh}
        _save_cache(cache)
        return en, zh
    except Exception as e:
        print(f"❌ OpenAI failed on: {title} — {e}")
        # 兜底，返回可识别的占位
        return "Error generating summary", "错误摘要"
