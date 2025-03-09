from fastapi import FastAPI

def setup_routes(app: FastAPI) -> None:
    """
    Set up all API routes.
    
    Args:
        app: FastAPI application
    """
    # Import routers
    from app.api.routes.auth import router as auth_router
    from app.api.routes.api_keys import router as api_keys_router
    from app.api.routes.users import router as users_router
    from app.api.routes.chat import router as chat_router
    from app.api.routes.health import router as health_router
    from app.api.routes.travel import router as travel_router
    
    # Include routers
    app.include_router(auth_router, prefix="/api")
    app.include_router(api_keys_router, prefix="/api")
    app.include_router(users_router, prefix="/api")
    app.include_router(chat_router, prefix="/api")
    app.include_router(health_router, prefix="/api")
    app.include_router(travel_router, prefix="/api") 