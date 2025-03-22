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

# Provider selection
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()

# Environment variables with defaults
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "deepseek-r1:1.5b")
DEFAULT_TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
DEFAULT_MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2048"))
DEFAULT_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "60.0"))
DEFAULT_PROMPT_TYPE = os.getenv("DEFAULT_PROMPT_TYPE", "general")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_DEFAULT_MODEL = os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o")

# Anthropic Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1")
ANTHROPIC_DEFAULT_MODEL = os.getenv("ANTHROPIC_DEFAULT_MODEL", "claude-3-opus-20240229")

# Add more provider configurations as needed

# Logger setup
import logging
logger = logging.getLogger(__name__)

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
    Get a response from the selected LLM provider.
    
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
    # Select the appropriate provider handler based on LLM_PROVIDER
    if LLM_PROVIDER == "ollama":
        return await _get_ollama_response(
            prompt, model, system_prompt, temperature, max_tokens,
            conversation_history, prompt_type, context, show_thinking
        )
    elif LLM_PROVIDER == "openai":
        if not OPENAI_API_KEY:
            logger.error("OpenAI API key not provided")
            return {
                "response": "Error: OpenAI API key not configured. Please set OPENAI_API_KEY in environment variables.",
                "thinking_process": None
            }
        return await _get_openai_response(
            prompt, model or OPENAI_DEFAULT_MODEL, system_prompt, temperature, max_tokens,
            conversation_history, prompt_type, context, show_thinking
        )
    elif LLM_PROVIDER == "anthropic":
        if not ANTHROPIC_API_KEY:
            logger.error("Anthropic API key not provided")
            return {
                "response": "Error: Anthropic API key not configured. Please set ANTHROPIC_API_KEY in environment variables.",
                "thinking_process": None
            }
        return await _get_anthropic_response(
            prompt, model or ANTHROPIC_DEFAULT_MODEL, system_prompt, temperature, max_tokens,
            conversation_history, prompt_type, context, show_thinking
        )
    else:
        logger.error(f"Unsupported LLM provider: {LLM_PROVIDER}")
        return {
            "response": f"Error: Unsupported LLM provider: {LLM_PROVIDER}",
            "thinking_process": None
        }

async def _get_ollama_response(
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
    """Implementation for Ollama provider."""
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
    
    # Log the system prompt instead of printing
    logger.debug(f"System prompt: {system_prompt}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json=payload,
                timeout=DEFAULT_TIMEOUT  # Use environment variable for timeout
            )
            
            if response.status_code != 200:
                error_message = f"Error from Ollama API: {response.status_code} - {response.text}"
                logger.error(error_message)
                return {
                    "response": f"Error: {error_message}",
                    "thinking_process": None
                }
            
            response_data = response.json()
            
            # Extract the assistant's message
            if "message" in response_data and "content" in response_data["message"]:
                # Get the raw response
                raw_response = response_data["message"]["content"]
                
                # Log the raw response instead of printing
                logger.debug(f"Raw response from model: {raw_response}")
                
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
        logger.error(error_message)
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
    Stream a response from the LLM using the selected provider.
    
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
    # Select the appropriate provider handler based on LLM_PROVIDER
    if LLM_PROVIDER == "ollama":
        async for chunk in _get_ollama_response_stream(
            prompt, model, system_prompt, temperature, max_tokens,
            conversation_history, prompt_type, context, show_thinking
        ):
            yield chunk
    elif LLM_PROVIDER == "openai":
        if not OPENAI_API_KEY:
            logger.error("OpenAI API key not provided")
            yield {"error": "OpenAI API key not configured. Please set OPENAI_API_KEY in environment variables."}
            return
        async for chunk in _get_openai_response_stream(
            prompt, model or OPENAI_DEFAULT_MODEL, system_prompt, temperature, max_tokens,
            conversation_history, prompt_type, context, show_thinking
        ):
            yield chunk
    elif LLM_PROVIDER == "anthropic":
        if not ANTHROPIC_API_KEY:
            logger.error("Anthropic API key not provided")
            yield {"error": "Anthropic API key not configured. Please set ANTHROPIC_API_KEY in environment variables."}
            return
        async for chunk in _get_anthropic_response_stream(
            prompt, model or ANTHROPIC_DEFAULT_MODEL, system_prompt, temperature, max_tokens,
            conversation_history, prompt_type, context, show_thinking
        ):
            yield chunk
    else:
        logger.error(f"Unsupported LLM provider for streaming: {LLM_PROVIDER}")
        yield {"error": f"Unsupported LLM provider for streaming: {LLM_PROVIDER}"}
        return

async def _get_ollama_response_stream(
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
    """Implementation of streaming for Ollama provider."""
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

async def _get_openai_response(
    prompt: str,
    model: str = OPENAI_DEFAULT_MODEL,
    system_prompt: Optional[str] = None,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    prompt_type: str = DEFAULT_PROMPT_TYPE,
    context: Optional[str] = None,
    show_thinking: bool = False
) -> Dict[str, Optional[str]]:
    """Implementation for OpenAI provider."""
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
    
    # If show_thinking is enabled, modify the system prompt to request thinking steps
    if show_thinking:
        thinking_instruction = """When solving problems or addressing complex questions, please use <think>...</think> tags to show your step-by-step reasoning before providing your final answer."""
        if "content" in messages[0]:
            messages[0]["content"] += "\n\n" + thinking_instruction
    
    # Prepare the request payload
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OPENAI_API_KEY}"
            }
            
            response = await client.post(
                f"{OPENAI_BASE_URL}/chat/completions",
                json=payload,
                headers=headers,
                timeout=DEFAULT_TIMEOUT
            )
            
            if response.status_code != 200:
                error_message = f"Error from OpenAI API: {response.status_code} - {response.text}"
                logger.error(error_message)
                return {
                    "response": f"Error: {error_message}",
                    "thinking_process": None
                }
            
            response_data = response.json()
            
            # Extract the assistant's message
            if "choices" in response_data and len(response_data["choices"]) > 0 and "message" in response_data["choices"][0]:
                message = response_data["choices"][0]["message"]
                raw_response = message.get("content", "")
                
                # Extract thinking process if present
                thinking_content = None
                thinking_match = re.search(r'<think>([\s\S]*?)</think>', raw_response)
                if thinking_match and show_thinking:
                    thinking_content = thinking_match.group(1).strip()
                
                # Clean the response if not showing thinking
                if not show_thinking and thinking_match:
                    raw_response = re.sub(r'<think>[\s\S]*?</think>', '', raw_response).strip()
                
                return {
                    "response": raw_response,
                    "thinking_process": thinking_content
                }
            else:
                return {
                    "response": "Error: Unexpected response format from OpenAI",
                    "thinking_process": None
                }
                
    except Exception as e:
        error_message = f"Error communicating with OpenAI: {str(e)}"
        logger.error(error_message)
        return {
            "response": f"Error: {error_message}",
            "thinking_process": None
        }

