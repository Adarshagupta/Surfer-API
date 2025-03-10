from fastapi import APIRouter, FastAPI
from app.api.routes import (
    auth,
    users,
    api_keys,
    chat,
    health,
    travel,
    chat_history
)

api_router = APIRouter()

# Add routes
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(api_keys.router, prefix="/api-keys", tags=["api-keys"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(travel.router, prefix="/travel", tags=["travel"])
api_router.include_router(chat_history.router, prefix="/chat", tags=["chat-history"])

def setup_routes(app: FastAPI) -> None:
    """Setup all API routes."""
    app.include_router(api_router, prefix="/api") 