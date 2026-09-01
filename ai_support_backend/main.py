import os
from typing import List

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from core.rag_core import get_chatbot_response
from core.response_utils import markdown_to_html_with_buttons, extract_links
from core.security import verify_mobile_api_key

# ==========================================
# تنظیمات عمومی
# ==========================================
# مثال مقدار: "15/minute" یا "100/hour" (طبق فرمت کتابخانه slowapi)
RATE_LIMIT = os.getenv("RATE_LIMIT_PER_MINUTE", "15/minute")

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="AI Support Backend")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS: در پروداکشن allow_origins رو به دامنه واقعی سایتتون محدود کنید،
# نه "*". اپ موبایل نیازی به CORS نداره (فقط مرورگرها این محدودیت رو دارن).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)


# ==========================================
# مدل‌های ورودی/خروجی
# ==========================================
class ChatRequest(BaseModel):
    message: str


class ChatResponseWeb(BaseModel):
    """خروجی فعلی، دقیقاً همون فرمتی که ویجت وردپرس انتظار داره."""
    reply: str


class LinkItem(BaseModel):
    title: str
    url: str


class ChatResponseMobile(BaseModel):
    """
    خروجی ساخت‌یافته برای کلاینت موبایل.
    به‌جای HTML خام، متن Markdown + لیست جدای لینک‌ها رو برمی‌گردونه
    تا اپ اندروید بتونه با UI نیتیو خودش (مثلاً Markwon + دکمه‌های نیتیو) رندرش کنه.
    مستندات کامل این قرارداد در فایل API_CONTRACT.md هست.
    """
    reply_markdown: str
    links: List[LinkItem] = []
    model_used: str
    is_fast_answer: bool


# ==========================================
# Endpoint شماره ۱: وردپرس (بدون تغییر رفتار برای کلاینت فعلی)
# ==========================================
@app.post("/chat", response_model=ChatResponseWeb)
@limiter.limit(RATE_LIMIT)
async def chat_web(request: Request, body: ChatRequest):
    try:
        if not body.message:
            raise HTTPException(status_code=400, detail="Message cannot be empty.")

        result = get_chatbot_response(body.message)
        formatted_reply = markdown_to_html_with_buttons(result["text"])

        return ChatResponseWeb(reply=formatted_reply)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# Endpoint شماره ۲: اپ موبایل (برای آینده — الان فقط آماده‌ست)
# وقتی کد اپ اندروید رو نوشتید، کافیه به همین آدرس POST بزنید:
#   https://chat.bluewaverobotics.ir/chat/mobile
# با هدر:
#   X-App-Key: <همون مقداری که در .env روی MOBILE_APP_API_KEY گذاشتید>
# ==========================================
@app.post(
    "/chat/mobile",
    response_model=ChatResponseMobile,
    dependencies=[Depends(verify_mobile_api_key)],
)
@limiter.limit(RATE_LIMIT)
async def chat_mobile(request: Request, body: ChatRequest):
    try:
        if not body.message:
            raise HTTPException(status_code=400, detail="Message cannot be empty.")

        result = get_chatbot_response(body.message)
        links = extract_links(result["text"])

        return ChatResponseMobile(
            reply_markdown=result["text"],
            links=links,
            model_used=result["model_used"],
            is_fast_answer=result["is_fast_answer"],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# Endpoint سلامت سرور (مفید برای مانیتورینگ و health check)
# ==========================================
@app.get("/health")
async def health_check():
    return {"status": "ok"}
