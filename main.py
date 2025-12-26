import os
import json
from datetime import datetime, timedelta, timezone
import google.generativeai as genai
from jinja2 import Template

# 1. 環境設定
JST = timezone(timedelta(hours=+9), 'JST')
today_str = datetime.now(JST).strftime("%Y-%m-%d")

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# 検索能力が高い 2.0 Flash を推奨 (1.5 Flash でも動作可能)
model = genai.GenerativeModel(
    model_name='gemini-3-flash-preview', 
    tools=[{'google_search_retrieval': {}}]
)

# --- STEP 1: DEEP RESEARCH (事実収集) ---
def perform_research():
    research_prompt = f"""
    Search for today's ({today_str}) news headlines and financial data in Japan.
    Focus on:
    1. The top story on the front pages of Asahi, Yomiuri, Mainichi, Nikkei, and Sankei newspapers.
    2. The latest Nikkei 225 Stock Average price and market summary for today.

    Provide a summary of the facts found. If multiple sources report the same top news, highlight it as the main topic.
    """
    print(f"[{today_str}] Step 1: ニュースと株価をリサーチ中...")
    response = model.generate_content(research_prompt)
    return response.text

# --- STEP 2: COLUMN WRITING (執筆) ---
def write_column(research_data):
    writing_prompt = f"""
    Based on the provided research data, write a column as "The Crimson Pen".
    
    RESEARCH DATA:
    {research_data}

    Requirements:
    1. Target: Junior high school students (Simple & Clear).
    2. Persona: "The Crimson Pen" (Witty, sharp-tongued American columnist).
    3. Output ONLY valid JSON.

    JSON Structure:
    {{
      "title_en": "...", "title_jp": "...",
      "content_en": "...", "content_jp": "...",
      "critique_en": "...", "critique_jp": "...",
      "investment_hint_en": "...", "investment_hint_jp": "...",
      "life_hint_en": "...", "life_hint_jp": "...",
      "proverb": {{"title_en": "...", "title_jp": "...", "desc_en": "...", "desc_jp": "..."}},
      "glossary": [
        {{"term_en": "...", "term_jp": "...", "def_en": "...", "def_jp": "..."}},
        {{"term_en": "...", "term_jp": "...", "def_en": "...", "def_jp": "..."}},
        {{"term_en": "...", "term_jp": "...", "def_en": "...", "def_jp": "..."}},
        {{"term_en": "...", "term_jp": "...", "def_en": "...", "def_jp": "..."}},
        {{"term_en": "...", "term_jp": "...", "def_en": "...", "def_jp": "..."}}
      ]
    }}
    """
    print(f"[{today_str}] Step 2: コラムを執筆中...")
    response = model.generate_content(writing_prompt)
    res_text = response.text.strip()
    
    # JSON抽出
    if "```json" in res_text:
        res_text = res_text.split("```json")[1].split("```")[0]
    elif "```" in res_text:
        res_text = res_text.split("```")[1].split("```")[0]
    
    return json.loads(res_text.strip())

def main():
    try:
        # リサーチと執筆の実行
        facts = perform_research()
        new_entry = write_column(facts)
        new_entry['date'] = today_str

        # ファイル保存処理
        data_path = 'docs/data.json'
        os.makedirs('docs/articles', exist_ok=True)
        
        history = []
        if os.path.exists(data_path):
            with open(data_path, 'r', encoding='utf-8') as f:
                history = json.load(f)

        # 重複削除して先頭に追加
        history = [e for e in history if e.get('date') != today_str]
        history.insert(0, new_entry)
            
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(history[:100], f, ensure_ascii=False, indent=2)

        # テンプレート反映
        for t_name, out_name in [('template_article.html', f'docs/articles/{today_str}.html'), ('template_portal.html', 'docs/index.html')]:
            if os.path.exists(t_name):
                with open(t_name, 'r', encoding='utf-8') as f:
                    tmpl = Template(f.read())
                with open(out_name, 'w', encoding='utf-8') as f:
                    f.write(tmpl.render(items=history, item=new_entry))

        print(f"成功: {today_str} の記事を生成しました。")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
