import os
import json
import datetime
import time
from datetime import timedelta, timezone
from google import genai
from google.genai import types
from jinja2 import Template

# 1. API・時間設定
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
jst = timezone(timedelta(hours=+9), 'JST')
now = datetime.datetime.now(jst)
today_str = now.strftime("%Y-%m-%d")

# 2. プロンプト設定 (4ヶ国語対応)
PROMPT = f"""
Today's date is {today_str}. 
Search for top news from Japan's 5 major newspapers and global news (BBC/Reuters).
Select THREE topics: 1. Social (Japan), 2. Investment (Japan), 3. International (Global).

Requirements for TITLES:
- Format: 'Main Title ： Sub Title' (Full-width '：').
- Languages: Japanese (jp), English (en), Chinese Simplified (zh), Hindi (hi).

Requirements for CONTENT:
- Perspective: "Editor H's Perspective" (編集者Hの視点).
- Tone: Intellectual yet accessible.
- Languages: All 4 languages (jp, en, zh, hi).
- Glossary: Define 5 key terms in all 4 languages.

Output ONLY a raw JSON object:
{{
  "articles": [
    {{
      "category": "Social",
      "titles": {{"jp": "...", "en": "...", "zh": "...", "hi": "..."}},
      "contents": {{"jp": "...", "en": "...", "zh": "...", "hi": "..."}},
      "critiques": {{"jp": "...", "en": "...", "zh": "...", "hi": "..."}},
      "glossary": [
        {{
          "terms": {{"jp": "...", "en": "...", "zh": "...", "hi": "..."}},
          "defs": {{"jp": "...", "en": "...", "zh": "...", "hi": "..."}}
        }}
      ]
    }}
  ]
}}
"""

def generate():
    data = None
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash-exp', # 最新モデルを指定
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

    # 本文中の用語をポップアップ用に置換（全言語対応）
    langs = ['jp', 'en', 'zh', 'hi']
    for article in data['articles']:
        for g in article['glossary']:
            for l in langs:
                term = g['terms'][l]
                definition = g['defs'][l].replace("'", "\\'")
                article['contents'][l] = article['contents'][l].replace(
                    term, f'<span class="term" onclick="openPanel(\'{term}\', \'{definition}\')">{term}</span>'
                )

    data['date'] = today_str
    data_path = 'docs/data.json'
    os.makedirs('docs/articles', exist_ok=True)
    
    # 履歴管理
    history = []
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            try: history = json.load(f)
            except: history = []

    history = [e for e in history if e.get('date') != today_str]
    history.insert(0, data)
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(history[:100], f, ensure_ascii=False, indent=2)

    # HTML生成
    for t_name, out_name in [('template_article.html', f'docs/articles/{today_str}.html'), ('template_portal.html', 'docs/index.html')]:
        if os.path.exists(t_name):
            with open(t_name, 'r', encoding='utf-8') as f:
                tmpl = Template(f.read())
            with open(out_name, 'w', encoding='utf-8') as f:
                f.write(tmpl.render(items=history, item=data, today=today_str))

if __name__ == "__main__":
    generate()
