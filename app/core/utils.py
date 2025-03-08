import re
from typing import Dict, List, Optional, Tuple, Any

def extract_code_blocks(text: str) -> List[Dict[str, str]]:
    """
    Extract code blocks from markdown text.
    
    Args:
        text: The markdown text containing code blocks
        
    Returns:
        A list of dictionaries with 'language' and 'code' keys
    """
    # Regular expression to match code blocks
    pattern = r"```(\w*)\n([\s\S]*?)```"
    
    # Find all code blocks
    matches = re.findall(pattern, text)
    
    # Convert matches to dictionaries
    code_blocks = []
    for language, code in matches:
        code_blocks.append({
            "language": language.strip() or "text",
            "code": code.strip()
        })
    
    return code_blocks

def enhance_prompt(prompt: str, context: Optional[str] = None) -> str:
    """
    Enhance the user prompt with additional context or instructions.
    
    Args:
        prompt: The original user prompt
        context: Additional context to include
        
    Returns:
        The enhanced prompt
    """
    if not context:
        return prompt
    
    # Add context to the prompt
    enhanced_prompt = f"Context:\n{context}\n\nQuestion: {prompt}"
    return enhanced_prompt

def format_conversation_history(history: List[Dict[str, str]]) -> str:
    """
    Format conversation history for display.
    
    Args:
        history: List of conversation messages
        
    Returns:
        Formatted conversation history as a string
    """
    formatted = ""
    for message in history:
        role = message.get("role", "unknown")
        content = message.get("content", "")
        
        if role == "user":
            formatted += f"User: {content}\n\n"
        elif role == "assistant":
            formatted += f"Assistant: {content}\n\n"
        elif role == "system":
            formatted += f"System: {content}\n\n"
    
    return formatted.strip()

def clean_response(response: str, show_thinking: bool = False) -> Dict[str, Optional[str]]:
    """
    Clean and format the LLM response.
    
    Args:
        response: The raw LLM response
        show_thinking: Whether to include the model's thinking process in the response
        
    Returns:
        Dictionary with 'response' and 'thinking_process' keys
    """
    # Check if the response is empty or None
    if not response:
        return {
            "response": "I'm sorry, I couldn't generate a proper response. Please try again with a different prompt.",
            "thinking_process": None
        }
    
    # Extract thinking process if present
    thinking_content = None
    thinking_matches = re.findall(r'<think>([\s\S]*?)</think>', response)
    
    if thinking_matches and len(thinking_matches) > 0:
        thinking_content = '\n'.join(thinking_matches).strip()
    
    # Extract content outside of thinking tags for the main response
    clean_response_text = re.sub(r'<think>[\s\S]*?</think>', '', response).strip()
    
    # If there's no content outside thinking tags, try to extract from thinking
    if not clean_response_text and thinking_content:
        # Try to extract a coherent response from the thinking content
        # Look for a conclusion or summary at the end
        conclusion_patterns = [
            r'(?:In conclusion|To summarize|Therefore|Thus|So|Overall|In summary)(.*?)(?:$|\.)',
            r'(?:The algorithm|The steps|The process|The implementation)(.*?)(?:$|\.)',
            r'(?:Here\'s how|Here is how|The way to)(.*?)(?:$|\.)'
        ]
        
        for pattern in conclusion_patterns:
            conclusion_match = re.search(pattern, thinking_content, re.IGNORECASE | re.DOTALL)
            if conclusion_match:
                conclusion = conclusion_match.group(0).strip()
                if len(conclusion) > 30:  # Ensure it's a substantial conclusion
                    clean_response_text = conclusion
                    break
        
        # If no conclusion found, try to extract key information for specific topics
        if not clean_response_text and "binary search" in response.lower():
            algorithm_patterns = [
                r'(?:steps|algorithm|process)[\s\S]*?(?:1\..*?2\..*?3\.)',
                r'(?:initialize|start with)[\s\S]*?(?:while|repeat|until)',
                r'(?:function|def|procedure)[\s\S]*?(?:return|end)'
            ]
            
            for pattern in algorithm_patterns:
                algo_match = re.search(pattern, thinking_content, re.IGNORECASE | re.DOTALL)
                if algo_match:
                    algo_desc = algo_match.group(0).strip()
                    if len(algo_desc) > 50:  # Ensure it's substantial
                        clean_response_text = f"Binary Search Algorithm:\n\n{algo_desc}"
                        break
        
        # If still no good extraction, use the last few sentences
        if not clean_response_text:
            sentences = re.split(r'(?<=[.!?])\s+', thinking_content)
            if len(sentences) > 3:
                clean_response_text = " ".join(sentences[-3:])
            else:
                clean_response_text = thinking_content
    
    # If we still don't have a clean response, use the original
    if not clean_response_text:
        # If the entire response is wrapped in thinking tags, use the original
        clean_response_text = response.strip()
    
    # If the response still contains thinking tags, remove them
    clean_response_text = re.sub(r'<think>[\s\S]*?</think>', '', clean_response_text).strip()
    
    # Format the thinking process for display if show_thinking is True
    formatted_thinking = None
    if show_thinking and thinking_content:
        formatted_thinking = thinking_content
    
    return {
        "response": clean_response_text,
        "thinking_process": formatted_thinking
    } 