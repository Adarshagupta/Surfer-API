import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from typing import Optional, List
from datetime import timedelta

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    # API settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Surfer API"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = ["*"]  # For development only
    
    # Authentication settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")  # Change in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    
    # Ollama settings
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "deepseek-r1:1.5b")
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", 2048))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", 0.7))
    
    # Web search settings
    SEARCH_API_KEY: Optional[str] = os.getenv("SEARCH_API_KEY", "")
    SEARCH_ENGINE_ID: Optional[str] = os.getenv("SEARCH_ENGINE_ID", "")
    SERPER_API_KEY: Optional[str] = os.getenv("SERPER_API_KEY", "")
    MAX_SEARCH_RESULTS: int = int(os.getenv("MAX_SEARCH_RESULTS", 5))
    SEARCH_TIMEOUT: int = int(os.getenv("SEARCH_TIMEOUT", 30))
    ENABLE_WEB_SCRAPING: bool = os.getenv("ENABLE_WEB_SCRAPING", "True").lower() == "true"
    
    class Config:
        case_sensitive = True

# Create global settings object
settings = Settings() 