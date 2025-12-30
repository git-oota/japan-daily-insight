import os
import json
import datetime
import time
import google.generativeai as genai
from jinja2 import Template

# API設定
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# プロンプト（日付を強調し、AIに最新情報を探させる）
today_str = datetime.date.today().strftime("%Y-%m-%d")
PROMPT = f"""
Search for and analyze the top news from Japan's 5 major newspapers published on {today_str}.
Write a Nicholas Kristof style column.
Output ONLY valid JSON:
{{
  "title_en": "...", "title_jp": "...",
  "content_en": "...", "content_jp": "...",
  "critique_en": "...", "critique_jp": "...",
  "investment_hint_en": "...", "investment_hint_jp": "...",
  "life_hint_en": "...", "life_hint_jp": "...",
  "proverb": {{"title_en": "...", "title_jp": "...", "desc_en": "...", "desc_jp": "..."}},
  "glossary": [{{"term_en": "...", "term_jp": "...", "def_en": "...", "def_jp": "..."}}]
}}
"""

def generate():
    # ご指定の通り gemini-3-flash-preview で試行
    configs = [
        {"model_name": "gemini-3-flash-preview", "tools": None}, 
        {"model_name": "gemini-3-flash-preview", "tools": [{"google_search_retrieval": {}}]} 
    ]

    new_entry = None
    for config in configs:
        model = genai.GenerativeModel(**config)
        for attempt in range(2): # 各設定で2回リトライ
            try:
                response = model.generate_content(PROMPT)
                res_text = response.text.strip()
                
                # Markdownのコードブロックを除去してJSONのみ抽出
                if "```json" in res_text:
                    res_text = res_text.split("```json")[1].split("```")[0]
                elif "```" in res_text:
                    res_text = res_text.split("```")[1].split("```")[0]
                
                new_entry = json.loads(res_text.strip())
                break
            except Exception as e:
                print(f"Attempt failed with {config['tools']}: {e}")
                time.sleep(30)
        if new_entry: break

    if not new_entry:
        raise Exception("Failed to generate content after multiple attempts with gemini-3-flash-preview.")

    new_entry['date'] = today_str

    # 既存の保存・テンプレート反映ロジック
    data_path = 'docs/data.json'
    os.makedirs('docs/articles', exist_ok=True)
    
    history = []
    if os.path.exists(data_path):
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except: 
            history = []

    # 重複チェックをして先頭に追加
    if not any(entry.get('date') == today_str for entry in history):
        history.insert(0, new_entry)
        
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(history[:100], f, ensure_ascii=False, indent=2)

    # 各テンプレートへの反映
    for t_name, out_name in [('template_article.html', f'docs/articles/{today_str}.html'), ('template_portal.html', 'docs/index.html')]:
        if os.path.exists(t_name):
            with open(t_name, 'r', encoding='utf-8') as f:
                tmpl = Template(f.read())
            with open(out_name, 'w', encoding='utf-8') as f:
                f.write(tmpl.render(items=history, item=new_entry))

if __name__ == "__main__":
    generate()
