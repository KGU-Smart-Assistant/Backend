from fastapi import APIRouter

from app.api.v1.endpoints import health
from app.api.v1.endpoints import chat, extra # chat 라우터 추가

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
# 라우터 추가
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(extra.router, prefix="/extra", tags=["extra-services"])