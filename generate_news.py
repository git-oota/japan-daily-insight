import os
import json
import datetime
import time
from datetime import timedelta, timezone
from google import genai
from google.genai import types
from jinja2 import Template

# 1. API設定 (最新SDKの初期化方法)
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# 2. 日本時間(JST)の設定
jst = timezone(timedelta(hours=+9), 'JST')
now = datetime.datetime.now(jst)
today_str = now.strftime("%Y-%m-%d")

# 3. プロンプト設定
PROMPT = f"""
Today's date is {today_str}. 
Search for the TOP NEWS from Japan's 5 major newspapers: Asahi, Yomiuri, Mainichi, Nikkei, and Sankei.
Find ONE common significant theme from today's headlines.

Write TWO columns (Social and Investment) in the style of Nicholas Kristof.
- Audience: Intellectual US readers and Japanese junior high school students.
- Content: Empathic, historical perspective, and deep analysis.
- Requirement: Provide both English and Japanese text for each section.

Output ONLY a raw JSON object. No markdown blocks, no preamble.
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
    print(f"Starting generation for {today_str} (JST) using Google Gen AI SDK...")
    
    data = None
    # 4. AIによる記事生成 (最新の検索ツール指定)
    for attempt in range(3):
        try:
            print(f"Attempt {attempt+1}...")
            response = client.models.generate_content(
                model='gemini-3-flash-preview', # または 'gemini-3-flash-preview'
                contents=PROMPT,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearchRetrieval())],
                    response_mime_type='application/json' # 強制的にJSONで出力させる
                )
            )
            
            # SDKが自動的にパースしたオブジェクトを辞書に変換
            if response.parsed:
                data = response.parsed
            else:
                # パースに失敗した場合はテキストから抽出
                res_text = response.text
                start_idx = res_text.find('{')
                end_idx = res_text.rfind('}') + 1
                data = json.loads(res_text[start_idx:end_idx])
            
            print("Successfully generated and parsed JSON.")
            break
        except Exception as e:
            print(f"Error in attempt {attempt+1}: {e}")
            time.sleep(20)
    
    if not data:
        raise Exception("Failed to generate content after all attempts.")

    # 5. データの保存・テンプレート反映
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

    history = [e for e in history if e.get('date') != today_str]
    history.insert(0, data)
        
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(history[:100], f, ensure_ascii=False, indent=2)

    templates = [
        ('template_portal.html', 'docs/index.html'),
        ('template_article.html', f'docs/articles/{today_str}.html')
    ]

    for t_name, out_name in templates:
        if os.path.exists(t_name):
            with open(t_name, 'r', encoding='utf-8') as f:
                tmpl = Template(f.read())
            with open(out_name, 'w', encoding='utf-8') as f:
                f.write(tmpl.render(items=history, item=data))
            print(f"Successfully rendered: {out_name}")

if __name__ == "__main__":
    generate()
