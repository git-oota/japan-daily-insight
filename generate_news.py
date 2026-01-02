import os
import json
import datetime
import time
from datetime import timedelta, timezone
import google.generativeai as genai
from jinja2 import Template

# 1. API・モデル設定
# 安定性を重視し、最新かつ安定した gemini-1.5-flash を推奨
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    tools=[{'google_search_retrieval': {}}]
)

# 2. 日本時間(JST)の厳密な設定
jst = timezone(timedelta(hours=+9), 'JST')
now = datetime.datetime.now(jst)
today_str = now.strftime("%Y-%m-%d")

# 3. プロンプト設定（Nicholas Kristof風・日英併記）
PROMPT = f"""
Today's date is {today_str}. 
Search for the TOP NEWS from Japan's 5 major newspapers: Asahi, Yomiuri, Mainichi, Nikkei, and Sankei.
Find ONE common significant theme (e.g., economic outlook, social reform, or regional stability).

Write TWO columns (Social and Investment) in the style of Nicholas Kristof.
- Audience: Intellectual US readers and Japanese junior high school students.
- Content: Empathic, historical perspective, and deep analysis.
- Requirement: Provide both English and Japanese text for each section.

Output ONLY a raw JSON object. No markdown, no preamble.
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
    print(f"Starting generation for {today_str}...")
    
    # 4. AIによる記事生成（リトライ・JSON抽出強化）
    data = None
    for attempt in range(3):
        try:
            response = model.generate_content(PROMPT)
            res_text = response.text.strip()
            
            # 文字列からJSON部分のみを抽出
            start_idx = res_text.find('{')
            end_idx = res_text.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                data = json.loads(res_text[start_idx:end_idx])
                print("Successfully generated and parsed JSON.")
                break
            else:
                print(f"JSON marker not found in attempt {attempt+1}.")
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            time.sleep(30)
    
    if not data:
        raise Exception("Failed to generate content after 3 attempts.")

    # 5. データの保存準備
    data['date'] = today_str
    data_path = 'docs/data.json'
    
    # 必要なディレクトリを強制作成
    os.makedirs('docs/articles', exist_ok=True)
    
    history = []
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            try:
                history = json.load(f)
            except:
                history = []

    # 重複削除（上書き許可）
    history = [e for e in history if e.get('date') != today_str]
    history.insert(0, data)
        
    # JSON保存
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(history[:100], f, ensure_ascii=False, indent=2)
    print(f"History updated in {data_path}.")

    # 6. HTMLテンプレート反映（404回避のための強制書き出し）
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
            # テンプレートがない場合はエラーを出して知らせる
            print(f"ERROR: Template {t_name} NOT FOUND in root directory!")
            # 応急処置として最小限のHTMLを作成
            if out_name == 'docs/index.html':
                with open(out_name, 'w', encoding='utf-8') as f:
                    f.write(f"<h1>{today_str} News - Template Missing</h1>")

if __name__ == "__main__":
    try:
        generate()
    except Exception as e:
        print(f"Fatal Error: {e}")
        exit(1)
