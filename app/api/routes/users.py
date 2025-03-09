from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.user_models import (
    User, 
    UserUpdate, 
    UserInDB, 
    UsageRecordResponse,
    UsageSummary
)
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me/profile", response_model=UserInDB)
async def get_user_profile(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get current user profile.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User profile
    """
    return current_user

@router.put("/me/profile", response_model=UserInDB)
async def update_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update current user profile.
    
    Args:
        user_data: User update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated user profile
    """
    # Update user fields if provided
    if user_data.email is not None:
        current_user.email = user_data.email
    
    if user_data.username is not None:
        current_user.username = user_data.username
    
    if user_data.full_name is not None:
        current_user.full_name = user_data.full_name
    
    if user_data.password is not None:
        current_user.hashed_password = User.get_password_hash(user_data.password)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user

@router.get("/me/usage", response_model=List[UsageRecordResponse])
async def get_user_usage(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get usage records for the current user.
    
    Args:
        limit: Maximum number of records to return
        offset: Number of records to skip
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of usage records
    """
    from app.models.user_models import UsageRecord
    
    usage_records = db.query(UsageRecord).filter(
        UsageRecord.user_id == current_user.id
    ).order_by(
        UsageRecord.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    return usage_records

@router.get("/me/usage/summary", response_model=UsageSummary)
async def get_user_usage_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get usage summary for the current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Usage summary
    """
    from app.models.user_models import UsageRecord
    
    # Get total requests
    total_requests = db.query(func.count(UsageRecord.id)).filter(
        UsageRecord.user_id == current_user.id
    ).scalar()
    
    # Get total tokens
    total_tokens = db.query(func.sum(UsageRecord.tokens_used)).filter(
        UsageRecord.user_id == current_user.id
    ).scalar() or 0
    
    # Get models used
    models_used = [
        model[0] for model in db.query(UsageRecord.model).filter(
            UsageRecord.user_id == current_user.id,
            UsageRecord.model.isnot(None)
        ).distinct().all()
    ]
    
    # Get endpoints used
    endpoints_used = [
        endpoint[0] for endpoint in db.query(UsageRecord.endpoint).filter(
            UsageRecord.user_id == current_user.id
        ).distinct().all()
    ]
    
    return {
        "total_requests": total_requests,
        "total_tokens": total_tokens,
        "models_used": models_used,
        "endpoints_used": endpoints_used
    } 