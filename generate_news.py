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

# モデル設定
model = genai.GenerativeModel(
    model_name='gemini-3-flash-preview',
    tools=[{'google_search_retrieval': {}}]
)

PROMPT = f"""
Today's date is {today_str}. 
Search for today's top news from Nikkei, Yomiuri, Asahi, and Mainichi.
Select TWO main topics: 1. Social Issue, 2. Investment/Economy.
Rewrite as a Nicholas Kristof-style column for junior high school students.
Output ONLY valid JSON.
"""

def generate():
    data = None
    for attempt in range(3):
        try:
            response = model.generate_content(PROMPT)
            res_text = response.text.strip()
            if "```json" in res_text:
                res_text = res_text.split("```json")[1].split("```")[0]
            data = json.loads(res_text.strip())
            break
        except Exception as e:
            print(f"Error: {e}. Retrying...")
            time.sleep(60)
    
    if not data: return

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

    # 【重要】同じ日の記事があったら一旦削除して、最新のもので作り直す
    history = [entry for entry in history if entry.get('date') != today_str]
    history.insert(0, data)
        
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(history[:100], f, ensure_ascii=False, indent=2)

    # テンプレート反映
    for t_name, out_name in [('template_article.html', f'docs/articles/{today_str}.html'), ('template_portal.html', 'docs/index.html')]:
        if os.path.exists(t_name):
            with open(t_name, 'r', encoding='utf-8') as f:
                tmpl = Template(f.read())
            with open(out_name, 'w', encoding='utf-8') as f:
                f.write(tmpl.render(items=history, item=data))

if __name__ == "__main__":
    generate()
