import os
import json
import datetime
import time
import google.generativeai as genai
from jinja2 import Template

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# 検索ツールを有効化
model = genai.GenerativeModel(
    model_name='gemini-3-flash-preview',
    tools=[{'google_search_retrieval': {}}]
)

today_str = datetime.date.today().strftime("%Y-%m-%d")

PROMPT = f"""
Search for today's ({today_str}) top news from Nikkei, Yomiuri, Asahi, and Mainichi.
Select TWO main topics: 1. Social Issue, 2. Investment/Economy.

Rewrite each as a Nicholas Kristof-style column for junior high school students.
Requirements:
1. Tone: Deep, empathetic, and clear.
2. Content: Include background, history, Japanese culture, and related topics.
3. Structure for each article: 
   - Rewritten Content
   - The Crimson Pen's Sharp Critique (The final perspective)
   - Today's Proverb (Related to the topic)
   - Glossary (5-10 terms)

Output ONLY valid JSON:
{{
  "articles": [
    {{
      "category": "Social",
      "title_en": "...", "title_jp": "...",
      "content_en": "...", "content_jp": "...",
      "critique_en": "...", "critique_jp": "...",
      "proverb": {{"title": "...", "desc": "..."}},
      "glossary": [{{"term": "...", "def": "..."}}]
    }},
    {{
      "category": "Investment",
      "title_en": "...", "title_jp": "...",
      "content_en": "...", "content_jp": "...",
      "critique_en": "...", "critique_jp": "...",
      "proverb": {{"title": "...", "desc": "..."}},
      "glossary": [{{"term": "...", "def": "..."}}]
    }}
  ]
}}
"""

def generate():
    # 安定稼働のためのリトライ処理
    for attempt in range(3):
        try:
            response = model.generate_content(PROMPT)
            res_text = response.text.strip()
            if "```json" in res_text:
                res_text = res_text.split("```json")[1].split("```")[0]
            data = json.loads(res_text.strip())
            break
        except Exception as e:
            print(f"Error: {e}. Retrying...")
            time.sleep(60)
    else: return

    data['date'] = today_str
    data_path = 'docs/data.json'
    os.makedirs('docs/articles', exist_ok=True)
    
    history = []
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            history = json.load(f)

    if not any(entry.get('date') == today_str for entry in history):
        history.insert(0, data)
        
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(history[:100], f, ensure_ascii=False, indent=2)

    # テンプレート反映
    for t_name, out_name in [('template_article.html', f'docs/articles/{today_str}.html'), ('template_portal.html', 'docs/index.html')]:
        with open(t_name, 'r', encoding='utf-8') as f:
            tmpl = Template(f.read())
        with open(out_name, 'w', encoding='utf-8') as f:
            f.write(tmpl.render(items=history, item=data))

if __name__ == "__main__":
    generate()
