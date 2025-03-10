from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from dotenv import load_dotenv

# Import routers and setup function
from app.api.routes import setup_routes
from app.api.template_routes import template_router
from app.api.document_routes import document_router
from app.docs import docs_router

# Import logging
from app.core.logging import RequestLoggingMiddleware, logger

# Import database
from app.core.database import engine, Base

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Surfer API",
    description="A FastAPI backend for a ChatGPT-like application with advanced web surfing capabilities",
    version="0.4.0",
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

# Setup routes using the setup function
setup_routes(app)

# Include other routers
app.include_router(template_router, prefix="/api")
app.include_router(document_router, prefix="/api")
app.include_router(docs_router)  # Include the documentation router

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