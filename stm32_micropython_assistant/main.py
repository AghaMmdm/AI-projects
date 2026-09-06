"""
FastAPI entry point for the STM32 MicroPython hardware assistant backend.

Unlike the earlier WordPress project, this backend has exactly ONE client
(the Kotlin/Android app), so there is only one endpoint (/chat) instead of
separate web/mobile variants. It's protected by an API key + rate limiting
from the start, since it will be embedded in a public app from day one.
"""

import os
from typing import List

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from core.rag_core import get_chatbot_response
from core.response_utils import extract_links
from core.security import verify_mobile_api_key

# Format follows the slowapi library convention, e.g. "15/minute" or "100/hour"
RATE_LIMIT = os.getenv("RATE_LIMIT_PER_MINUTE", "15/minute")

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="STM32 MicroPython Assistant Backend")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS is mostly irrelevant for a native mobile client (it's a browser-only
# restriction), but kept here in case you ever add a web-based test client.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


class LinkItem(BaseModel):
    title: str
    url: str


class ChatResponse(BaseModel):
    """
    Structured response for the Android client. `reply_markdown` may contain
    fenced ```python code blocks — render it with a Markdown library
    (e.g. Markwon) rather than displaying it as plain text.
    """
    reply_markdown: str
    links: List[LinkItem] = []
    model_used: str
    is_fast_answer: bool


@app.post(
    "/chat",
    response_model=ChatResponse,
    dependencies=[Depends(verify_mobile_api_key)],
)
@limiter.limit(RATE_LIMIT)
async def chat(request: Request, body: ChatRequest):
    try:
        if not body.message:
            raise HTTPException(status_code=400, detail="Message cannot be empty.")

        result = get_chatbot_response(body.message)
        links = extract_links(result["text"])

        return ChatResponse(
            reply_markdown=result["text"],
            links=links,
            model_used=result["model_used"],
            is_fast_answer=result["is_fast_answer"],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Useful for uptime monitoring / load balancer health checks."""
    return {"status": "ok"}
