from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx
import os
import time
from dotenv import load_dotenv
import re
import json
from fastapi.responses import StreamingResponse

from app.services.llm_service import get_llm_response, get_available_models, get_llm_response_stream
from app.models.chat_models import ChatMessage, ChatResponse, AdvancedChatMessage, FunctionCallingMessage, DocumentChatMessage
from app.core.config import settings
from app.services.prompt_templates import template_manager
from app.services.function_calling import function_registry, FunctionCall
from app.services.document_service import document_processor

# Load environment variables
load_dotenv()

# Create routers
chat_router = APIRouter(tags=["chat"])
health_router = APIRouter(tags=["health"])

# Health check endpoint
@health_router.get("/health")
async def health_check():
    """Check if the API is running and Ollama is accessible."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if response.status_code == 200:
                return {"status": "ok", "ollama": "connected", "models": response.json()}
            else:
                return {"status": "ok", "ollama": "error", "message": "Ollama is not responding correctly"}
    except Exception as e:
        return {"status": "ok", "ollama": "error", "message": str(e)}

# Chat endpoint
@chat_router.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Process a chat message and return a response from the LLM."""
    try:
        start_time = time.time()
        
        # Get response from LLM
        response_data = await get_llm_response(
            prompt=message.prompt, 
            model=message.model or settings.DEFAULT_MODEL,
            system_prompt=message.system_prompt,
            temperature=message.temperature or settings.TEMPERATURE,
            max_tokens=message.max_tokens or settings.MAX_TOKENS,
            conversation_history=message.conversation_history,
            # Add prompt type detection based on content (simple example)
            prompt_type="code" if any(keyword in message.prompt.lower() for keyword in ["code", "function", "program", "script"]) else "general",
            # Pass the show_thinking parameter
            show_thinking=message.show_thinking
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Get the raw response
        raw_response = response_data["response"]
        
        # Check if the response contains thinking tags
        has_thinking_tags = "<think>" in raw_response
        
        # Extract thinking content if present
        thinking_content = None
        if has_thinking_tags:
            # Try to extract all thinking content
            thinking_matches = re.findall(r'<think>([\s\S]*?)</think>', raw_response)
            if thinking_matches:
                thinking_content = '\n'.join(thinking_matches).strip()
        
        # Extract content outside thinking tags
        clean_response = re.sub(r'<think>[\s\S]*?</think>', '', raw_response).strip()
        
        # If there's no content outside thinking tags, extract a coherent response from thinking content
        if not clean_response and thinking_content:
            # Try to extract a conclusion or summary from the thinking content
            conclusion_patterns = [
                r'(?:In conclusion|To summarize|Therefore|Thus|So|Overall|In summary)(.*?)(?:$|\.)',
                r'(?:The answer is|The solution is|The result is|The joke is)(.*?)(?:$|\.)',
                r'(?:Here\'s|Here is)(.*?)(?:$|\.)'
            ]
            
            for pattern in conclusion_patterns:
                conclusion_match = re.search(pattern, thinking_content, re.IGNORECASE | re.DOTALL)
                if conclusion_match:
                    conclusion = conclusion_match.group(0).strip()
                    if len(conclusion) > 20:  # Ensure it's a substantial conclusion
                        clean_response = conclusion
                        break
            
            # If no conclusion found, use the last few sentences
            if not clean_response:
                sentences = re.split(r'(?<=[.!?])\s+', thinking_content)
                if len(sentences) > 3:
                    clean_response = " ".join(sentences[-3:])
                else:
                    clean_response = thinking_content
        
        # If we still don't have a clean response, use the raw response with tags removed
        if not clean_response:
            clean_response = re.sub(r'<think>|</think>', '', raw_response).strip()
        
        # Only include thinking process if explicitly requested
        thinking_process = thinking_content if message.show_thinking else None
        
        # If show_thinking is false, make sure the response doesn't contain thinking tags
        if not message.show_thinking:
            clean_response = re.sub(r'<think>|</think>', '', clean_response).strip()
        
        return ChatResponse(
            response=clean_response,
            thinking_process=thinking_process,
            model=message.model or settings.DEFAULT_MODEL,
            status="success",
            processing_time=processing_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get available models endpoint
@chat_router.get("/models")
async def get_models():
    """Get a list of available models from Ollama."""
    try:
        models = await get_available_models()
        return {"models": models, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Streaming chat endpoint
@chat_router.post("/chat/stream")
async def stream_chat(message: ChatMessage):
    """Process a chat message and stream the response from the LLM."""
    try:
        # Start timing
        start_time = time.time()
        
        # Create a streaming response
        return StreamingResponse(
            stream_llm_response(
                prompt=message.prompt,
                model=message.model or settings.DEFAULT_MODEL,
                system_prompt=message.system_prompt,
                temperature=message.temperature or settings.TEMPERATURE,
                max_tokens=message.max_tokens or settings.MAX_TOKENS,
                conversation_history=message.conversation_history,
                prompt_type="code" if any(keyword in message.prompt.lower() for keyword in ["code", "function", "program", "script"]) else "general",
                show_thinking=message.show_thinking
            ),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def stream_llm_response(
    prompt: str,
    model: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    prompt_type: str = "general",
    show_thinking: bool = False
):
    """Stream the LLM response as Server-Sent Events."""
    try:
        # Get the streaming generator from the LLM service
        async for chunk in get_llm_response_stream(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            conversation_history=conversation_history,
            prompt_type=prompt_type,
            show_thinking=show_thinking
        ):
            # Format as SSE
            yield f"data: {json.dumps(chunk)}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
    finally:
        yield "data: [DONE]\n\n"

# Advanced chat endpoint with template support
@chat_router.post("/chat/advanced", response_model=ChatResponse)
async def advanced_chat(message: AdvancedChatMessage):
    """Process a chat message using a template and return a response from the LLM."""
    try:
        start_time = time.time()
        
        # Get the template if specified
        template_content = None
        if message.template_id:
            try:
                # Prepare variables for template rendering
                variables = {
                    "prompt": message.prompt,
                    "custom_instructions": message.system_prompt or ""
                }
                
                # Add any additional variables from the message
                if message.template_variables:
                    variables.update(message.template_variables)
                
                # Render the template
                template_content = template_manager.render_template(
                    template_id=message.template_id,
                    variables=variables
                )
            except Exception as e:
                print(f"Error rendering template: {str(e)}")
                # Fall back to standard system prompt if template rendering fails
                template_content = None
        
        # Use the rendered template as the system prompt if available
        effective_system_prompt = template_content or message.system_prompt
        
        # Get response from LLM
        response_data = await get_llm_response(
            prompt=message.prompt, 
            model=message.model or settings.DEFAULT_MODEL,
            system_prompt=effective_system_prompt,
            temperature=message.temperature or settings.TEMPERATURE,
            max_tokens=message.max_tokens or settings.MAX_TOKENS,
            conversation_history=message.conversation_history,
            prompt_type=message.prompt_type or "general",
            context=message.context,
            show_thinking=message.show_thinking
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Get the raw response
        raw_response = response_data["response"]
        
        # Check if the response contains thinking tags
        has_thinking_tags = "<think>" in raw_response
        
        # Extract thinking content if present
        thinking_content = None
        if has_thinking_tags:
            # Try to extract all thinking content
            thinking_matches = re.findall(r'<think>([\s\S]*?)</think>', raw_response)
            if thinking_matches:
                thinking_content = '\n'.join(thinking_matches).strip()
        
        # Extract content outside thinking tags
        clean_response = re.sub(r'<think>[\s\S]*?</think>', '', raw_response).strip()
        
        # If there's no content outside thinking tags, extract a coherent response from thinking content
        if not clean_response and thinking_content:
            # Try to extract a conclusion or summary from the thinking content
            conclusion_patterns = [
                r'(?:In conclusion|To summarize|Therefore|Thus|So|Overall|In summary)(.*?)(?:$|\.)',
                r'(?:The answer is|The solution is|The result is|The joke is)(.*?)(?:$|\.)',
                r'(?:Here\'s|Here is)(.*?)(?:$|\.)'
            ]
            
            for pattern in conclusion_patterns:
                conclusion_match = re.search(pattern, thinking_content, re.IGNORECASE | re.DOTALL)
                if conclusion_match:
                    conclusion = conclusion_match.group(0).strip()
                    if len(conclusion) > 20:  # Ensure it's a substantial conclusion
                        clean_response = conclusion
                        break
            
            # If no conclusion found, use the last few sentences
            if not clean_response:
                sentences = re.split(r'(?<=[.!?])\s+', thinking_content)
                if len(sentences) > 3:
                    clean_response = " ".join(sentences[-3:])
                else:
                    clean_response = thinking_content
        
        # If we still don't have a clean response, use the raw response with tags removed
        if not clean_response:
            clean_response = re.sub(r'<think>|</think>', '', raw_response).strip()
        
        # Only include thinking process if explicitly requested
        thinking_process = thinking_content if message.show_thinking else None
        
        # If show_thinking is false, make sure the response doesn't contain thinking tags
        if not message.show_thinking:
            clean_response = re.sub(r'<think>|</think>', '', clean_response).strip()
        
        return ChatResponse(
            response=clean_response,
            thinking_process=thinking_process,
            model=message.model or settings.DEFAULT_MODEL,
            status="success",
            processing_time=processing_time,
            template_id=message.template_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Function calling endpoint
@chat_router.post("/chat/function")
async def function_calling_chat(message: FunctionCallingMessage):
    """Process a chat message with function calling capabilities."""
    try:
        start_time = time.time()
        
        # Get the system prompt
        system_prompt = message.system_prompt or "You are a helpful AI assistant that can call functions to get information. When you need to use a function, format your response like this: functionName(param1=\"value1\", param2=123)"
        
        # Add available functions to the system prompt
        if message.enable_function_calling:
            function_definitions = function_registry.get_function_definitions()
            functions_str = json.dumps(function_definitions, indent=2)
            system_prompt += f"\n\nYou have access to the following functions:\n{functions_str}\n\nWhen you need to use a function, call it directly in your response."
        
        # Get response from LLM
        response_data = await get_llm_response(
            prompt=message.prompt, 
            model=message.model or settings.DEFAULT_MODEL,
            system_prompt=system_prompt,
            temperature=message.temperature or settings.TEMPERATURE,
            max_tokens=message.max_tokens or settings.MAX_TOKENS,
            conversation_history=message.conversation_history,
            show_thinking=message.show_thinking
        )
        
        # Get the raw response
        raw_response = response_data["response"]
        
        # Extract thinking content if present
        thinking_content = None
        if "<think>" in raw_response:
            thinking_matches = re.findall(r'<think>([\s\S]*?)</think>', raw_response)
            if thinking_matches:
                thinking_content = '\n'.join(thinking_matches).strip()
        
        # Extract content outside thinking tags
        clean_response = re.sub(r'<think>[\s\S]*?</think>', '', raw_response).strip()
        
        # Extract function calls from the response
        function_calls = []
        function_results = []
        
        if message.enable_function_calling:
            # Extract function calls
            function_calls = function_registry.extract_function_calls(raw_response)
            
            # Execute function calls if auto_execute is enabled
            if message.auto_execute_functions and function_calls:
                for func_call in function_calls:
                    try:
                        result = function_registry.call_function(func_call)
                        function_results.append({
                            "name": func_call.name,
                            "arguments": func_call.arguments,
                            "result": result,
                            "status": "success"
                        })
                    except Exception as e:
                        function_results.append({
                            "name": func_call.name,
                            "arguments": func_call.arguments,
                            "error": str(e),
                            "status": "error"
                        })
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Return the response
        return {
            "response": clean_response,
            "thinking_process": thinking_content if message.show_thinking else None,
            "model": message.model or settings.DEFAULT_MODEL,
            "status": "success",
            "processing_time": processing_time,
            "function_calls": [fc.dict() for fc in function_calls],
            "function_results": function_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Execute function endpoint
@chat_router.post("/function/execute")
async def execute_function(function_call: FunctionCall):
    """Execute a function call."""
    try:
        result = function_registry.call_function(function_call)
        return {
            "name": function_call.name,
            "arguments": function_call.arguments,
            "result": result,
            "status": "success"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get available functions endpoint
@chat_router.get("/functions")
async def get_functions():
    """Get a list of available functions."""
    try:
        functions = function_registry.get_function_definitions()
        return {"functions": functions, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Document chat endpoint
@chat_router.post("/chat/document", response_model=ChatResponse)
async def document_chat(message: DocumentChatMessage):
    """Process a chat message with document context."""
    try:
        start_time = time.time()
        
        # Get the document
        document_data = document_processor.get_document_by_id(message.document_id)
        if not document_data:
            raise HTTPException(status_code=404, detail=f"Document not found: {message.document_id}")
        
        # Extract text from the document
        extracted_text = document_processor.extract_text_from_document(message.document_id)
        
        # Prepare the system prompt
        default_system_prompt = f"""You are a document assistant. You are given a document to analyze and answer questions about.
        
Document type: {document_data.get('type', 'unknown')}
Document filename: {message.document_id.split('_', 1)[1] if '_' in message.document_id else message.document_id}

When answering questions:
1. Only use information from the provided document.
2. If the answer is not in the document, say so clearly.
3. Provide specific references to parts of the document when possible.
"""
        
        effective_system_prompt = message.system_prompt or default_system_prompt
        
        # Prepare the full prompt with the extracted text if requested
        if message.include_document_content:
            document_context = f"\n\nDocument content:\n{extracted_text}"
            
            # Add custom document prompt if provided
            if message.document_prompt:
                document_context = f"\n\n{message.document_prompt}:\n{extracted_text}"
                
            full_prompt = f"{message.prompt}{document_context}"
        else:
            full_prompt = message.prompt
        
        # Get response from LLM
        response_data = await get_llm_response(
            prompt=full_prompt,
            model=message.model or settings.DEFAULT_MODEL,
            system_prompt=effective_system_prompt,
            temperature=message.temperature or settings.TEMPERATURE,
            max_tokens=message.max_tokens or settings.MAX_TOKENS,
            conversation_history=message.conversation_history,
            show_thinking=message.show_thinking
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Get the raw response
        raw_response = response_data["response"]
        
        # Check if the response contains thinking tags
        has_thinking_tags = "<think>" in raw_response
        
        # Extract thinking content if present
        thinking_content = None
        if has_thinking_tags:
            # Try to extract all thinking content
            thinking_matches = re.findall(r'<think>([\s\S]*?)</think>', raw_response)
            if thinking_matches:
                thinking_content = '\n'.join(thinking_matches).strip()
        
        # Extract content outside thinking tags
        clean_response = re.sub(r'<think>[\s\S]*?</think>', '', raw_response).strip()
        
        # If there's no content outside thinking tags, extract a coherent response from thinking content
        if not clean_response and thinking_content:
            # Try to extract a conclusion or summary from the thinking content
            conclusion_patterns = [
                r'(?:In conclusion|To summarize|Therefore|Thus|So|Overall|In summary)(.*?)(?:$|\.)',
                r'(?:The answer is|The solution is|The result is|The joke is)(.*?)(?:$|\.)',
                r'(?:Here\'s|Here is)(.*?)(?:$|\.)'
            ]
            
            for pattern in conclusion_patterns:
                conclusion_match = re.search(pattern, thinking_content, re.IGNORECASE | re.DOTALL)
                if conclusion_match:
                    conclusion = conclusion_match.group(0).strip()
                    if len(conclusion) > 20:  # Ensure it's a substantial conclusion
                        clean_response = conclusion
                        break
            
            # If no conclusion found, use the last few sentences
            if not clean_response:
                sentences = re.split(r'(?<=[.!?])\s+', thinking_content)
                if len(sentences) > 3:
                    clean_response = " ".join(sentences[-3:])
                else:
                    clean_response = thinking_content
        
        # If we still don't have a clean response, use the raw response with tags removed
        if not clean_response:
            clean_response = re.sub(r'<think>|</think>', '', raw_response).strip()
        
        # Only include thinking process if explicitly requested
        thinking_process = thinking_content if message.show_thinking else None
        
        # If show_thinking is false, make sure the response doesn't contain thinking tags
        if not message.show_thinking:
            clean_response = re.sub(r'<think>|</think>', '', clean_response).strip()
        
        return ChatResponse(
            response=clean_response,
            thinking_process=thinking_process,
            model=message.model or settings.DEFAULT_MODEL,
            status="success",
            processing_time=processing_time,
            document_id=message.document_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 