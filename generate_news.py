import os
import json
import datetime
import time
from datetime import timedelta, timezone
import google.generativeai as genai
from jinja2 import Template

# 1. API設定
# 環境変数からAPIキーを取得
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# 2. 日本時間(JST)の厳密な設定
jst = timezone(timedelta(hours=+9), 'JST')
now = datetime.datetime.now(jst)
today_str = now.strftime("%Y-%m-%d")

# 3. モデルの初期化（404エラーを回避する最も安定した指定方法）
# 'models/' を付けず、ライブラリのデフォルト挙動（v1）を利用します
model = genai.GenerativeModel(
    model_name='gemini-3-flash-preview',
    tools=[{'google_search_retrieval': {}}]
)

# 4. プロンプト設定
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
    print(f"Starting generation for {today_str} (JST)...")
    
    # 5. AIによる記事生成（リトライ・JSON抽出処理）
    data = None
    for attempt in range(3):
        try:
            print(f"Attempt {attempt+1}...")
            response = model.generate_content(PROMPT)
            res_text = response.text.strip()
            
            # 文字列からJSON部分を抽出（Markdownタグがあっても対応可能にする）
            start_idx = res_text.find('{')
            end_idx = res_text.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                data = json.loads(res_text[start_idx:end_idx])
                print("Successfully generated and parsed JSON.")
                break
        except Exception as e:
            print(f"Error in attempt {attempt+1}: {e}")
            if "429" in str(e): # クォータ制限の場合は長めに待機
                time.sleep(60)
            else:
                time.sleep(20)
    
    if not data:
        raise Exception("Failed to generate content after all attempts.")

    # 6. データの保存とディレクトリ管理
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

    # 上書き許可ロジック（同日のデータがあれば差し替え）
    history = [e for e in history if e.get('date') != today_str]
    history.insert(0, data)
        
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(history[:100], f, ensure_ascii=False, indent=2)

    # 7. HTMLテンプレートへの反映
    # テンプレートはリポジトリのルート（docsの外）にある前提です
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
        else:
            print(f"Warning: Template {t_name} NOT FOUND.")

if __name__ == "__main__":
    generate()
