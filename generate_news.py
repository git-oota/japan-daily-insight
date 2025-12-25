import os
import json
import datetime
import google.generativeai as genai
from jinja2 import Template

# API設定
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# モデル名を最新版エイリアスに変更
model = genai.GenerativeModel('gemini-3-flash-preview')

PROMPT = """
Identify today's top story from Japan's 5 major newspapers. 
Write a sophisticated column as "The Crimson Pen".
Include: Comparison, Cultural Context, and a related Japanese Proverb.
Output ONLY valid JSON:
{
  "title": "...", "content": "...",
  "proverb": {"title": "...", "desc": "..."},
  "glossary": [{"term": "...", "def": "..."}]
}
"""

def generate():
    # 安全にコンテンツを生成
    response = model.generate_content(PROMPT)
    
    # JSON抽出のロジックを強化
    res_text = response.text.strip()
    # マークダウンの除去
    if "```json" in res_text:
        res_text = res_text.split("```json")[1].split("```")[0]
    elif "```" in res_text:
        res_text = res_text.split("```")[1].split("```")[0]
    
    new_entry = json.loads(res_text)
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    new_entry['date'] = date_str

    # データの保存処理
    data_path = 'docs/data.json'
    os.makedirs('docs/articles', exist_ok=True)
    
    history = []
    if os.path.exists(data_path):
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            history = []

    # 重複を防いで先頭に追加
    if not any(day.get('date') == date_str for day in history):
        history.insert(0, new_entry)
        
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(history[:100], f, ensure_ascii=False, indent=2)

    # ページ生成
    with open('template_article.html', 'r', encoding='utf-8') as f:
        tmpl_art = Template(f.read())
    with open(f'docs/articles/{date_str}.html', 'w', encoding='utf-8') as f:
        f.write(tmpl_art.render(item=new_entry))

    with open('template_portal.html', 'r', encoding='utf-8') as f:
        tmpl_port = Template(f.read())
    with open('docs/index.html', 'w', encoding='utf-8') as f:
        f.write(tmpl_port.render(items=history))

if __name__ == "__main__":
    generate()
