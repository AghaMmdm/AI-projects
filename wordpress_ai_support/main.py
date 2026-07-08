import markdown
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from rag_core import get_chatbot_response
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI app
app = FastAPI(title="WordPress AI Support API")

# Define request schema
class ChatRequest(BaseModel):
    message: str

# Define response schema
class ChatResponse(BaseModel):
    reply: str

# Helper function to convert markdown and inject button-style links
def process_response(text: str) -> str:
    # 1. Convert Markdown to HTML
    html_text = markdown.markdown(text)
    
    # 2. Regex to find URLs and replace them with HTML buttons
    url_pattern = r'(https?://[^\s<>"]+)'
    button_html = (
        r'<br><a href="\1" target="_blank" '
        r'style="display:inline-block; margin:10px 0; padding:10px 15px; '
        r'background-color:#0073aa; color:#ffffff; border-radius:5px; '
        r'text-decoration:none; font-weight:bold;">View More Information</a><br>'
    )
    return re.sub(url_pattern, button_html, html_text)

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint to receive messages, process with RAG, 
    and format as HTML with buttons.
    """
    try:
        if not request.message:
            raise HTTPException(status_code=400, detail="Message cannot be empty.")

        # Get raw answer from RAG engine
        raw_ai_reply = get_chatbot_response(request.message)
        
        # Format the response
        formatted_reply = process_response(raw_ai_reply)

        return ChatResponse(reply=formatted_reply)

    except Exception as e:
        # Log the error and return a 500 error
        raise HTTPException(status_code=500, detail=str(e))