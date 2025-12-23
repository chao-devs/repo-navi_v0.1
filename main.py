from fastapi import FastAPI
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel
from openai import OpenAI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import os,json

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static", html=True), name="static")

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

class Input(BaseModel):
    text : str
    length : int
    faculty : str

client = OpenAI(api_key=api_key)

HUMANITIES_RULE = """
文系レポートとして、以下の流れで見出し構成を作成せよ。
1. 研究背景・問題提起
2. 用語や概念の整理
3. 主要な議論・論点
4. 批判的考察・課題
5. 結論・示唆
"""

SCIENCE_RULE = """
理系レポートとして、以下の流れで見出し構成を作成せよ。
1. 研究対象の定義
2. 理論・仕組みの説明
3. 方法・手法・アプローチ
4. 結果・考察
5. 限界と今後の展望
"""

MIXED_RULE = """
文理融合系レポートとして、以下の流れで見出し構成を作成せよ。
1. 技術・テーマの概要
2. 技術的仕組みや特徴
3. 社会への応用・影響
4. 課題・リスク・倫理的観点
5. 将来展望
"""

@app.post("/structure")
def structure(data:Input):
    if data.length == 500:
        h2_count = 2
        h3_count = 0
        rule_text = "H2は2つ作り、H3は使わないでください。簡潔な構成にしてください。"
    elif data.length == 1000:
        h2_count = 3
        h3_count = 2
        rule_text = "H2は3つ作り、各H2にH3を2つずつ含めてください。"
    elif data.length == 2000:
        h2_count = 4
        h3_count = 2
        rule_text = "H2は4つ作り、各H2にH3を2つずつ含めてください。"

    if data.faculty=="humanities":
        rule = HUMANITIES_RULE
    elif data.faculty=="science":
        rule = SCIENCE_RULE
    else:
        rule = MIXED_RULE
    

    messages = [
        {
            "role": "system",
            "content": (
                "あなたは大学のレポートの構成を考えるアシスタントです。"
                "以下のテーマについて、大学レポート用の見出し構成（H1〜H3）と、"
                "各見出しで書くべき内容を箇条書きで出力してください。\n\n"
                "出力は以下の形式に厳密に従ってください。\n\n"
                "# タイトル\n\n"
                "## H1：見出し\n"
                "- 書く内容\n"
                "- 書く内容\n\n"
                "## H2：見出し\n"
                "- 書く内容\n\n"
                "### H3：見出し\n"
                "- 書く内容\n\n"
                "説明文や前置きは書かず、構成のみを出力してください。\n\n"
                "以下のルールを必ず守ってください。\n"
                "H1 → H2 → H3 の順でのみ出力してください。\n"
                "H2の中にのみH3を含めてください。\n"
                "H3の中にH2やH1を含めないでください。\n"
                "見出し構造を変更・省略しないでください。\n"
                "指定された見出し記号（#, ##, ###）を必ず使用してください。\n"
                "フォーマット例を内容で置き換えず、構造として守ってください。"
                "この見出しフレームの構造・順序・数は絶対に変更しないでください。"
                + rule
            )
        },
        {
            "role": "user",
            "content": (
                f"課題文:{data.text}\n"
                f"{rule_text}"
            )
        }
    ]

    response = client.chat.completions.create(
        model = "gpt-4o-mini",
        messages = messages
    )
    structuring = response.choices[0].message.content

    path = Path("structures.json")
    if path.exists():
        with open(path,"r",encoding="utf-8") as f:
            structures = json.load(f)
    else:
        structures = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_structure = {
        "time":timestamp,
        "text":data.text,
        "structuring":structuring
    }
    structures.append(new_structure)
    with open(path,"w",encoding="utf-8") as f:
        json.dump(structures,f,ensure_ascii=False,indent=2)
        
    return {
        "length" : data.length,
        "structure" : structuring
    }

@app.get("/")
def home():
    return FileResponse("static/index.html")