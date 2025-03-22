from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List
from sqlalchemy.orm import Session
from app.models.chat_models import (
    ChatMessage, ChatResponse, AdvancedChatMessage,
    FunctionCallingMessage, DocumentChatMessage,
    WebSearchChatMessage, WebSearchResponse,
    ComplexTaskRequest, ComplexTaskResponse,
    ChatWithContextRequest, ChatHistory, UserContext
)
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user_models import User
from app.services.llm_service import get_llm_response

router = APIRouter(tags=["chat"])

@router.post("/")
async def chat(
    message: ChatMessage,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """Send a message to the LLM and get a response."""
    # Get response from LLM
    llm_response = await get_llm_response(
        prompt=message.prompt,
        model=message.model,
        system_prompt=message.system_prompt,
        temperature=message.temperature,
        max_tokens=message.max_tokens,
        conversation_history=message.conversation_history,
        show_thinking=message.show_thinking
    )
    
    # Save to chat history
    chat_history = ChatHistory(
        user_id=current_user.id,
        message=message.prompt,
        response=llm_response["response"],
        model=message.model,
        tokens_used=llm_response.get("tokens_used")
    )
    db.add(chat_history)
    db.commit()
    
    return ChatResponse(
        response=llm_response["response"],
        thinking_process=llm_response.get("thinking_process"),
        model=message.model or "deepseek-r1:1.5b",
        status="success",
        processing_time=0.5
    )

@router.post("/context")
async def contextual_chat(
    message: ChatWithContextRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """Chat with context management."""
    # Get context if specified
    context = None
    if message.context_id:
        context = db.query(UserContext).filter(
            UserContext.id == message.context_id,
            UserContext.user_id == current_user.id,
            UserContext.is_active == True
        ).first()
        if not context:
            raise HTTPException(status_code=404, detail="Context not found")
    
    # Prepare conversation history with context
    conversation_history = message.conversation_history or []
    if context and context.context_data.get("history"):
        conversation_history = context.context_data["history"] + conversation_history
    
    # Get response from LLM
    llm_response = await get_llm_response(
        prompt=message.prompt,
        model=message.model,
        system_prompt=message.system_prompt,
        temperature=message.temperature,
        max_tokens=message.max_tokens,
        conversation_history=conversation_history,
        show_thinking=message.show_thinking
    )
    
    # Save to chat history
    chat_history = ChatHistory(
        user_id=current_user.id,
        message=message.prompt,
        response=llm_response["response"],
        model=message.model,
        tokens_used=llm_response.get("tokens_used"),
        context_id=message.context_id if context else None
    )
    db.add(chat_history)
    
    # Update context if requested
    if context and message.update_context:
        new_history = conversation_history + [
            {"role": "user", "content": message.prompt},
            {"role": "assistant", "content": llm_response["response"]}
        ]
        context.context_data["history"] = new_history[-10:]  # Keep last 10 messages
        db.add(context)
    
    db.commit()
    
    return ChatResponse(
        response=llm_response["response"],
        thinking_process=llm_response.get("thinking_process"),
        model=message.model or "deepseek-r1:1.5b",
        status="success",
        processing_time=0.5
    )

@router.post("/stream")
async def stream_chat(
    message: ChatMessage,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a message to the LLM and get a streaming response."""
    return {"content": "Placeholder streaming response", "full_response": ""}

@router.post("/advanced")
async def advanced_chat(
    message: AdvancedChatMessage,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """Send a message with template support and additional options."""
    return ChatResponse(
        content="This is a placeholder advanced response",
        model="deepseek-r1:1.5b",
        status="success",
        processing_time=0.5
    )

@router.post("/function")
async def function_chat(
    message: FunctionCallingMessage,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """Chat with function calling capabilities."""
    return ChatResponse(
        content="This is a placeholder function response",
        model="deepseek-r1:1.5b",
        status="success",
        processing_time=0.5
    )

@router.post("/document")
async def document_chat(
    message: DocumentChatMessage,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """Chat with context from a document."""
    return ChatResponse(
        content="This is a placeholder document response",
        model="deepseek-r1:1.5b",
        status="success",
        processing_time=0.5
    )

@router.post("/websearch")
async def websearch_chat(
    message: WebSearchChatMessage,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> WebSearchResponse:
    """Chat with web search capabilities."""
    return WebSearchResponse(
        content="This is a placeholder web search response",
        model="deepseek-r1:1.5b",
        status="success",
        processing_time=0.5,
        search_results=[],
        citations=[]
    )

@router.post("/complex-task")
async def complex_task(
    request: ComplexTaskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ComplexTaskResponse:
    """Process complex tasks using advanced web surfing and visual understanding."""
    return ComplexTaskResponse(
        content="This is a placeholder complex task response",
        status="success",
        processing_time=0.5,
        task_results={},
        visual_elements=[]
    ) 