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

# 2. プロンプト設定
PROMPT = f"""
Today's date is {today_str}. 
Search for top news from Japan's 5 major newspapers and global news (BBC/Reuters).
Select THREE topics: 1. Social (Japan), 2. Investment (Japan), 3. International (Global).

Requirements for TITLES:
- Main Title: Factual, straight news headline.
- Sub Title: Insightful sub-headline.
- Format: 'Main Title ： Sub Title' (Full-width '：').

Requirements for CONTENT:
- Perspective: Write the critique section as "Editor H's Perspective" (編集者Hの視点).
- Tone: Intellectual yet accessible (Kristof-style).
- Sign-off: DO NOT add a signature like "Editor H" at the very end of the text.
- Language: Both English and Japanese.
- Glossary: Define 5 key terms used in the text for the sliding panel.

Output ONLY a raw JSON object:
{{
  "articles": [
    {{
      "category": "Social",
      "title_en": "Main ： Sub", "title_jp": "メイン ： サブ",
      "content_en": "...", "content_jp": "...",
      "critique_en": "...", "critique_jp": "...",
      "proverb_jp": {{"title": "...", "desc": "..."}},
      "proverb_en": {{"title": "...", "desc": "..."}},
      "glossary": [{{"term_en": "...", "def_en": "...", "term_jp": "...", "def_jp": "..."}}]
    }}
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

    # 本文中の用語を自動的にスライド解説用タグに置換
    for article in data['articles']:
        for g in article['glossary']:
            t_jp, d_jp = g['term_jp'], g['def_jp'].replace("'", "\\'")
            article['content_jp'] = article['content_jp'].replace(t_jp, f'<span class="term" onclick="openPanel(\'{t_jp}\', \'{d_jp}\')">{t_jp}</span>')
            t_en, d_en = g['term_en'], g['def_en'].replace("'", "\\'")
            article['content_en'] = article['content_en'].replace(t_en, f'<span class="term" onclick="openPanel(\'{t_en}\', \'{d_en}\')">{t_en}</span>')

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

    for t_name, out_name in [('template_article.html', f'docs/articles/{today_str}.html'), ('template_portal.html', 'docs/index.html')]:
        if os.path.exists(t_name):
            with open(t_name, 'r', encoding='utf-8') as f:
                tmpl = Template(f.read())
            with open(out_name, 'w', encoding='utf-8') as f:
                f.write(tmpl.render(items=history, item=data))

if __name__ == "__main__":
    generate()
