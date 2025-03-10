from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user_models import User
from app.models.chat_models import (
    ChatHistory, UserContext,
    ChatHistoryCreate, ChatHistoryResponse,
    UserContextCreate, UserContextUpdate, UserContextResponse
)

router = APIRouter()

# Chat History Routes
@router.get("/chat-history", response_model=List[ChatHistoryResponse])
async def get_chat_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    context_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's chat history with optional filtering."""
    query = db.query(ChatHistory).filter(ChatHistory.user_id == current_user.id)
    
    if context_id:
        query = query.filter(ChatHistory.context_id == context_id)
    if start_date:
        query = query.filter(ChatHistory.created_at >= start_date)
    if end_date:
        query = query.filter(ChatHistory.created_at <= end_date)
    
    return query.order_by(ChatHistory.created_at.desc()).offset(skip).limit(limit).all()

@router.delete("/chat-history/{chat_id}")
async def delete_chat_history(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a specific chat history entry."""
    chat = db.query(ChatHistory).filter(
        ChatHistory.id == chat_id,
        ChatHistory.user_id == current_user.id
    ).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat history not found")
    
    db.delete(chat)
    db.commit()
    return {"message": "Chat history deleted successfully"}

# Context Management Routes
@router.post("/contexts", response_model=UserContextResponse)
async def create_context(
    context: UserContextCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new context for the user."""
    db_context = UserContext(
        user_id=current_user.id,
        name=context.name,
        description=context.description,
        context_data=context.context_data
    )
    db.add(db_context)
    db.commit()
    db.refresh(db_context)
    return db_context

@router.get("/contexts", response_model=List[UserContextResponse])
async def get_contexts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's contexts."""
    query = db.query(UserContext).filter(UserContext.user_id == current_user.id)
    if active_only:
        query = query.filter(UserContext.is_active == True)
    return query.order_by(UserContext.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/contexts/{context_id}", response_model=UserContextResponse)
async def get_context(
    context_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific context."""
    context = db.query(UserContext).filter(
        UserContext.id == context_id,
        UserContext.user_id == current_user.id
    ).first()
    
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    
    return context

@router.put("/contexts/{context_id}", response_model=UserContextResponse)
async def update_context(
    context_id: int,
    context_update: UserContextUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a specific context."""
    context = db.query(UserContext).filter(
        UserContext.id == context_id,
        UserContext.user_id == current_user.id
    ).first()
    
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    
    for field, value in context_update.dict(exclude_unset=True).items():
        setattr(context, field, value)
    
    db.commit()
    db.refresh(context)
    return context

@router.delete("/contexts/{context_id}")
async def delete_context(
    context_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a specific context."""
    context = db.query(UserContext).filter(
        UserContext.id == context_id,
        UserContext.user_id == current_user.id
    ).first()
    
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    
    db.delete(context)
    db.commit()
    return {"message": "Context deleted successfully"} 