from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import datetime

from app.core.database import Base

class ChatHistory(Base):
    """SQLAlchemy model for chat history."""
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    model = Column(String)
    tokens_used = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    context_id = Column(Integer, ForeignKey("user_contexts.id"), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="chat_history")
    context = relationship("UserContext", back_populates="chat_history")

class UserContext(Base):
    """SQLAlchemy model for user's contextual learning."""
    __tablename__ = "user_contexts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    context_data = Column(JSON, nullable=False, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="contexts")
    chat_history = relationship("ChatHistory", back_populates="context")

class ChatMessage(BaseModel):
    """Model for incoming chat messages."""
    prompt: str = Field(..., description="The user's message")
    model: Optional[str] = Field(None, description="The model to use for generating a response")
    system_prompt: Optional[str] = Field(
        "You are a helpful AI assistant that provides accurate and concise information.",
        description="System prompt to guide the model's behavior"
    )
    temperature: Optional[float] = Field(None, description="Temperature for response generation (0.0 to 1.0)")
    max_tokens: Optional[int] = Field(None, description="Maximum number of tokens to generate")
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        default=None, 
        description="Previous conversation messages in the format [{'role': 'user', 'content': 'message'}, ...]"
    )
    show_thinking: Optional[bool] = Field(
        False,
        description="Whether to include the model's thinking process in the response"
    )

class AdvancedChatMessage(ChatMessage):
    """Model for advanced chat messages with template support."""
    template_id: Optional[str] = Field(
        None,
        description="ID of the prompt template to use"
    )
    template_variables: Optional[Dict[str, Any]] = Field(
        None,
        description="Variables to use when rendering the template"
    )
    prompt_type: Optional[str] = Field(
        None,
        description="Type of prompt (general, code, creative, academic)"
    )
    context: Optional[str] = Field(
        None,
        description="Additional context to include in the prompt"
    )

class ChatResponse(BaseModel):
    """Model for chat responses."""
    response: str = Field(..., description="The model's response")
    thinking_process: Optional[str] = Field(None, description="The model's thinking process, if requested")
    model: str = Field(..., description="The model used for generating the response")
    status: str = Field(..., description="Status of the request (success or error)")
    processing_time: Optional[float] = Field(None, description="Time taken to process the request in seconds")
    tokens_used: Optional[int] = Field(None, description="Number of tokens used in the request and response")
    template_id: Optional[str] = Field(None, description="ID of the prompt template used, if any")
    document_id: Optional[str] = Field(None, description="ID of the document used, if any")

class FunctionCallingMessage(ChatMessage):
    """Model for chat messages with function calling capabilities."""
    enable_function_calling: bool = Field(
        True,
        description="Whether to enable function calling"
    )
    auto_execute_functions: bool = Field(
        False,
        description="Whether to automatically execute function calls"
    )

class DocumentChatMessage(ChatMessage):
    """Model for chat messages with document context."""
    document_id: str = Field(
        ...,
        description="ID of the document to chat with"
    )
    include_document_content: bool = Field(
        True,
        description="Whether to include the document content in the prompt"
    )
    document_prompt: Optional[str] = Field(
        None,
        description="Custom prompt for document context"
    )

class WebSearchChatMessage(ChatMessage):
    """Model for chat messages with web search capabilities (Perplexity-like)."""
    search_enabled: bool = Field(
        True,
        description="Whether to enable web search for this message"
    )
    num_results: int = Field(
        3,
        description="Number of search results to include"
    )
    include_citations: bool = Field(
        True,
        description="Whether to include citations in the response"
    )
    search_depth: str = Field(
        "basic",
        description="Depth of search: 'basic' (just snippets) or 'deep' (fetch and analyze content)"
    )
    time_limit: Optional[int] = Field(
        None,
        description="Time limit for search in seconds (None for no limit)"
    )

class WebSearchResponse(ChatResponse):
    """Model for web search chat responses with additional fields."""
    search_results: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Search results used to generate the response"
    )
    citations: Optional[List[Dict[str, str]]] = Field(
        None,
        description="Citations for information sources"
    )
    search_query: Optional[str] = Field(
        None,
        description="The search query used"
    )

