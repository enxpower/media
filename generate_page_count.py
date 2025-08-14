import os
import re
import json

# 设置路径
POSTS_DIR = 'posts'
OUTPUT_FILE = os.path.join(POSTS_DIR, 'page-count.json')

# 匹配 pageX.html 的正则
page_pattern = re.compile(r'^page(\d+)\.html$')

def count_pages():
    if not os.path.exists(POSTS_DIR):
        print(f"❌ 目录不存在：{POSTS_DIR}")
        return

    page_numbers = []
    for filename in os.listdir(POSTS_DIR):
        match = page_pattern.match(filename)
        if match:
            page_num = int(match.group(1))
            page_numbers.append(page_num)

    if not page_numbers:
        print("⚠️ 未找到任何 pageX.html 文件")
        return

    total_pages = max(page_numbers)
    data = {'total_pages': total_pages}

    # 写入 JSON 文件
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"✅ 已生成 {OUTPUT_FILE}，总页数: {total_pages}")

if __name__ == "__main__":
    count_pages()
