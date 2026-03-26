# GEMINI service와의 통신을 담당하는 통로 
from fastapi import APIRouter
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.gemini_service import get_gemini_response

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_with_gemini(request: ChatRequest):
    reply = get_gemini_response(request.message)
    return ChatResponse(reply=reply)