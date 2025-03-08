from typing import Dict, List, Optional, Any, Callable
import json
import re
import inspect
import logging
from pydantic import BaseModel, Field, create_model

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FunctionDefinition(BaseModel):
    """Model for function definitions."""
    name: str
    description: str
    parameters: Dict[str, Any] = {}
    required_parameters: List[str] = []

class FunctionCall(BaseModel):
    """Model for function calls."""
    name: str
    arguments: Dict[str, Any] = {}

class FunctionRegistry:
    """Registry for functions that can be called by the LLM."""
    
    def __init__(self):
        """Initialize the function registry."""
        self.functions: Dict[str, Dict[str, Any]] = {}
    
    def register(self, func: Callable, name: Optional[str] = None, description: Optional[str] = None):
        """
        Register a function with the registry.
        
        Args:
            func: The function to register
            name: Optional name for the function (defaults to function name)
            description: Optional description for the function (defaults to docstring)
        """
        # Get function name
        func_name = name or func.__name__
        
        # Get function description
        func_description = description or (func.__doc__ or "").strip()
        
        # Get function signature
        sig = inspect.signature(func)
        
        # Get function parameters
        parameters = {}
        required_parameters = []
        
        for param_name, param in sig.parameters.items():
            # Skip self parameter for methods
            if param_name == "self":
                continue
            
            # Get parameter type and default value
            param_type = param.annotation if param.annotation != inspect.Parameter.empty else Any
            has_default = param.default != inspect.Parameter.empty
            
            # Add to required parameters if no default value
            if not has_default:
                required_parameters.append(param_name)
            
            # Add parameter to parameters dict
            parameters[param_name] = {
                "type": self._get_type_name(param_type),
                "description": "",  # No easy way to get parameter descriptions
            }
            
            # Add default value if available
            if has_default:
                parameters[param_name]["default"] = param.default
        
        # Register the function
        self.functions[func_name] = {
            "function": func,
            "definition": FunctionDefinition(
                name=func_name,
                description=func_description,
                parameters=parameters,
                required_parameters=required_parameters
            )
        }
        
        logger.info(f"Registered function: {func_name}")
        
        return func  # Return the function for use as a decorator
    
    def _get_type_name(self, type_hint: Any) -> str:
        """Get a string representation of a type hint."""
        if type_hint == Any:
            return "any"
        elif type_hint == str:
            return "string"
        elif type_hint == int:
            return "integer"
        elif type_hint == float:
            return "number"
        elif type_hint == bool:
            return "boolean"
        elif type_hint == List[str]:
            return "array of strings"
        elif type_hint == List[int]:
            return "array of integers"
        elif type_hint == Dict[str, Any]:
            return "object"
        else:
            return "any"
    
    def get_function_definitions(self) -> List[Dict[str, Any]]:
        """Get all function definitions in a format suitable for LLM API."""
        return [
            {
                "name": func_data["definition"].name,
                "description": func_data["definition"].description,
                "parameters": {
                    "type": "object",
                    "properties": func_data["definition"].parameters,
                    "required": func_data["definition"].required_parameters
                }
            }
            for func_data in self.functions.values()
        ]
    
    def call_function(self, function_call: FunctionCall) -> Any:
        """
        Call a function by name with arguments.
        
        Args:
            function_call: The function call to execute
            
        Returns:
            The result of the function call
        """
        # Check if function exists
        if function_call.name not in self.functions:
            raise ValueError(f"Function {function_call.name} not found")
        
        # Get function
        func = self.functions[function_call.name]["function"]
        
        # Call function with arguments
        try:
            return func(**function_call.arguments)
        except Exception as e:
            logger.error(f"Error calling function {function_call.name}: {str(e)}")
            raise

    def extract_function_calls(self, text: str) -> List[FunctionCall]:
        """
        Extract function calls from text.
        
        Args:
            text: The text to extract function calls from
            
        Returns:
            A list of function calls
        """
        function_calls = []
        
        # Look for function calls in the format: functionName(arg1="value1", arg2=123)
        pattern = r'(\w+)\((.*?)\)'
        matches = re.finditer(pattern, text)
        
        for match in matches:
            func_name = match.group(1)
            args_str = match.group(2)
            
            # Skip if function doesn't exist
            if func_name not in self.functions:
                continue
            
            # Parse arguments
            args = {}
            if args_str:
                # Split by commas, but not inside quotes or brackets
                arg_pairs = re.findall(r'(\w+)\s*=\s*("[^"]*"|\'[^\']*\'|\{[^}]*\}|\[[^\]]*\]|[^,]+)', args_str)
                for arg_name, arg_value in arg_pairs:
                    # Clean up the value
                    arg_value = arg_value.strip()
                    
                    # Handle strings
                    if (arg_value.startswith('"') and arg_value.endswith('"')) or \
                       (arg_value.startswith("'") and arg_value.endswith("'")):
                        arg_value = arg_value[1:-1]
                    # Handle numbers
                    elif arg_value.isdigit():
                        arg_value = int(arg_value)
                    elif arg_value.replace('.', '', 1).isdigit():
                        arg_value = float(arg_value)
                    # Handle booleans
                    elif arg_value.lower() == 'true':
                        arg_value = True
                    elif arg_value.lower() == 'false':
                        arg_value = False
                    # Handle null/None
                    elif arg_value.lower() in ('none', 'null'):
                        arg_value = None
                    
                    args[arg_name] = arg_value
            
            function_calls.append(FunctionCall(name=func_name, arguments=args))
        
        return function_calls

# Create a global function registry
function_registry = FunctionRegistry()

# Example functions to register
@function_registry.register
def get_weather(location: str, unit: str = "celsius") -> Dict[str, Any]:
    """
    Get the current weather for a location.
    
    Args:
        location: The location to get weather for
        unit: The unit to use (celsius or fahrenheit)
        
    Returns:
        Weather information
    """
    # This is a mock implementation
    return {
        "location": location,
        "temperature": 22 if unit == "celsius" else 72,
        "unit": unit,
        "condition": "sunny",
        "humidity": 50
    }

@function_registry.register
def search_knowledge_base(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search the knowledge base for information.
    
    Args:
        query: The search query
        max_results: Maximum number of results to return
        
    Returns:
        List of search results
    """
    # This is a mock implementation
    return [
        {
            "title": f"Result {i} for {query}",
            "content": f"This is the content of result {i} for query: {query}",
            "relevance": 0.9 - (i * 0.1)
        }
        for i in range(min(max_results, 5))
    ] 