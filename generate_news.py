import os
import json
import datetime
import google.generativeai as genai
from jinja2 import Template

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-pro')
PROMPT = "Create a news article about Japan in JSON format. Include title_en, title_jp, content_en, content_jp, trend_en, trend_jp, and a proverb."

def generate():
  response = model.generate_content(PROMPT)
  text = response.text.strip().replace('```json', '').replace('```', '')
  data = json.loads(text)
  data['date'] = datetime.date.today().strftime("%Y-%m-%d")
  with open('template.html', 'r', encoding='utf-8') as f:
    tmpl = Template(f.read())
  os.makedirs('docs', exist_ok=True)
  for lang in ['en', 'jp']:
    path = f"docs/index{'' if lang == 'en' else '_jp'}.html"
    with open(path, 'w', encoding='utf-8') as f:
      f.write(tmpl.render(data=data, lang=lang))

if __name__ == "__main__":
  generate()
