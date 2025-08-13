import feedparser
import json
import time
import hashlib
from datetime import datetime, timedelta

# === CONFIG ===
FEED_FILE = "feeds.json"
OUTPUT_FILE = "news.json"
USER_AGENT = "DysonxNewsBot/1.0 (+https://dysonx.com)"
MAX_DAYS = 30

# === FUNCTIONS ===
def load_feeds():
    with open(FEED_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)
        feeds = []
        for item in raw:
            if isinstance(item, str):
                feeds.append({"url": item})
            elif isinstance(item, dict) and "url" in item:
                feeds.append(item)
        return feeds

def is_recent(entry, max_days):
    published = entry.get("published_parsed") or entry.get("updated_parsed")
    if not published:
        return False
    published_time = time.mktime(published)
    cutoff = time.time() - max_days * 86400
    return published_time >= cutoff

def generate_id(entry):
    return hashlib.md5(entry.link.encode("utf-8")).hexdigest()

def fetch_and_filter(feeds):
    collected = []
    for feed in feeds:
        url = feed.get("url")
        if not url:
            continue
        try:
            d = feedparser.parse(url, request_headers={"User-Agent": USER_AGENT})
            for entry in d.entries:
                if not is_recent(entry, MAX_DAYS):
                    continue
                collected.append({
                    "id": generate_id(entry),
                    "title": entry.get("title", "No Title"),
                    "link": entry.get("link"),
                    "summary": entry.get("summary", "")[:300],
                    "published": time.strftime("%Y-%m-%d %H:%M:%S", entry.published_parsed) if "published_parsed" in entry else "",
                    "source": d.feed.get("title", "")
                })
        except Exception as e:
            print(f"Error fetching {url}: {e}")
    return collected

# === MAIN ===
if __name__ == "__main__":
    feeds = load_feeds()
    items = fetch_and_filter(feeds)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"Fetched {len(items)} items.")
