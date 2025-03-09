from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db, get_redis
from app.models.user_models import User, UserCreate, UserInDB, Token, TokenData
from app.services.auth_service import (
    authenticate_user, 
    create_access_token, 
    get_current_user,
    blacklist_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    oauth2_scheme
)
import redis

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/signup", response_model=UserInDB, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)) -> Any:
    """
    Register a new user.
    
    Args:
        user_data: User creation data
        db: Database session
        
    Returns:
        Newly created user
        
    Raises:
        HTTPException: If username or email already exists
    """
    # Check if username or email already exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = User.get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        is_active=True,
        is_superuser=False
    )
    
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed. Please try again."
        )

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    
    Args:
        form_data: OAuth2 password request form
        db: Database session
        
    Returns:
        Access token and token type
        
    Raises:
        HTTPException: If authentication fails
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, 
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
    redis_client: redis.Redis = Depends(get_redis)
) -> Any:
    """
    Logout a user by blacklisting their token.
    
    Args:
        current_user: Current authenticated user
        token: Current token from Authorization header
        redis_client: Redis client
        
    Returns:
        Success message
    """
    blacklist_token(token, redis_client)
    return {"detail": "Successfully logged out"}

@router.get("/me", response_model=UserInDB)
async def read_users_me(current_user: User = Depends(get_current_user)) -> Any:
    """
    Get current user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user information
    """
    return current_user 