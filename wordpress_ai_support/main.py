import markdown
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from rag_core import get_chatbot_response

# Initialize FastAPI app
app = FastAPI(title="WordPress AI Support API")

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

def process_response(text: str) -> str:
    # 1. Convert Markdown to HTML (فعال کردن افزونه جدول)
    html_text = markdown.markdown(text, extensions=['tables'])
    
    # 2. Regex to find URLs
    url_pattern = r'(?<!href=")(https?://[^\s<>"]+)'
    
    # 3. HTML button template
    button_html = (
        r'<br><a href="\1" target="_blank" '
        r'style="display:inline-block; margin:10px 0; padding:10px 15px; '
        r'background-color:#0073aa; color:#ffffff; border-radius:5px; '
        r'text-decoration:none; font-weight:bold;">مشاهده اطلاعات بیشتر</a><br>'
    )
    
    # Replace only clean URLs
    return re.sub(url_pattern, button_html, html_text)

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        if not request.message:
            raise HTTPException(status_code=400, detail="Message cannot be empty.")

        # Get answer from RAG
        raw_ai_reply = get_chatbot_response(request.message)
        
        # Process and format
        formatted_reply = process_response(raw_ai_reply)

        return ChatResponse(reply=formatted_reply)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))