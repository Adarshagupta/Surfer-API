from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user_models import User, TokenData, APIKey
from app.core.config import settings

# Configuration
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a new access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Get the current user from the token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # Check for both 'sub' and 'user_id' to support different token formats
        user_id = payload.get("user_id")
        if user_id is None:
            # Try 'sub' field which is commonly used
            sub = payload.get("sub")
            if sub is None:
                raise credentials_exception
            # Convert to int if it's a string (common in JWT)
            try:
                user_id = int(sub)
            except (ValueError, TypeError):
                user_id = sub
                
        token_data = TokenData(user_id=user_id, exp=payload.get("exp"))
    except JWTError as e:
        print(f"JWT Error: {str(e)}")
        raise credentials_exception
    
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def verify_api_key(api_key: str, db: Session = Depends(get_db)) -> APIKey:
    """Verify an API key and update its last used timestamp."""
    api_key_record = db.query(APIKey).filter(
        APIKey.key == api_key,
        APIKey.is_active == True
    ).first()
    
    if not api_key_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    # Check if the API key has expired
    if api_key_record.expires_at and api_key_record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired"
        )
    
    # Update last used timestamp
    api_key_record.last_used_at = datetime.utcnow()
    db.commit()
    
    return api_key_record 