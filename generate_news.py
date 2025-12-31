import os
import json
import datetime
import time
from datetime import timedelta, timezone
import google.generativeai as genai
from jinja2 import Template

# API設定
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# 1. 【重要】日本時間(JST)の設定
jst = timezone(timedelta(hours=+9), 'JST')
now = datetime.datetime.now(jst)
today_str = now.strftime("%Y-%m-%d")

# モデル設定 (ご指定のモデル)
model = genai.GenerativeModel(
    model_name='gemini-3-flash-preview',
    tools=[{'google_search_retrieval': {}}]
)

PROMPT = f"""
Today's date is {today_str}.
Search for today's top news from Nikkei, Yomiuri, Asahi, and Mainichi.
Select TWO main topics: 1. Social Issue, 2. Investment/Economy.

Rewrite each as a Nicholas Kristof-style column for junior high school students.
Requirements:
1. Tone: Deep, empathetic, and clear.
2. Content: Include background, history, Japanese culture, and related topics.
3. Structure for each article: 
   - Rewritten Content
   - The Crimson Pen's Sharp Critique
   - Today's Proverb
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
    data = None
    for attempt in range(3):
        try:
            response = model.generate_content(PROMPT)
            res_text = response.text.strip()
            if "```json" in res_text:
                res_text = res_text.split("```json")[1].split("```")[0]
            data = json.loads(res_text.strip())
            break
        except Exception as e:
            print(f"Error: {e}. Retrying in 60s...")
            time.sleep(60)
    
    if not data:
        print("Failed to generate data after 3 attempts.")
        return

    data['date'] = today_str
    data_path = 'docs/data.json'
    os.makedirs('docs/articles', exist_ok=True)
    
    history = []
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            try:
                history = json.load(f)
            except:
                history = []

    # 2. 【重要】上書きロジック：同日のデータがあれば一旦削除して差し替える
    history = [entry for entry in history if entry.get('date') != today_str]
    history.insert(0, data)
        
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(history[:100], f, ensure_ascii=False, indent=2)

    # 3. テンプレート反映 (PortalとArticleの両方を更新)
    for t_name, out_name in [('template_article.html', f'docs/articles/{today_str}.html'), ('template_portal.html', 'docs/index.html')]:
        if os.path.exists(t_name):
            with open(t_name, 'r', encoding='utf-8') as f:
                tmpl = Template(f.read())
            with open(out_name, 'w', encoding='utf-8') as f:
                f.write(tmpl.render(items=history, item=data))
        else:
            print(f"Warning: {t_name} not found.")

if __name__ == "__main__":
    generate()
