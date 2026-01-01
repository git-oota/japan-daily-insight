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
            
            # JSONを抽出するための正規表現的な処理を強化
            if "{" in res_text:
                # 最初の '{' から最後の '}' までを抜き出す
                start = res_text.find("{")
                end = res_text.rfind("}") + 1
                json_str = res_text[start:end]
                data = json.loads(json_str)
                break
            else:
                print(f"No JSON found in response. Raw: {res_text[:100]}")
        except Exception as e:
            print(f"Error: {e}. Retrying...")
            time.sleep(60)
            
if __name__ == "__main__":
    generate()
