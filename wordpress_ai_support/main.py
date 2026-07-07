from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from rag_core import get_chatbot_response
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI app
app = FastAPI(title="WordPress AI Support API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request schema
class ChatRequest(BaseModel):
    message: str

# Define response schema
class ChatResponse(BaseModel):
    reply: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint to receive messages from WordPress and return AI answers.
    """
    try:
        if not request.message:
            raise HTTPException(status_code=400, detail="Message cannot be empty.")
            
        # Get answer from the RAG engine
        ai_reply = get_chatbot_response(request.message)
        
        return ChatResponse(reply=ai_reply)
        
    except Exception as e:
        # In a production environment, log the error properly
        raise HTTPException(status_code=500, detail=str(e))