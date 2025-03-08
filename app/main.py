from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv

# Import routers
from app.api.routes import chat_router, health_router
from app.api.template_routes import template_router
from app.api.document_routes import document_router

# Import logging
from app.core.logging import RequestLoggingMiddleware, logger

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Surfer API",
    description="A FastAPI backend for a ChatGPT-like application using Ollama",
    version="0.3.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Include routers
app.include_router(chat_router, prefix="/api")
app.include_router(health_router, prefix="/api")
app.include_router(template_router, prefix="/api")
app.include_router(document_router, prefix="/api")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Log when the application starts."""
    logger.info("Surfer API starting up")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Log when the application shuts down."""
    logger.info("Surfer API shutting down")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 