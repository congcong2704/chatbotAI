from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import os, json

app = FastAPI()

# ===== CORS =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Gemini API =====
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("⚠️ Chưa cấu hình GEMINI_API_KEY trong environment variables!")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# ===== Load dữ liệu crawl từ watv.org =====
with open("watv_articles.json", "r", encoding="utf-8") as f:
    articles = json.load(f)

def search_articles(query: str, max_len=2000):
    """
    Tìm nội dung liên quan trong articles dựa vào từ khóa.
    """
    for art in articles:
        if query.lower() in art["content"].lower():
            return art["content"][:max_len]
    return ""

@app.post("/api/message")
async def message(req: Request):
    data = await req.json()
    user = data.get("username")
    msg = data.get("message")

    # Tìm nội dung liên quan từ file JSON
    context = search_articles(msg)

    if not context:
        return {"reply": "Xin lỗi, tôi chưa tìm thấy nội dung liên quan trong dữ liệu WATV."}

    try:
        prompt = f"""
        Người dùng hỏi: "{msg}"
        Đây là tài liệu từ WATV.org:
        {context}
        
        Hãy trả lời ngắn gọn, rõ ràng dựa trên tài liệu WATV.
        """
        response = model.generate_content(prompt)
        reply = response.text
    except Exception as e:
        reply = f"Lỗi gọi Gemini API: {e}"

    return {"reply": reply}
