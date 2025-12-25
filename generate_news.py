import os
import json
import datetime
import google.generativeai as genai
from jinja2 import Template

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-3-flash-preview')

PROMPT = """
Analyze today's top stories from Japan's 5 major newspapers. 
Identify the most common story and write as a witty American columnist "The Crimson Pen".
Requirements:
1. Provide content in BOTH English and Japanese.
2. Content: Comparison of papers, Cultural/Historical context, and Japanese Common Sense.
3. Proverb: Select 1 related Japanese proverb.
4. Glossary: 3 terms with definitions in both languages.

Output ONLY valid JSON:
{
  "title_en": "...", "title_jp": "...",
  "content_en": "...", "content_jp": "...",
  "proverb": {
    "title_en": "...", "title_jp": "...",
    "desc_en": "...", "desc_jp": "..."
  },
  "glossary": [
    {"term_en": "...", "term_jp": "...", "def_en": "...", "def_jp": "..."}
  ]
}
"""

def generate():
    response = model.generate_content(PROMPT)
    res_text = response.text.strip()
    if "```json" in res_text:
        res_text = res_text.split("```json")[1].split("```")[0]
    elif "```" in res_text:
        res_text = res_text.split("```")[1].split("```")[0]
    
    new_entry = json.loads(res_text.strip())
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    new_entry['date'] = date_str

    data_path = 'docs/data.json'
    os.makedirs('docs/articles', exist_ok=True)
    
    history = []
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            history = json.load(f)

    if not any(entry.get('date') == date_str for entry in history):
        history.insert(0, new_entry)
        
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(history[:100], f, ensure_ascii=False, indent=2)

    # テンプレート読み込み
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
