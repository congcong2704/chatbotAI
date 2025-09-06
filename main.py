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
    results = []
    for art in articles:
        if query.lower() in art["sentence"].lower():
            results.append(art["sentence"])
    if not results:
        results = [art["sentence"] for art in articles[:5]]
    combined = "\n\n".join(results)
    return combined[:max_len]

# ===== Lưu lịch sử hội thoại =====
# Lưu theo session_id nếu muốn nhiều người chat riêng biệt
chat_history = []

@app.post("/api/message")
async def message(req: Request):
    data = await req.json()
    user_msg = data.get("message", "").strip()
    if not user_msg:
        return {"reply": "Xin hãy nhập câu hỏi."}

    # Tìm nội dung liên quan
    context = search_articles(user_msg)

    # Lấy lịch sử hội thoại trước đó
    history_text = ""
    for entry in chat_history[-10:]:  # lấy 10 lượt gần nhất
        history_text += f'Người dùng: {entry["user"]}\nChatbot: {entry["bot"]}\n'

    prompt = f"""
Bạn là trợ lý AI, trả lời người dùng hoàn toàn dựa trên nội dung WATV.org.
Hãy trả lời tiếp theo một cách mạch lạc, dựa trên lịch sử hội thoại trước đó.

Yêu cầu về phong cách:
- Luôn xưng hô "Bạn" với người dùng, dùng giọng điệu thân thiện, lễ phép.
- Viết câu trả lời tự nhiên, gần gũi như đang trò chuyện, tránh khô khan.
- Vẫn phải giữ sự chính xác và không thêm ý kiến cá nhân ngoài dữ liệu.

Lịch sử hội thoại:
{history_text}

Người dùng hỏi tiếp: "{user_msg}"

Dữ liệu liên quan từ WATV.org:
{context}

- Nếu dữ liệu không phải tiếng Việt, hãy dịch sang tiếng Việt trước khi trả lời.
- Trả lời ngắn gọn, rõ ràng, dễ hiểu.
- KHÔNG thêm ý kiến cá nhân, chỉ dùng thông tin trong dữ liệu.
"""


    try:
        response = model.generate_content(prompt)
        reply = response.text
    except Exception as e:
        reply = f"Lỗi gọi Gemini API: {e}"

    # Lưu vào lịch sử
    chat_history.append({"user": user_msg, "bot": reply})

    return {"reply": reply}
