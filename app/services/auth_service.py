from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

from app.core.database import get_db, get_redis
from app.models.user_models import User, APIKey, TokenData
import redis

# Load environment variables
load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Security schemes
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")
api_key_header = APIKeyHeader(name="X-API-Key")

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time
        
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
) -> User:
    """
    Get the current user from a JWT token.
    
    Args:
        token: JWT token
        db: Database session
        redis_client: Redis client
        
    Returns:
        User object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Check if token is in blacklist
    if redis_client.exists(f"blacklist:{token}"):
        raise credentials_exception
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: Optional[int] = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
        
        token_data = TokenData(user_id=int(user_id), exp=datetime.fromtimestamp(payload.get("exp")))
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == token_data.user_id).first()
    
    if user is None or not user.is_active:
        raise credentials_exception
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get the current active user.
    
    Args:
        current_user: Current user
        
    Returns:
        User object
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_api_key_user(
    api_key: str = Depends(api_key_header),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
) -> User:
    """
    Get the user associated with an API key.
    
    Args:
        api_key: API key
        db: Database session
        redis_client: Redis client
        
    Returns:
        User object
        
    Raises:
        HTTPException: If API key is invalid or user not found
    """
    # Check if API key is cached in Redis
    cached_user_id = redis_client.get(f"api_key:{api_key}")
    
    if cached_user_id:
        user = db.query(User).filter(User.id == int(cached_user_id)).first()
        if user and user.is_active:
            # Update last used timestamp in database (async)
            api_key_obj = db.query(APIKey).filter(APIKey.key == api_key).first()
            if api_key_obj:
                api_key_obj.last_used_at = datetime.utcnow()
                db.commit()
            return user
    
    # If not cached, query the database
    api_key_obj = db.query(APIKey).filter(APIKey.key == api_key, APIKey.is_active == True).first()
    
    if not api_key_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "APIKey"},
        )
    
    # Check if API key is expired
    if api_key_obj.expires_at and api_key_obj.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired",
            headers={"WWW-Authenticate": "APIKey"},
        )
    
    # Update last used timestamp
    api_key_obj.last_used_at = datetime.utcnow()
    db.commit()
    
    # Get the user
    user = db.query(User).filter(User.id == api_key_obj.user_id).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key or inactive user",
            headers={"WWW-Authenticate": "APIKey"},
        )
    
    # Cache the API key in Redis for 1 hour
    redis_client.setex(f"api_key:{api_key}", 3600, str(user.id))
    
    return user

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Authenticate a user with username and password.
    
    Args:
        db: Database session
        username: Username
        password: Plain password
        
    Returns:
        User object if authentication successful, None otherwise
    """
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        return None
    
    if not user.verify_password(password):
        return None
    
    return user

def blacklist_token(token: str, redis_client: redis.Redis, expires_in: int = None) -> None:
    """
    Add a token to the blacklist.
    
    Args:
        token: JWT token
        redis_client: Redis client
        expires_in: Expiration time in seconds
    """
    try:
        # If expiration not provided, decode the token to get its expiration
        if expires_in is None:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            exp = payload.get("exp")
            
            if exp:
                # Calculate remaining time until expiration
                expires_in = max(0, int(exp - datetime.utcnow().timestamp()))
            else:
                # Default to 24 hours if no expiration found
                expires_in = 86400
        
        # Add token to blacklist with expiration
        redis_client.setex(f"blacklist:{token}", expires_in, "1")
    except JWTError:
        # If token is invalid, still blacklist it for 24 hours
        redis_client.setex(f"blacklist:{token}", 86400, "1") 