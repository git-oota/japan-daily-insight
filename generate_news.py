import os
import json
import datetime
import time
import google.generativeai as genai
from jinja2 import Template

# API設定
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# モデル設定 (最新ニュース取得のため検索ツールを維持)
model = genai.GenerativeModel(
    model_name='gemini-3-flash-preview',
    tools=[{'google_search_retrieval': {}}]
)

today_str = datetime.date.today().strftime("%Y-%m-%d")

# プロンプトをより簡潔にしてトークン消費を抑える
PROMPT = f"""
Analyze today's ({today_str}) top news from Japan's 5 major newspapers. 
Write an original column in the style of Nicholas Kristof.
Target: Junior high school level.
Include: Simple Summary, Crimson Pen's Critique, Investment/Life Hints, Proverb, and 5 Glossary terms.

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
    # 429エラー対策: 最大3回リトライ
    for attempt in range(3):
        try:
            response = model.generate_content(PROMPT)
            res_text = response.text.strip()
            if "```json" in res_text:
                res_text = res_text.split("```json")[1].split("```")[0]
            new_entry = json.loads(res_text.strip())
            break
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                print(f"Quota exceeded. Waiting 60s... (Attempt {attempt+1})")
                time.sleep(60)
                continue
            raise e

    new_entry['date'] = today_str
    data_path = 'docs/data.json'
    os.makedirs('docs/articles', exist_ok=True)
    
    history = []
    if os.path.exists(data_path):
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except: history = []

    if not any(entry.get('date') == today_str for entry in history):
        history.insert(0, new_entry)
        
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(history[:100], f, ensure_ascii=False, indent=2)

    # テンプレート反映
    for t_name, out_name in [('template_article.html', f'docs/articles/{today_str}.html'), ('template_portal.html', 'docs/index.html')]:
        with open(t_name, 'r', encoding='utf-8') as f:
            tmpl = Template(f.read())
        with open(out_name, 'w', encoding='utf-8') as f:
            f.write(tmpl.render(items=history, item=new_entry))

if __name__ == "__main__":
    generate()