class VisualElement(BaseModel):
    """Visual element for travel itinerary."""
    type: str = Field(..., description="Type of visual element (image, map, chart)")
    description: str = Field(..., description="Description of what this visual shows")
    source: Optional[str] = Field(None, description="Source URL if applicable")
    map_url: Optional[str] = Field(None, description="URL for map image if type is map")

class DetailedSection(BaseModel):
    """Detailed section for travel itinerary."""
    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content")
    visual_elements: List[VisualElement] = Field(default_factory=list, description="Visual elements for this section")

class TravelItineraryRequest(BaseModel):
    """Request model for travel itinerary generation."""
    destination: str = Field(..., description="Travel destination")
    start_date: str = Field(..., description="Start date of the trip (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date of the trip (YYYY-MM-DD)")
    budget_range: str = Field(..., description="Budget range for the trip (e.g., $2500-5000)")
    interests: List[str] = Field(..., description="List of traveler interests")
    special_requests: Optional[str] = Field(None, description="Any special requests or requirements")

class TravelItineraryResponse(BaseModel):
    """Response model for travel itinerary generation."""
    summary: str = Field(..., description="Summary of the travel itinerary")
    detailed_sections: List[DetailedSection] = Field(..., description="Detailed sections of the itinerary")
    html_template: str = Field(..., description="HTML template for displaying the itinerary")
    processing_time: float = Field(..., description="Time taken to process the request in seconds")

class ComplexTaskRequest(BaseModel):
    """Request model for processing complex tasks."""
    task_description: str = Field(..., description="Detailed description of the task to be performed")
    task_type: str = Field("general", description="Type of task (general, research, comparison, planning, analysis, creative)")
    additional_context: Optional[str] = Field(None, description="Any additional context or information that might help with the task")
    visual_understanding: bool = Field(True, description="Whether to use visual understanding capabilities")
    max_depth: int = Field(2, description="Maximum depth of web page exploration (1-3)")

class ComplexTaskResponse(BaseModel):
    """Response model for complex task processing."""
    summary: str = Field(..., description="Summary of the task results")
    detailed_sections: List[DetailedSection] = Field(..., description="Detailed sections of the response")
    html_template: str = Field(..., description="HTML template for displaying the results")
    task_type: str = Field(..., description="Type of task that was processed")
    processing_time: float = Field(..., description="Time taken to process the request in seconds")

class ChatHistoryBase(BaseModel):
    """Base Pydantic model for chat history."""
    message: str = Field(..., description="The user's message")
    response: str = Field(..., description="The model's response")
    model: Optional[str] = Field(None, description="The model used for the response")
    tokens_used: Optional[int] = Field(None, description="Number of tokens used")
    context_id: Optional[int] = Field(None, description="ID of the associated context")

class ChatHistoryCreate(ChatHistoryBase):
    """Pydantic model for creating chat history entries."""
    user_id: int

class ChatHistoryInDB(ChatHistoryBase):
    """Pydantic model for chat history in database."""
    id: int
    user_id: int
    created_at: datetime.datetime
    
    class Config:
        orm_mode = True

class ChatHistoryResponse(ChatHistoryInDB):
    """Pydantic model for chat history response."""
    pass

class UserContextBase(BaseModel):
    """Base Pydantic model for user context."""
    name: str = Field(..., description="Name of the context")
    description: Optional[str] = Field(None, description="Description of the context")
    context_data: Dict[str, Any] = Field(default_factory=dict, description="Context data")

class UserContextCreate(UserContextBase):
    """Pydantic model for creating user contexts."""
    user_id: int

class UserContextUpdate(BaseModel):
    """Pydantic model for updating user contexts."""
    name: Optional[str] = None
    description: Optional[str] = None
    context_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class UserContextInDB(UserContextBase):
    """Pydantic model for user context in database."""
    id: int
    user_id: int
    is_active: bool
    created_at: datetime.datetime
    updated_at: Optional[datetime.datetime] = None
    
    class Config:
        orm_mode = True

class UserContextResponse(UserContextInDB):
    """Pydantic model for user context response."""
    pass

class ChatWithContextRequest(ChatMessage):
    """Model for chat messages with context."""
    context_id: Optional[int] = Field(None, description="ID of the context to use")
    update_context: bool = Field(True, description="Whether to update the context with this interaction") 