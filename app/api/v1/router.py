from fastapi import APIRouter

from app.api.v1.endpoints import chat, extra, health, translation

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(extra.router, prefix="/extra", tags=["extra-services"])
api_router.include_router(translation.router, prefix="/translation", tags=["translation"])
