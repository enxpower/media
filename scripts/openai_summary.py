# scripts/openai_summary.py
import os
import openai

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def summarize(title, link):
    prompt_en = f"Summarize this news title in 1-2 sentences (in English):\nTitle: {title}\nLink: {link}"
    prompt_zh = f"用中文将这条新闻标题总结为一两句话：\n标题：{title}\n链接：{link}"

    # English summary
    response_en = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt_en}],
        temperature=0.5
    )
    summary_en = response_en.choices[0].message.content.strip()

    # Chinese summary
    response_zh = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt_zh}],
        temperature=0.5
    )
    summary_zh = response_zh.choices[0].message.content.strip()

    return summary_en, summary_zh
