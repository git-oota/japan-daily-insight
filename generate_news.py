import os
import json
import datetime
import time
from datetime import timedelta, timezone
from google import genai
from google.genai import types
from jinja2 import Template

# 1. API設定
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# 2. 日本時間(JST)の設定
jst = timezone(timedelta(hours=+9), 'JST')
now = datetime.datetime.now(jst)
today_str = now.strftime("%Y-%m-%d")

# 3. プロンプト設定（社会・投資・国際の3カテゴリ）
PROMPT = f"""
Today's date is {today_str}. 
Search for the TOP NEWS from:
1. Japan's 5 major newspapers (Asahi, Yomiuri, Mainichi, Nikkei, Sankei).
2. Global news (NYT, BBC, Reuters).

Select THREE different main topics: 
1. Social Issue (Japan context)
2. Investment/Economy (Japan context)
3. International (Global top story)

Rewrite each as a Nicholas Kristof-style column for junior high school students.
Requirements:
- Empathic, historical perspective, and deep analysis.
- Provide both English and Japanese text.
- For each, pick 5-10 difficult terms for the glossary.

Output ONLY a raw JSON object:
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
