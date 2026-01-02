import os
import json
import datetime
import time
from datetime import timedelta, timezone
from google import genai
from google.genai import types
from jinja2 import Template
import re

# 1. API設定
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# 2. 日本時間(JST)の設定
jst = timezone(timedelta(hours=+9), 'JST')
now = datetime.datetime.now(jst)
today_str = now.strftime("%Y-%m-%d")

# 3. プロンプト設定
PROMPT = f"""
Today's date is {today_str}. 
Search for top news from Japan's 5 major newspapers and global news (BBC/Reuters).
Select THREE main topics: 1. Social, 2. Investment, 3. International.

Rewrite each as a Nicholas Kristof-style column for junior high school students.
Requirements:
- Empathic, historical perspective, and deep analysis.
- Provide both English and Japanese text.
- For EACH article, pick 5 difficult terms used in the text and provide short definitions in both JP and EN.
- Sign off as "Editor H" (編集者H).

Output ONLY a raw JSON object:
{{
  "articles": [
    {{
      "category": "Social",
      "title_en": "...", "title_jp": "...",
      "content_en": "...", "content_jp": "...",
      "critique_en": "...", "critique_jp": "...",
      "proverb": {{"title": "...", "desc": "..."}},
      "glossary": [
        {{"term_en": "...", "def_en": "...", "term_jp": "...", "def_jp": "..."}}
      ]
    }},
    {{ "category": "Investment", ... }},
    {{ "category": "International", ... }}
  ]
}}
"""

def generate():
    data = None
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model='gemini-3-flash-preview',
                contents=PROMPT,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearchRetrieval())],
                    response_mime_type='application/json'
                )
            )
            data = response.parsed if response.parsed else json.loads(response.text)
            break
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            time.sleep(20)
    
    if not data: return

    # --- 【新機能】本文中の用語を自動的にタグ置換するロジック ---
    for article in data['articles']:
        for g in article['glossary']:
            # 日本語: 用語を <span class="term"> で囲む
            t_jp = g['term_jp']
            d_jp = g['def_jp'].replace("'", "\\'") # JSエラー防止のクォート処理
            replace_jp = f'<span class="term" onclick="openPanel(\'{t_jp}\', \'{d_jp}\')">{t_jp}</span>'
            article['content_jp'] = article['content_jp'].replace(t_jp, replace_jp)
            
            # 英語: 用語を <span class="term"> で囲む
            t_en = g['term_en']
            d_en = g['def_en'].replace("'", "\\'")
            replace_en = f'<span class="term" onclick="openPanel(\'{t_en}\', \'{d_en}\')">{t_en}</span>'
            article['content_en'] = article['content_en'].replace(t_en, replace_en)

    data['date'] = today_str
    data_path = 'docs/data.json'
    os.makedirs('docs/articles', exist_ok=True)
    
    history = []
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            try: history = json.load(f)
            except: history = []

    history = [e for e in history if e.get('date') != today_str]
    history.insert(0, data)
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(history[:100], f, ensure_ascii=False, indent=2)

    # テンプレート反映
    for t_name, out_name in [('template_article.html', f'docs/articles/{today_str}.html'), ('template_portal.html', 'docs/index.html')]:
        if os.path.exists(t_name):
            with open(t_name, 'r', encoding='utf-8') as f:
                tmpl = Template(f.read())
            with open(out_name, 'w', encoding='utf-8') as f:
                f.write(tmpl.render(items=history, item=data))

if __name__ == "__main__":
    generate()
