import os
import json
import datetime
import google.generativeai as genai
from jinja2 import Template

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# リアルタイム検索を有効化
model = genai.GenerativeModel(
    model_name='gemini-3-flash-preview',
    tools=[{'google_search_retrieval': {}}]
)

today_str = datetime.date.today().strftime("%Y-%m-%d")

# 著作権配慮とリライトを徹底したプロンプト
PROMPT = f"""
Search for today's ({today_str}) top news from Japan's major newspapers.
Based on the facts, write a COMPLETELY ORIGINAL column. Do not copy sentences. 

Requirements:
1. Target: Junior high school students (Simple & Clear).
2. Persona: "The Crimson Pen" (A witty, sharp-tongued American columnist).
3. Structure:
   - Original Summary (Rewritten from scratch)
   - The Crimson Pen's Sharp Critique (The core original analysis)
   - Conclusion: Investment Hint & Life Hint
   - Proverb: 1 relevant Japanese proverb
   - Glossary: 5 terms

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
    response = model.generate_content(PROMPT)
    res_text = response.text.strip()
    if "```json" in res_text:
        res_text = res_text.split("```json")[1].split("```")[0]
    
    new_entry = json.loads(res_text.strip())
    new_entry['date'] = today_str

    data_path = 'docs/data.json'
    os.makedirs('docs/articles', exist_ok=True)
    
    history = []
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            history = json.load(f)

    if not any(entry.get('date') == today_str for entry in history):
        history.insert(0, new_entry)
        
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(history[:100], f, ensure_ascii=False, indent=2)

    # テンプレート反映
    for t_name, out_name in [('template_article.html', f'docs/articles/{today_str}.html'), ('template_portal.html', 'docs/index.html')]:
        with open(t_name, 'r', encoding='utf-8') as f:
            tmpl = Template(f.read())
        with open(out_name, 'w', encoding='utf-8') as f:
            if 'portal' in t_name:
                f.write(tmpl.render(items=history))
            else:
                f.write(tmpl.render(item=new_entry))

if __name__ == "__main__":
    generate()
