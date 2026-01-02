import os
import json
import datetime
import time
from datetime import timedelta, timezone
import google.generativeai as genai
from jinja2 import Template

# API設定
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# 日本時間(JST)を設定
jst = timezone(timedelta(hours=+9), 'JST')
now = datetime.datetime.now(jst)
today_str = now.strftime("%Y-%m-%d")

# モデル設定 (最新の安定版を使用)
model = genai.GenerativeModel(
    model_name='gemini-3-flash-preview',
    tools=[{'google_search_retrieval': {}}]
)

PROMPT = f"""
Today's date is {today_str}. 
Search for the TOP NEWS from Asahi, Yomiuri, Mainichi, Nikkei, and Sankei.
Identify the most significant shared topic (e.g., Earthquake recovery, New Year economy).

Write TWO columns (Social and Investment) in Nicholas Kristof's style.
Structure each as: Title, Content (empathic & deep), Critique, Proverb, and 5-10 Glossary terms.
Target: Junior high school level but intellectual.

Output ONLY a raw JSON object. No preamble, no markdown blocks.
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
    data = None
    for attempt in range(3):
        try:
            # 安全策として検索ありで実行
            response = model.generate_content(PROMPT)
            res_text = response.text.strip()
            
            # JSONの抽出処理を強化
            start_idx = res_text.find('{')
            end_idx = res_text.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                data = json.loads(res_text[start_idx:end_idx])
                break
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            time.sleep(30)
    
    if not data:
        print("Final error: Could not generate valid JSON.")
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

    # 重複削除して先頭に追加
    history = [e for e in history if e.get('date') != today_str]
    history.insert(0, data)
        
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(history[:100], f, ensure_ascii=False, indent=2)

    # テンプレート反映 (ここで index.html を「準備中」から「最新記事」へ上書き)
    for t_name, out_name in [('template_article.html', f'docs/articles/{today_str}.html'), ('template_portal.html', 'docs/index.html')]:
        if os.path.exists(t_name):
            with open(t_name, 'r', encoding='utf-8') as f:
                tmpl = Template(f.read())
            with open(out_name, 'w', encoding='utf-8') as f:
                f.write(tmpl.render(items=history, item=data))

if __name__ == "__main__":
    generate()
