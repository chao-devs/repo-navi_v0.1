from fastapi import FastAPI
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel
from openai import OpenAI
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


load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

class Input(BaseModel):
    text : str

client = OpenAI(api_key=api_key)

@app.post("/structure")
def structure(data:Input):
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
            )
        },
        {
            "role": "user",
            "content": data.text
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
        "data":{
            "structuring":structuring
        },
        "meta":{
            "saved":True
        }
    }