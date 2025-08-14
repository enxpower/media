import os
import json
from hashlib import sha256
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
CACHE_FILE = "summary_cache.json"

# 加载缓存
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        cache = json.load(f)
else:
    cache = {}

def make_cache_key(title, link):
    return sha256(f"{title}|{link}".encode("utf-8")).hexdigest()

def summarize(title, link):
    cache_key = make_cache_key(title, link)
    if cache_key in cache:
        return cache[cache_key]["en"], cache[cache_key]["zh"]

    try:
        # 改为 gpt-3.5-turbo
        prompt_en = f"Summarize the following energy news title in 1-2 sentences in English.\n\nTitle: {title}\nLink: {link}"
        prompt_zh = f"请用简洁中文将以下能源新闻标题概括成一到两句话。\n\n标题：{title}\n链接：{link}"

        response_en = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt_en}],
            temperature=0.5,
        )
        summary_en = response_en.choices[0].message.content.strip()

        response_zh = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt_zh}],
            temperature=0.5,
        )
        summary_zh = response_zh.choices[0].message.content.strip()

        # 写入缓存
        cache[cache_key] = {"en": summary_en, "zh": summary_zh}
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)

        return summary_en, summary_zh

    except Exception as e:
        print(f"❌ OpenAI failed on: {title} — {e}")
        return "Error generating summary", "错误摘要"
