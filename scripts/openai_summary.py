import os
import openai

# 获取 OpenAI API Key
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 调用 GPT 生成英文和中文摘要
def summarize(title, link):
    prompt_en = f"Summarize the following energy news title in 1-2 sentences in English.\\n\\nTitle: {title}\\nURL: {link}"
    prompt_zh = f"请用简洁中文将以下能源新闻标题概括成一到两句话。\\n\\n标题：{title}\\n链接：{link}"

    # 英文摘要
    response_en = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt_en}],
        temperature=0.5,
    )
    summary_en = response_en.choices[0].message.content.strip()

    # 中文摘要
    response_zh = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt_zh}],
        temperature=0.5,
    )
    summary_zh = response_zh.choices[0].message.content.strip()

    return summary_en, summary_zh
