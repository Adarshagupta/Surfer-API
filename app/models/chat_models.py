from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

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