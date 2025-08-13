# aggregator.py
import json
import os
import feedparser
from openai_summary import summarize
from datetime import datetime

OUTPUT_PATH = "posts/page1.html"
MAX_ITEMS = 50  # 首页显示新闻数量限制

def load_feeds(file="feeds.json"):
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

def fetch_articles(feed_urls):
    articles = []
    for feed in feed_urls:
        d = feedparser.parse(feed["url"])
        for entry in d.entries:
            title = entry.title
            link = entry.link
            articles.append((title, link))
    return articles[:MAX_ITEMS]

def build_html(posts):
    html = ""
    for title, link, summary_en, summary_zh in posts:
        block = f"""
<div class='news-post' data-title="{title}" data-summary="{summary_en}">
  <h3><a href="{link}" target="_blank">{title}</a></h3>
  <p class="summary" data-summary-en="{summary_en}" data-summary-zh="{summary_zh}">{summary_en}</p>
</div>
"""
        html += block + "\n"
    return html

def main():
    feeds = load_feeds()
    articles = fetch_articles(feeds)

    print(f"🔍 Fetched {len(articles)} articles... Generating summaries...")

    all_posts = []
    for title, link in articles:
        try:
            summary_en, summary_zh = summarize(title, link)
            all_posts.append((title, link, summary_en, summary_zh))
        except Exception as e:
            print(f"⚠️ Skipped '{title}' due to error: {e}")

    html = build_html(all_posts)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Successfully wrote {len(all_posts)} posts to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
