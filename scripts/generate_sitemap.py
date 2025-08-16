import os
from pathlib import Path

BASE_URL = "https://media.energizeos.com"
POSTS_DIR = "posts"
SITEMAP_PATH = "sitemap.xml"

def generate():
    urls = [f"{BASE_URL}/"]

    for file in sorted(Path(POSTS_DIR).glob("page*.html")):
        name = file.name
        if name.endswith(".html"):
            urls.append(f"{BASE_URL}/{name}")

    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in urls:
        sitemap += f"  <url><loc>{url}</loc></url>\n"
    sitemap += '</urlset>\n'

    Path(SITEMAP_PATH).write_text(sitemap, encoding="utf-8")
    print(f"[INFO] sitemap.xml written with {len(urls)} URLs")

if __name__ == "__main__":
    generate()
