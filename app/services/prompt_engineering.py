from typing import Dict, List, Optional, Any
from app.core.utils import enhance_prompt, format_conversation_history

# Default system prompts for different use cases
DEFAULT_SYSTEM_PROMPTS = {
    "general": """You are a helpful AI assistant that provides accurate and concise information.

IMPORTANT INSTRUCTIONS ABOUT RESPONSE FORMAT:
1. You can use <think>...</think> tags to show your thinking process.
2. AFTER your thinking, you MUST provide a clear, direct answer WITHOUT any thinking tags.
3. Your final answer should appear AFTER the </think> tag.
4. DO NOT put your entire response inside thinking tags.
5. ALWAYS include a response outside of the thinking tags.

Example of correct format:
<think>
Here I analyze the question and think about the answer...
</think>

Here is my clear, direct answer to the question...
""",
    
    "code": """You are a coding assistant. Provide clear, efficient, and well-documented code examples.

IMPORTANT INSTRUCTIONS ABOUT RESPONSE FORMAT:
1. You can use <think>...</think> tags to show your thinking process.
2. AFTER your thinking, you MUST provide a clear, direct answer with code examples WITHOUT any thinking tags.
3. Your final answer should appear AFTER the </think> tag.
4. DO NOT put your entire response inside thinking tags.
5. ALWAYS include a response outside of the thinking tags.

Example of correct format:
<think>
Here I analyze the coding problem and think about the solution...
</think>

Here is my clear solution with code examples:
```python
def example():
    return "code here"
```
""",
    
    "creative": """You are a creative assistant. Think outside the box and provide imaginative responses.

IMPORTANT INSTRUCTIONS ABOUT RESPONSE FORMAT:
1. You can use <think>...</think> tags to show your thinking process.
2. AFTER your thinking, you MUST provide a clear, creative response WITHOUT any thinking tags.
3. Your final answer should appear AFTER the </think> tag.
4. DO NOT put your entire response inside thinking tags.
5. ALWAYS include a response outside of the thinking tags.

Example of correct format:
<think>
Here I explore different creative ideas...
</think>

Here is my creative response to the prompt...
""",
    
    "academic": """You are an academic assistant. Provide well-researched, factual information with citations when possible.

IMPORTANT INSTRUCTIONS ABOUT RESPONSE FORMAT:
1. You can use <think>...</think> tags to show your thinking process.
2. AFTER your thinking, you MUST provide a clear, well-structured academic response WITHOUT any thinking tags.
3. Your final answer should appear AFTER the </think> tag.
4. DO NOT put your entire response inside thinking tags.
5. ALWAYS include a response outside of the thinking tags.

Example of correct format:
<think>
Here I analyze the academic question and consider relevant research...
</think>

Here is my well-structured academic response with citations...
"""
}

def create_system_prompt(prompt_type: str = "general", custom_instructions: Optional[str] = None) -> str:
    """
    Create a system prompt based on the type and custom instructions.
    
    Args:
        prompt_type: The type of system prompt to use
        custom_instructions: Custom instructions to add to the system prompt
        
    Returns:
        The system prompt
    """
    base_prompt = DEFAULT_SYSTEM_PROMPTS.get(prompt_type, DEFAULT_SYSTEM_PROMPTS["general"])
    
    if custom_instructions:
        return f"{base_prompt}\n\n{custom_instructions}"
    
    return base_prompt

def create_chat_prompt(
    user_message: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    context: Optional[str] = None,
    instruction: Optional[str] = None
) -> str:
    """
    Create a chat prompt with conversation history and context.
    
    Args:
        user_message: The user's message
        conversation_history: Previous conversation messages
        context: Additional context to include
        instruction: Specific instruction for the model
        
    Returns:
        The formatted chat prompt
    """
    prompt_parts = []
    
    # Add instruction if provided
    if instruction:
        prompt_parts.append(f"Instruction: {instruction}")
    
    # Add conversation history if provided
    if conversation_history:
        history_text = format_conversation_history(conversation_history)
        prompt_parts.append(f"Previous conversation:\n{history_text}")
    
    # Add context if provided
    if context:
        prompt_parts.append(f"Context:\n{context}")
    
    # Add user message
    prompt_parts.append(f"User message: {user_message}")
    
    # Combine all parts
    return "\n\n".join(prompt_parts)

def create_code_prompt(
    user_query: str,
    language: Optional[str] = None,
    code_context: Optional[str] = None,
    requirements: Optional[List[str]] = None
) -> str:
    """
    Create a prompt for code generation.
    
    Args:
        user_query: The user's query about code
        language: The programming language
        code_context: Existing code context
        requirements: Specific requirements for the code
        
    Returns:
        The formatted code prompt
    """
    prompt_parts = []
    
    # Add language if provided
    if language:
        prompt_parts.append(f"Programming language: {language}")
    
    # Add code context if provided
    if code_context:
        prompt_parts.append(f"Existing code:\n```\n{code_context}\n```")
    
    # Add requirements if provided
    if requirements:
        requirements_text = "\n".join([f"- {req}" for req in requirements])
        prompt_parts.append(f"Requirements:\n{requirements_text}")
    
    # Add user query
    prompt_parts.append(f"Task: {user_query}")
    
    # Add instruction for code format
    prompt_parts.append("Please provide the code solution in a clear, efficient, and well-documented manner.")
    
    # Combine all parts
    return "\n\n".join(prompt_parts) 