import os
import json
import datetime
import google.generativeai as genai
from jinja2 import Template

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-3-flash-preview')

# 今日の日付を取得
today = datetime.date.today()
today_str = today.strftime("%Y-%m-%d")

# プロンプトに今日の日付を埋め込み、鮮度を保証させる
PROMPT = f"""
Today's date is {today_str}. 
Analyze the actual TOP news from the morning editions of Japan's 5 major newspapers (Asahi, Yomiuri, Mainichi, Sankei, Nikkei) issued on THIS DAY ({today_str}).
Do NOT use old news like the Nikkei hitting 40,000 from 2024.

Write for a junior high school audience.
Structure:
1. Simple News Summary (Bilingual).
2. "The Crimson Pen" Sharp Critique (Bilingual) - Place this ONLY before the conclusion.
3. Conclusion: "Investment Hint" and "Life Hint" (Bilingual).
4. Proverb: 1 related Japanese proverb.
5. Glossary: 5 terms (Bilingual).

Output ONLY valid JSON:
{{
  "title_en": "...", "title_jp": "...",
  "content_en": "...", "content_jp": "...",
  "critique_en": "...", "critique_jp": "...",
  "investment_hint_en": "...", "investment_hint_jp": "...",
  "life_hint_en": "...", "life_hint_jp": "...",
  "proverb": {{"title_en": "...", "title_jp": "...", "desc_en": "...", "desc_jp": "..."}},
  "glossary": [{{"term_en": "...", "term_jp": "...", "def_en": "...", "def_jp": "..."}}]
}}
"""

def generate():
    response = model.generate_content(PROMPT)
    res_text = response.text.strip()
    if "```json" in res_text:
        res_text = res_text.split("```json")[1].split("```")[0]
    
    new_entry = json.loads(res_text.strip())
    new_entry['date'] = today_str

    data_path = 'docs/data.json'
    os.makedirs('docs/articles', exist_ok=True)
    
    history = []
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            history = json.load(f)

    if not any(entry.get('date') == today_str for entry in history):
        history.insert(0, new_entry)
        
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(history[:100], f, ensure_ascii=False, indent=2)

    with open('template_article.html', 'r', encoding='utf-8') as f:
        tmpl_art = Template(f.read())
    with open(f'docs/articles/{{today_str}}.html', 'w', encoding='utf-8') as f:
        f.write(tmpl_art.render(item=new_entry))

    with open('template_portal.html', 'r', encoding='utf-8') as f:
        tmpl_port = Template(f.read())
    with open('docs/index.html', 'w', encoding='utf-8') as f:
        f.write(tmpl_port.render(items=history))

if __name__ == "__main__":
    generate()
