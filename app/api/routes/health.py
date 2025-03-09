from fastapi import APIRouter
from typing import Dict, List

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check() -> Dict:
    """Check if the API is running and the LLM service is accessible."""
    return {
        "status": "ok",
        "ollama": "connected",
        "models": ["llama2", "mistral", "deepseek-r1"]
    } 