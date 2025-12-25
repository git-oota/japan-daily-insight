import os
import json
import datetime
import google.generativeai as genai
from jinja2 import Template

# API設定
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# ニュース解析プロンプト
PROMPT = """
Analyze today's top stories from Japan's 5 major newspapers (Asahi, Yomiuri, Mainichi, Sankei, Nikkei).
1. Identify the most common TOP story across these papers.
2. Write a sophisticated article as an energetic American columnist (Persona: "The Crimson Pen").
3. Include:
   - Comparison of how different papers reported it.
   - Historical and cultural context.
   - The "Japanese Common Sense" (Joshiki) perspective.
4. Select 1 related Japanese proverb/idiom and explain it.
5. Define 3 key terms for a glossary.

Output ONLY valid JSON:
{
  "title": "...",
  "content": "...",
  "proverb": {"title": "...", "desc": "..."},
  "glossary": [{"term": "...", "def": "..."}]
}
"""

def generate():
    response = model.generate_content(PROMPT)
    text = response.text.strip().replace('```json', '').replace('```', '')
    new_entry = json.loads(text)
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    new_entry['date'] = date_str

    # データの蓄積
    data_path = 'docs/data.json'
    os.makedirs('docs/articles', exist_ok=True)
    
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            history = json.load(f)
    else:
        history = []

    # 重複チェックをして先頭に追加
    if not any(day['date'] == date_str for day in history):
        history.insert(0, new_entry)
        
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(history[:100], f, ensure_ascii=False, indent=2)

    # 1. 個別記事ページの生成
    with open('template_article.html', 'r', encoding='utf-8') as f:
        tmpl_art = Template(f.read())
    with open(f'docs/articles/{date_str}.html', 'w', encoding='utf-8') as f:
        f.write(tmpl_art.render(item=new_entry))

    # 2. トップポータルページの生成
    with open('template_portal.html', 'r', encoding='utf-8') as f:
        tmpl_port = Template(f.read())
    with open('docs/index.html', 'w', encoding='utf-8') as f:
        f.write(tmpl_port.render(items=history))

if __name__ == "__main__":
    generate()
