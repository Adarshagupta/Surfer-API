import httpx
import os
import json
import time
import re
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

from app.core.utils import clean_response
from app.services.prompt_engineering import create_system_prompt, create_chat_prompt

# Load environment variables
load_dotenv()

# Environment variables with defaults
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "deepseek-r1:1.5b")
DEFAULT_TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
DEFAULT_MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2048"))
DEFAULT_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "60.0"))
DEFAULT_PROMPT_TYPE = os.getenv("DEFAULT_PROMPT_TYPE", "general")

async def get_llm_response(
    prompt: str,
    model: str = DEFAULT_MODEL,
    system_prompt: Optional[str] = None,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    prompt_type: str = DEFAULT_PROMPT_TYPE,
    context: Optional[str] = None,
    show_thinking: bool = False
) -> Dict[str, Optional[str]]:
    """
    Get a response from the LLM using Ollama.
    
    Args:
        prompt: The user's message
        model: The model to use
        system_prompt: System prompt to guide the model's behavior
        temperature: Temperature for response generation
        max_tokens: Maximum number of tokens to generate
        conversation_history: Previous conversation messages
        prompt_type: Type of prompt (general, code, creative, academic)
        context: Additional context to include
        show_thinking: Whether to include the model's thinking process in the response
        
    Returns:
        Dictionary with 'response' and 'thinking_process' keys
    """
    # Prepare the messages
    messages = []
    
    # Use prompt engineering to create a system prompt if not provided
    if not system_prompt:
        system_prompt = create_system_prompt(prompt_type)
    
    # Add system prompt
    messages.append({"role": "system", "content": system_prompt})
    
    # Add conversation history if provided
    if conversation_history:
        messages.extend(conversation_history)
    
    # Use prompt engineering to enhance the user prompt if context is provided
    if context:
        enhanced_prompt = create_chat_prompt(prompt, conversation_history, context)
        messages.append({"role": "user", "content": enhanced_prompt})
    else:
        messages.append({"role": "user", "content": prompt})
    
    # Prepare the request payload
    payload = {
        "model": model,
        "messages": messages,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens
        },
        "stream": False
    }
    
    # Print the system prompt for debugging
    print(f"System prompt: {system_prompt}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json=payload,
                timeout=DEFAULT_TIMEOUT  # Use environment variable for timeout
            )
            
            if response.status_code != 200:
                error_message = f"Error from Ollama API: {response.status_code} - {response.text}"
                print(error_message)
                return {
                    "response": f"Error: {error_message}",
                    "thinking_process": None
                }
            
            response_data = response.json()
            
            # Extract the assistant's message
            if "message" in response_data and "content" in response_data["message"]:
                # Get the raw response
                raw_response = response_data["message"]["content"]
                
                # Print the raw response for debugging
                print(f"Raw response from model: {raw_response}")
                
                # Extract thinking process if present
                thinking_content = None
                thinking_match = re.search(r'<think>([\s\S]*?)</think>', raw_response)
                if thinking_match and show_thinking:
                    thinking_content = thinking_match.group(1).strip()
                
                return {
                    "response": raw_response,
                    "thinking_process": thinking_content
                }
            else:
                return {
                    "response": "Error: Unexpected response format from Ollama",
                    "thinking_process": None
                }
                
    except Exception as e:
        error_message = f"Error communicating with Ollama: {str(e)}"
        print(error_message)
        return {
            "response": f"Error: {error_message}",
            "thinking_process": None
        }

async def get_available_models():
    """Get a list of available models from Ollama."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if response.status_code == 200:
                return response.json().get("models", [])
            else:
                return []
    except Exception as e:
        print(f"Error fetching models: {str(e)}")
        return []

async def get_llm_response_stream(
    prompt: str,
    model: str = DEFAULT_MODEL,
    system_prompt: Optional[str] = None,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    prompt_type: str = DEFAULT_PROMPT_TYPE,
    context: Optional[str] = None,
    show_thinking: bool = False
):
    """
    Stream a response from the LLM using Ollama.
    
    Args:
        prompt: The user's message
        model: The model to use
        system_prompt: System prompt to guide the model's behavior
        temperature: Temperature for response generation
        max_tokens: Maximum number of tokens to generate
        conversation_history: Previous conversation messages
        prompt_type: Type of prompt (general, code, creative, academic)
        context: Additional context to include
        show_thinking: Whether to include the model's thinking process in the response
        
    Yields:
        Chunks of the response as they are generated
    """
    # Prepare the messages
    messages = []
    
    # Use prompt engineering to create a system prompt if not provided
    if not system_prompt:
        system_prompt = create_system_prompt(prompt_type)
    
    # Add system prompt
    messages.append({"role": "system", "content": system_prompt})
    
    # Add conversation history if provided
    if conversation_history:
        messages.extend(conversation_history)
    
    # Use prompt engineering to enhance the user prompt if context is provided
    if context:
        enhanced_prompt = create_chat_prompt(prompt, conversation_history, context)
        messages.append({"role": "user", "content": enhanced_prompt})
    else:
        messages.append({"role": "user", "content": prompt})
    
    # Prepare the request payload
    payload = {
        "model": model,
        "messages": messages,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens
        },
        "stream": True  # Enable streaming
    }
    
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{OLLAMA_BASE_URL}/api/chat",
                json=payload,
                timeout=DEFAULT_TIMEOUT
            ) as response:
                if response.status_code != 200:
                    error_message = f"Error from Ollama API: {response.status_code}"
                    yield {"error": error_message}
                    return
                
                # Initialize variables to track the response
                full_response = ""
                thinking_content = ""
                in_thinking_block = False
                
                # Process the streaming response
                async for chunk in response.aiter_lines():
                    if not chunk.strip():
                        continue
                    
                    try:
                        chunk_data = json.loads(chunk)
                        if "message" in chunk_data and "content" in chunk_data["message"]:
                            content = chunk_data["message"]["content"]
                            
                            # Update the full response
                            full_response += content
                            
                            # Track thinking content
                            if "<think>" in content:
                                in_thinking_block = True
                            
                            if in_thinking_block:
                                thinking_content += content
                            
                            if "</think>" in content:
                                in_thinking_block = False
                            
                            # Prepare the chunk to yield
                            response_chunk = {
                                "content": content,
                                "full_response": full_response
                            }
                            
                            # Only include thinking process if requested
                            if show_thinking and thinking_content:
                                response_chunk["thinking_process"] = thinking_content
                            
                            yield response_chunk
                    except json.JSONDecodeError:
                        # Skip invalid JSON
                        continue
                    
    except Exception as e:
        error_message = f"Error communicating with Ollama: {str(e)}"
        yield {"error": error_message} 