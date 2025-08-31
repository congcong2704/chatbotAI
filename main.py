


from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from groq import Groq
import json
import datetime
import re
import unicodedata

app = FastAPI()

# Cho phép frontend (index.html) gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tạo client cho Groq (dùng key thật của bạn)
client = Groq(api_key="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")

# Hàm loại bỏ dấu tiếng Việt
def remove_accents(input_str: str) -> str:
    nfkd_form = unicodedata.normalize("NFKD", input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

@app.post("/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        message = data.get("message", "")

        # Xử lý bỏ dấu để chatbot hiểu tiếng Việt không dấu
        clean_message = remove_accents(message)

        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": clean_message}]
        )

        reply = completion.choices[0].message.content
        return {"reply": reply}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Route để mở file index.html
@app.get("/")
async def serve_index():
    return FileResponse("index.html")
