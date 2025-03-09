from datetime import datetime, timedelta
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user_models import User, APIKey, APIKeyCreate, APIKeyResponse
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api-keys", tags=["api keys"])

@router.post("", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    api_key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new API key for the current user.
    
    Args:
        api_key_data: API key creation data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Newly created API key
    """
    # Generate a new API key
    key = APIKey.generate_key()
    
    # Set expiration date if provided
    expires_at = None
    if api_key_data.expires_at:
        expires_at = api_key_data.expires_at
    
    # Create new API key
    db_api_key = APIKey(
        key=key,
        name=api_key_data.name,
        user_id=current_user.id,
        is_active=True,
        expires_at=expires_at
    )
    
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)
    
    return db_api_key

@router.get("", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    List all API keys for the current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of API keys
    """
    api_keys = db.query(APIKey).filter(
        APIKey.user_id == current_user.id
    ).all()
    
    return api_keys

@router.get("/{api_key_id}", response_model=APIKeyResponse)
async def get_api_key(
    api_key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get a specific API key by ID.
    
    Args:
        api_key_id: API key ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        API key
        
    Raises:
        HTTPException: If API key not found or doesn't belong to user
    """
    api_key = db.query(APIKey).filter(
        APIKey.id == api_key_id,
        APIKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return api_key

@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    api_key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke an API key by ID.
    """
    api_key = db.query(APIKey).filter(
        APIKey.id == api_key_id,
        APIKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    db.delete(api_key)
    db.commit() 