# main.py
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

# ===== Load dữ liệu WATV =====
with open("watv_all_sentences_vi_filtered.json", "r", encoding="utf-8") as f:
    articles = json.load(f)

def search_articles(query: str, max_len=2000):
    """
    Tìm nội dung liên quan trong articles dựa vào từ khóa.
    """
    results = []
    for art in articles:
        if query.lower() in art["content"].lower():
            results.append(art["content"])
    if not results:
        # fallback: trả về toàn bộ nội dung nếu không tìm thấy match
        results = [art["content"] for art in articles[:5]]
    combined = "\n\n".join(results)
    return combined[:max_len]

@app.post("/api/message")
async def message(req: Request):
    data = await req.json()
    user_msg = data.get("message", "").strip()
    if not user_msg:
        return {"reply": "Xin hãy nhập câu hỏi."}

    # Tìm nội dung liên quan
    context = search_articles(user_msg)

    prompt = f"""
Bạn là trợ lý AI, trả lời người dùng hoàn toàn dựa trên nội dung WATV.org.

Người dùng hỏi: "{user_msg}"

Dữ liệu liên quan từ WATV.org:
{context}

- Nếu dữ liệu không phải tiếng Việt, hãy dịch sang tiếng Việt trước khi trả lời.
- Hãy trả lời ngắn gọn, rõ ràng, dễ hiểu.
- KHÔNG thêm ý kiến cá nhân, chỉ dùng thông tin trong dữ liệu.
"""

    try:
        response = model.generate_content(prompt)
        reply = response.text
    except Exception as e:
        reply = f"Lỗi gọi Gemini API: {e}"

    return {"reply": reply}
