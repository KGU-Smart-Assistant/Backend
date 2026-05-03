# GEMINI service와의 통신을 담당하는 통로

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.gemini_service import get_gemini_response
from app.services.intent_service import classify_intent

from app.services.map_service import get_map_response
from app.services.call_service import get_phone

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_with_gemini(request: ChatRequest, db: Session = Depends(get_db)):
    user_input = request.message

    intent = classify_intent(user_input)
    
    if intent == "지도":
        reply = get_map_response(user_input, db)
    elif intent == "전화":
        reply = get_phone(user_input, db)
    else:
        reply = get_gemini_response(user_input)

    return ChatResponse(
        reply=reply,
        intent=intent   #프론트에서 이을 부분
    )