async def _get_anthropic_response(
    prompt: str,
    model: str = ANTHROPIC_DEFAULT_MODEL,
    system_prompt: Optional[str] = None,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    prompt_type: str = DEFAULT_PROMPT_TYPE,
    context: Optional[str] = None,
    show_thinking: bool = False
) -> Dict[str, Optional[str]]:
    """Implementation for Anthropic provider."""
    # Prepare the messages
    messages = []
    
    # Handle conversation history for Anthropic format
    anthropic_messages = []
    
    # Add conversation history if provided
    if conversation_history:
        for msg in conversation_history:
            if msg["role"] in ["user", "assistant"]:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
    
    # Use prompt engineering to enhance the user prompt if context is provided
    if context:
        enhanced_prompt = create_chat_prompt(prompt, conversation_history, context)
        user_message = enhanced_prompt
    else:
        user_message = prompt
    
    # Add the latest user message
    anthropic_messages.append({"role": "user", "content": user_message})
    
    # Prepare the request payload for Anthropic
    payload = {
        "model": model,
        "messages": anthropic_messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    # Add system prompt if provided
    if system_prompt:
        payload["system"] = system_prompt
    elif prompt_type:
        payload["system"] = create_system_prompt(prompt_type)
    
    # If show_thinking is enabled, modify the system prompt to request thinking steps
    if show_thinking and "system" in payload:
        thinking_instruction = " When solving problems, please use <think>...</think> tags to show your step-by-step reasoning before providing your final answer."
        payload["system"] += thinking_instruction
    
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "Content-Type": "application/json",
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01"
            }
            
            response = await client.post(
                f"{ANTHROPIC_BASE_URL}/messages",
                json=payload,
                headers=headers,
                timeout=DEFAULT_TIMEOUT
            )
            
            if response.status_code != 200:
                error_message = f"Error from Anthropic API: {response.status_code} - {response.text}"
                logger.error(error_message)
                return {
                    "response": f"Error: {error_message}",
                    "thinking_process": None
                }
            
            response_data = response.json()
            
            # Extract the assistant's message
            if "content" in response_data:
                content_blocks = response_data.get("content", [])
                text_blocks = [block.get("text", "") for block in content_blocks if block.get("type") == "text"]
                raw_response = "".join(text_blocks)
                
                # Extract thinking process if present
                thinking_content = None
                thinking_match = re.search(r'<think>([\s\S]*?)</think>', raw_response)
                if thinking_match and show_thinking:
                    thinking_content = thinking_match.group(1).strip()
                
                # Clean the response if not showing thinking
                if not show_thinking and thinking_match:
                    raw_response = re.sub(r'<think>[\s\S]*?</think>', '', raw_response).strip()
                
                return {
                    "response": raw_response,
                    "thinking_process": thinking_content
                }
            else:
                return {
                    "response": "Error: Unexpected response format from Anthropic",
                    "thinking_process": None
                }
                
    except Exception as e:
        error_message = f"Error communicating with Anthropic: {str(e)}"
        logger.error(error_message)
        return {
            "response": f"Error: {error_message}",
            "thinking_process": None
        } 