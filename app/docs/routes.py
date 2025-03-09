"""
Documentation routes for the Surfer API.
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
import json
import httpx
import sys
from typing import Dict, List, Any, Optional
import inspect
import re
from pathlib import Path

from app.api.routes import chat_router, health_router, travel_router
from app.services.llm_service import get_llm_response
from app.services.web_surfing_service import WebSurfingService
from app.models.chat_models import (
    ChatMessage, ChatResponse, AdvancedChatMessage, 
    FunctionCallingMessage, DocumentChatMessage, 
    WebSearchChatMessage, WebSearchResponse, 
    TravelItineraryRequest, TravelItineraryResponse,
    ComplexTaskRequest, ComplexTaskResponse
)

# Create the documentation router
docs_router = APIRouter(tags=["documentation"])

# Set up templates
templates_path = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))

# API endpoint documentation
API_DOCS = {
    "health": {
        "title": "Health Check",
        "description": "Check if the API is running and the LLM service is accessible.",
        "endpoints": [
            {
                "path": "/api/health",
                "method": "GET",
                "summary": "Health Check",
                "description": "Check if the API is running and the LLM service is accessible.",
                "parameters": [],
                "responses": {
                    "200": {
                        "description": "API is running and LLM service is accessible",
                        "content": {
                            "application/json": {
                                "example": {
                                    "status": "ok",
                                    "ollama": "connected",
                                    "models": ["llama2", "mistral", "deepseek-r1"]
                                }
                            }
                        }
                    }
                }
            }
        ]
    },
    "chat": {
        "title": "Chat API",
        "description": "Endpoints for interacting with the LLM in various ways.",
        "endpoints": [
            {
                "path": "/api/chat",
                "method": "POST",
                "summary": "Basic Chat",
                "description": "Send a message to the LLM and get a response.",
                "request_body": "ChatMessage",
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "model": "ChatResponse"
                            }
                        }
                    }
                },
                "example_request": {
                    "prompt": "What is the capital of France?",
                    "model": "deepseek-r1:1.5b",
                    "temperature": 0.7
                }
            },
            {
                "path": "/api/chat/stream",
                "method": "POST",
                "summary": "Streaming Chat",
                "description": "Send a message to the LLM and get a streaming response.",
                "request_body": "ChatMessage",
                "responses": {
                    "200": {
                        "description": "Streaming response",
                        "content": {
                            "application/json": {
                                "example": {
                                    "content": "Partial response content",
                                    "full_response": "Full response so far"
                                }
                            }
                        }
                    }
                },
                "example_request": {
                    "prompt": "Write a short poem about AI.",
                    "model": "deepseek-r1:1.5b",
                    "temperature": 0.8
                }
            },
            {
                "path": "/api/chat/advanced",
                "method": "POST",
                "summary": "Advanced Chat",
                "description": "Send a message with template support and additional options.",
                "request_body": "AdvancedChatMessage",
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "model": "ChatResponse"
                            }
                        }
                    }
                },
                "example_request": {
                    "prompt": "Explain quantum computing",
                    "template_id": "academic_explanation",
                    "prompt_type": "academic",
                    "context": "The user is a college student studying physics."
                }
            },
            {
                "path": "/api/chat/function",
                "method": "POST",
                "summary": "Function Calling Chat",
                "description": "Chat with function calling capabilities.",
                "request_body": "FunctionCallingMessage",
                "responses": {
                    "200": {
                        "description": "Successful response with function calls",
                        "content": {
                            "application/json": {
                                "model": "ChatResponse"
                            }
                        }
                    }
                },
                "example_request": {
                    "prompt": "What's the weather in New York?",
                    "enable_function_calling": True,
                    "auto_execute_functions": True
                }
            },
            {
                "path": "/api/chat/document",
                "method": "POST",
                "summary": "Document Chat",
                "description": "Chat with context from a document.",
                "request_body": "DocumentChatMessage",
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "model": "ChatResponse"
                            }
                        }
                    }
                },
                "example_request": {
                    "prompt": "Summarize the main points of the document",
                    "document_id": "doc_123456",
                    "include_document_content": True
                }
            },
            {
                "path": "/api/chat/websearch",
                "method": "POST",
                "summary": "Web Search Chat",
                "description": "Chat with web search capabilities.",
                "request_body": "WebSearchChatMessage",
                "responses": {
                    "200": {
                        "description": "Successful response with search results",
                        "content": {
                            "application/json": {
                                "model": "WebSearchResponse"
                            }
                        }
                    }
                },
                "example_request": {
                    "prompt": "What are the latest developments in fusion energy?",
                    "search_enabled": True,
                    "num_results": 5,
                    "include_citations": True
                }
            },
            {
                "path": "/api/chat/complex-task",
                "method": "POST",
                "summary": "Complex Task Processing",
                "description": "Process complex tasks using advanced web surfing and visual understanding.",
                "request_body": "ComplexTaskRequest",
                "responses": {
                    "200": {
                        "description": "Successful response with processed task results",
                        "content": {
                            "application/json": {
                                "model": "ComplexTaskResponse"
                            }
                        }
                    }
                },
                "example_request": {
                    "task_description": "Compare the top 5 electric vehicles in 2023 based on range, price, and features.",
                    "task_type": "comparison",
                    "visual_understanding": True,
                    "max_depth": 2
                }
            }
        ]
    },
    "travel": {
        "title": "Travel API",
        "description": "Endpoints for travel-related services.",
        "endpoints": [
            {
                "path": "/api/travel/itinerary",
                "method": "POST",
                "summary": "Generate Travel Itinerary",
                "description": "Generate a detailed travel itinerary with real-time data.",
                "request_body": "TravelItineraryRequest",
                "responses": {
                    "200": {
                        "description": "Successful response with travel itinerary",
                        "content": {
                            "application/json": {
                                "model": "TravelItineraryResponse"
                            }
                        }
                    }
                },
                "example_request": {
                    "destination": "Japan",
                    "start_date": "2023-04-15",
                    "end_date": "2023-04-23",
                    "budget_range": "$2500-5000",
                    "interests": ["historical sites", "hidden gems", "Japanese culture"],
                    "special_requests": "Looking for a special location for a proposal"
                }
            }
        ]
    }
}

# Tutorials
TUTORIALS = [
    {
        "id": "getting-started",
        "title": "Getting Started",
        "description": "Learn how to set up and start using the Surfer API.",
        "content": """
# Getting Started with Surfer API

This tutorial will guide you through the process of setting up and using the Surfer API.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Basic knowledge of REST APIs

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/Surfer-API.git
   cd Surfer-API
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Copy `.env.template` to `.env`
   - Edit `.env` to configure your LLM providers and API keys

5. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```

6. Access the API at `http://localhost:8000`

## Basic Usage

### Making a Simple Chat Request

```python
import requests

response = requests.post(
    "http://localhost:8000/api/chat",
    json={
        "prompt": "What is the capital of France?",
        "model": "deepseek-r1:1.5b",
        "temperature": 0.7
    }
)

print(response.json())
```

### Using Streaming Responses

```python
import requests

response = requests.post(
    "http://localhost:8000/api/chat/stream",
    json={
        "prompt": "Write a short poem about AI.",
        "model": "deepseek-r1:1.5b"
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
```

## Next Steps

- Check out the [API Documentation](/docs/api) for detailed information about all available endpoints
- Explore the [Tutorials](/docs/tutorials) for more advanced usage examples
- Try the [API Tester](/docs/tester) to experiment with different API calls
"""
    },
    {
        "id": "thinking-process",
        "title": "Using the Thinking Process Feature",
        "description": "Learn how to use the 'show_thinking' parameter to see the LLM's reasoning process.",
        "content": """
# Using the Thinking Process Feature

The Surfer API includes a powerful feature that allows you to see the LLM's reasoning process as it generates a response. This tutorial explains how to use the "thinking process" feature and how it can help you understand and improve your AI interactions.

## What is the Thinking Process?

The thinking process is a step-by-step breakdown of how the LLM approaches a problem or question. It reveals:

- The model's reasoning steps
- Assumptions it's making
- Information it's considering
- How it arrives at its conclusions

This is similar to the "chain-of-thought" or "reasoning" techniques in AI research, but made accessible through a simple API parameter.

## How to Enable the Thinking Process

To enable the thinking process in your API calls, simply set the `show_thinking` parameter to `true` in your request:

```python
import requests

response = requests.post(
    "http://localhost:8000/api/chat",
    json={
        "prompt": "Solve this math problem: If a train travels at 120 km/h and another train travels at 80 km/h in the opposite direction, how long will it take for them to be 500 km apart if they start 100 km apart?",
        "model": "deepseek-r1:1.5b",
        "show_thinking": True
    }
)

result = response.json()
print("Response:", result["response"])
print("\nThinking Process:", result["thinking_process"])
```

## Example Output

When you enable the thinking process, the response will include both the final answer and the thinking process that led to it:

```json
{
  "response": "The trains will be 500 km apart after 2.5 hours.",
  "thinking_process": "To solve this problem, I need to find how long it takes for the trains to be 500 km apart when they start 100 km apart.\n\nFirst, let me identify what I know:\n- Train A travels at 120 km/h\n- Train B travels at 80 km/h in the opposite direction\n- They start 100 km apart\n- I need to find when they'll be 500 km apart\n\nSince they're traveling in opposite directions, their relative speed is the sum of their individual speeds:\n120 km/h + 80 km/h = 200 km/h\n\nThey need to increase their distance from 100 km to 500 km, so they need to add 400 km of separation.\n\nTime = Distance ÷ Speed\nTime = 400 km ÷ 200 km/h\nTime = 2 hours\n\nWait, I need to double-check this. After 2 hours:\n- Train A travels: 120 km/h × 2 h = 240 km\n- Train B travels: 80 km/h × 2 h = 160 km\n- Total distance covered: 240 km + 160 km = 400 km\n- Initial separation: 100 km\n- Final separation: 100 km + 400 km = 500 km\n\nSo the trains will be 500 km apart after 2 hours.",
  "model": "deepseek-r1:1.5b",
  "status": "success",
  "processing_time": 1.25
}
```

## How the Thinking Process Works

Behind the scenes, the Surfer API instructs the LLM to include its reasoning process using special tags. The model is prompted to:

1. Think through the problem step-by-step within `<think>...</think>` tags
2. Provide a concise final answer outside these tags
3. The API then extracts and separates these components for you

## Benefits of Using the Thinking Process

### 1. Debugging and Verification

The thinking process helps you verify that the model is approaching problems correctly. If the final answer seems incorrect, you can examine the reasoning to find where the model might have made a mistake.

### 2. Educational Value

For complex topics, seeing the step-by-step reasoning can be educational, helping users understand how to approach similar problems.

### 3. Transparency

Increases trust by making the AI's reasoning transparent rather than presenting answers as if from a black box.

### 4. Improved Prompting

By seeing how the model interprets and reasons about your prompts, you can refine them to get better results.

## Advanced Usage: Streaming with Thinking Process

You can also use the thinking process with streaming responses:

```python
import requests
import json

response = requests.post(
    "http://localhost:8000/api/chat/stream",
    json={
        "prompt": "Explain how photosynthesis works.",
        "model": "deepseek-r1:1.5b",
        "show_thinking": True
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        chunk = json.loads(line.decode('utf-8'))
        if "thinking_process" in chunk:
            print("\nThinking:", chunk["thinking_process"])
        if "content" in chunk:
            print("Response:", chunk["content"])
```

## Best Practices

1. **Use Selectively**: The thinking process can make responses more verbose, so use it when you need insight into the reasoning, not for every request.

2. **Complex Problems**: It's most useful for complex reasoning tasks like math problems, logical puzzles, or multi-step analyses.

3. **Educational Settings**: Great for educational contexts where the process is as important as the answer.

4. **Debugging**: Use it when responses seem incorrect or inconsistent to understand why.

## Technical Details

The thinking process is implemented using a special prompt engineering technique that instructs the model to:

```
<think>
[Detailed reasoning process goes here]
</think>

[Final concise answer here]
```

The API then parses this format to separate the thinking process from the final response.

## Limitations

- Not all models support the thinking process equally well
- Very complex problems might exceed token limits
- The thinking process is the model's own reasoning, which may still contain errors

## Conclusion

The thinking process feature provides a window into the LLM's reasoning, making AI interactions more transparent, educational, and easier to debug. By enabling this feature when appropriate, you can gain deeper insights into how the model approaches problems and generates responses.
"""
    },
    {
        "id": "advanced-chat",
        "title": "Advanced Chat Features",
        "description": "Learn how to use advanced chat features like templates, function calling, and more.",
        "content": """
# Advanced Chat Features

This tutorial covers the advanced chat features available in the Surfer API.

## Using Templates

Templates allow you to create predefined prompts with placeholders for variables.

```python
import requests

response = requests.post(
    "http://localhost:8000/api/chat/advanced",
    json={
        "prompt": "Explain quantum computing",
        "template_id": "academic_explanation",
        "template_variables": {
            "topic": "quantum computing",
            "audience": "undergraduate students"
        },
        "prompt_type": "academic"
    }
)

print(response.json())
```

## Function Calling

Function calling allows the LLM to call predefined functions to perform actions.

```python
import requests

response = requests.post(
    "http://localhost:8000/api/chat/function",
    json={
        "prompt": "What's the weather in New York?",
        "enable_function_calling": True,
        "auto_execute_functions": True
    }
)

print(response.json())
```

## Document Chat

Chat with context from a document.

```python
import requests

# First, upload a document
with open("document.pdf", "rb") as f:
    upload_response = requests.post(
        "http://localhost:8000/api/documents/upload",
        files={"file": f}
    )
    document_id = upload_response.json()["document_id"]

# Then, chat with the document
response = requests.post(
    "http://localhost:8000/api/chat/document",
    json={
        "prompt": "Summarize the main points of the document",
        "document_id": document_id,
        "include_document_content": True
    }
)

print(response.json())
```

## Web Search Chat

Chat with web search capabilities.

```python
import requests

response = requests.post(
    "http://localhost:8000/api/chat/websearch",
    json={
        "prompt": "What are the latest developments in fusion energy?",
        "search_enabled": True,
        "num_results": 5,
        "include_citations": True
    }
)

print(response.json())
```

## Complex Task Processing

Process complex tasks using advanced web surfing and visual understanding.

```python
import requests

response = requests.post(
    "http://localhost:8000/api/chat/complex-task",
    json={
        "task_description": "Compare the top 5 electric vehicles in 2023 based on range, price, and features.",
        "task_type": "comparison",
        "visual_understanding": True,
        "max_depth": 2
    }
)

print(response.json())
```
"""
    },
    {
        "id": "travel-itinerary",
        "title": "Creating Travel Itineraries",
        "description": "Learn how to use the travel itinerary generation feature.",
        "content": """
# Creating Travel Itineraries

This tutorial shows you how to use the travel itinerary generation feature of the Surfer API.

## Basic Itinerary Generation

```python
import requests

response = requests.post(
    "http://localhost:8000/api/travel/itinerary",
    json={
        "destination": "Japan",
        "start_date": "2023-04-15",
        "end_date": "2023-04-23",
        "budget_range": "$2500-5000",
        "interests": ["historical sites", "hidden gems", "Japanese culture"],
        "special_requests": "Looking for a special location for a proposal"
    }
)

itinerary = response.json()
print(itinerary["summary"])

# Display the HTML itinerary
with open("itinerary.html", "w") as f:
    f.write(itinerary["html_template"])
```

## Customizing the Itinerary

You can customize the itinerary by providing more specific interests and special requests.

```python
import requests

response = requests.post(
    "http://localhost:8000/api/travel/itinerary",
    json={
        "destination": "Italy",
        "start_date": "2023-06-10",
        "end_date": "2023-06-20",
        "budget_range": "$3000-6000",
        "interests": [
            "Renaissance art",
            "Italian cuisine",
            "Wine tasting",
            "Ancient ruins",
            "Coastal villages"
        ],
        "special_requests": "We prefer boutique hotels and would like to avoid tourist traps. We're also interested in cooking classes and local experiences."
    }
)

itinerary = response.json()
print(itinerary["summary"])

# Access detailed sections
for section in itinerary["detailed_sections"]:
    print(f"\n## {section['title']}\n")
    print(section["content"])
    
    # Check for visual elements
    if section["visual_elements"]:
        print("\nVisual elements:")
        for visual in section["visual_elements"]:
            print(f"- {visual['type']}: {visual['description']}")
```

## Rendering the Itinerary

The API provides an HTML template that you can use to display the itinerary. You can also customize this template to match your application's design.

```python
import requests
import webbrowser
import tempfile
import os

response = requests.post(
    "http://localhost:8000/api/travel/itinerary",
    json={
        "destination": "France",
        "start_date": "2023-07-15",
        "end_date": "2023-07-25",
        "budget_range": "$4000-7000",
        "interests": ["art", "cuisine", "history", "wine"],
        "special_requests": "We're celebrating our 10th anniversary."
    }
)

itinerary = response.json()

# Create a temporary HTML file
with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as f:
    f.write(itinerary["html_template"].encode('utf-8'))
    temp_path = f.name

# Open the HTML file in the default browser
webbrowser.open('file://' + os.path.realpath(temp_path))
```
"""
    },
    {
        "id": "environment-setup",
        "title": "Environment Configuration",
        "description": "Learn how to configure the environment variables for different LLM providers.",
        "content": """
# Environment Configuration

This tutorial explains how to configure the environment variables for different LLM providers.

## Overview

The Surfer API supports multiple LLM providers:

- Ollama (local)
- OpenAI
- Anthropic
- Replicate
- Deepseek
- Amazon Bedrock
- Custom LLM endpoints

## Configuration File

The configuration is stored in the `.env` file. You can copy the `.env.template` file and modify it according to your needs.

```bash
cp .env.template .env
```

## Basic Configuration

```
# LLM Provider Selection
# Options: ollama, openai, anthropic, replicate, deepseek, bedrock, custom
DEFAULT_LLM_PROVIDER=ollama

# Default LLM Settings (used across providers)
TEMPERATURE=0.7
MAX_TOKENS=2048
REQUEST_TIMEOUT=60.0
DEFAULT_PROMPT_TYPE=general
```

## Ollama Configuration

For local LLM deployment using Ollama:

```
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=deepseek-r1:1.5b
```

## OpenAI Configuration

```
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_DEFAULT_MODEL=gpt-4o
OPENAI_API_BASE=https://api.openai.com/v1
```

## Anthropic Configuration

```
# Anthropic Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key
ANTHROPIC_DEFAULT_MODEL=claude-3-opus-20240229
ANTHROPIC_API_BASE=https://api.anthropic.com/v1
```

## Replicate Configuration

```
# Replicate Configuration
REPLICATE_API_KEY=your_replicate_api_key
REPLICATE_DEFAULT_MODEL=meta/llama-3-70b-instruct:2a30680ab9b12307db19bce8c7e74da618c76c9eba31db02e4b3088d9e9ee5b2
REPLICATE_API_BASE=https://api.replicate.com/v1
```

## Deepseek Configuration

```
# Deepseek Configuration
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_DEFAULT_MODEL=deepseek-chat
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
```

## Amazon Bedrock Configuration

```
# Amazon Bedrock Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=us-east-1
BEDROCK_DEFAULT_MODEL=anthropic.claude-3-sonnet-20240229-v1:0
```

## Custom LLM Configuration

```
# Custom LLM Configuration
CUSTOM_LLM_API_BASE=https://your-custom-llm-endpoint.com/api
CUSTOM_LLM_API_KEY=your_custom_api_key
CUSTOM_LLM_DEFAULT_MODEL=your-custom-model
```

## Web Surfing Configuration

For the web surfing and complex task processing features:

```
# Web Search Configuration
SEARCH_API_KEY=your_google_search_api_key
SEARCH_ENGINE_ID=your_google_search_engine_id
SERPER_API_KEY=your_serper_api_key

# Web Surfing Configuration
BROWSERLESS_API_KEY=your_browserless_api_key
BROWSERLESS_URL=https://chrome.browserless.io
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

## Switching Between Providers

To switch between providers, simply change the `DEFAULT_LLM_PROVIDER` variable in your `.env` file.

You can also specify the provider for individual requests by setting the `provider` parameter in your API calls.

```python
import requests

response = requests.post(
    "http://localhost:8000/api/chat",
    json={
        "prompt": "What is the capital of France?",
        "provider": "openai",  # Override the default provider
        "model": "gpt-4o"
    }
)

print(response.json())
```
"""
    }
]

# Documentation routes
@docs_router.get("/docs", response_class=HTMLResponse)
async def get_docs_home(request: Request):
    """Get the documentation home page."""
    return templates.TemplateResponse(
        "docs_home.html", 
        {"request": request, "api_docs": API_DOCS, "tutorials": TUTORIALS}
    )

@docs_router.get("/docs/api", response_class=HTMLResponse)
async def get_api_docs(request: Request):
    """Get the API documentation page."""
    return templates.TemplateResponse(
        "api_docs.html", 
        {"request": request, "api_docs": API_DOCS}
    )

@docs_router.get("/docs/api/{category}", response_class=HTMLResponse)
async def get_api_category_docs(request: Request, category: str):
    """Get documentation for a specific API category."""
    if category not in API_DOCS:
        raise HTTPException(status_code=404, detail=f"Category {category} not found")
    
    return templates.TemplateResponse(
        "api_category.html", 
        {"request": request, "category": category, "docs": API_DOCS[category]}
    )

@docs_router.get("/docs/tutorials", response_class=HTMLResponse)
async def get_tutorials(request: Request):
    """Get the tutorials page."""
    return templates.TemplateResponse(
        "tutorials.html", 
        {"request": request, "tutorials": TUTORIALS}
    )

@docs_router.get("/docs/tutorials/{tutorial_id}", response_class=HTMLResponse)
async def get_tutorial(request: Request, tutorial_id: str):
    """Get a specific tutorial."""
    tutorial = next((t for t in TUTORIALS if t["id"] == tutorial_id), None)
    if not tutorial:
        raise HTTPException(status_code=404, detail=f"Tutorial {tutorial_id} not found")
    
    return templates.TemplateResponse(
        "tutorial.html", 
        {"request": request, "tutorial": tutorial}
    )

@docs_router.get("/docs/tester", response_class=HTMLResponse)
async def get_api_tester(request: Request):
    """Get the API tester page."""
    return templates.TemplateResponse(
        "api_tester.html", 
        {"request": request, "api_docs": API_DOCS}
    )

@docs_router.post("/docs/tester/execute")
async def execute_api_test(request: Request):
    """Execute an API test."""
    try:
        data = await request.json()
        endpoint = data.get("endpoint")
        method = data.get("method", "GET")
        payload = data.get("payload", {})
        
        # Construct the URL
        base_url = str(request.base_url).rstrip("/")
        url = f"{base_url}{endpoint}"
        
        # Make the request
        async with httpx.AsyncClient() as client:
            if method.upper() == "GET":
                response = await client.get(url, params=payload, timeout=60.0)
            else:
                response = await client.post(url, json=payload, timeout=60.0)
        
        # Return the response
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content": response.json() if response.headers.get("content-type") == "application/json" else response.text
        }
    except Exception as e:
        return {"error": str(e)}

@docs_router.get("/docs/models", response_class=HTMLResponse)
async def get_models_docs(request: Request):
    """Get documentation for the data models."""
    # Extract model information
    models_info = {}
    for name, cls in inspect.getmembers(sys.modules["app.models.chat_models"], inspect.isclass):
        if cls.__module__ == "app.models.chat_models" and issubclass(cls, BaseModel):
            # Get model fields and their descriptions
            fields = []
            for field_name, field in cls.__fields__.items():
                field_info = {
                    "name": field_name,
                    "type": str(field.type_),
                    "required": field.required,
                    "description": field.field_info.description
                }
                fields.append(field_info)
            
            # Get model description from docstring
            description = cls.__doc__ or ""
            description = description.strip()
            
            models_info[name] = {
                "name": name,
                "description": description,
                "fields": fields
            }
    
    return templates.TemplateResponse(
        "models_docs.html", 
        {"request": request, "models_info": models_info}
    )

@docs_router.get("/docs/search", response_class=HTMLResponse)
async def search_docs(request: Request, query: str):
    """Search the documentation."""
    # Implement a simple search across API docs and tutorials
    results = []
    
    # Search in API docs
    for category, category_data in API_DOCS.items():
        if query.lower() in category.lower() or query.lower() in category_data["title"].lower() or query.lower() in category_data["description"].lower():
            results.append({
                "type": "api_category",
                "id": category,
                "title": category_data["title"],
                "description": category_data["description"],
                "url": f"/docs/api/{category}"
            })
        
        for endpoint in category_data["endpoints"]:
            if (query.lower() in endpoint["path"].lower() or 
                query.lower() in endpoint["summary"].lower() or 
                query.lower() in endpoint["description"].lower()):
                results.append({
                    "type": "api_endpoint",
                    "id": endpoint["path"],
                    "title": endpoint["summary"],
                    "description": endpoint["description"],
                    "url": f"/docs/api/{category}#{endpoint['path'].replace('/', '_')}"
                })
    
    # Search in tutorials
    for tutorial in TUTORIALS:
        if (query.lower() in tutorial["id"].lower() or 
            query.lower() in tutorial["title"].lower() or 
            query.lower() in tutorial["description"].lower() or 
            query.lower() in tutorial["content"].lower()):
            results.append({
                "type": "tutorial",
                "id": tutorial["id"],
                "title": tutorial["title"],
                "description": tutorial["description"],
                "url": f"/docs/tutorials/{tutorial['id']}"
            })
    
    return templates.TemplateResponse(
        "search_results.html", 
        {"request": request, "query": query, "results": results}
    )

@docs_router.get("/docs/test", response_class=HTMLResponse)
async def test_docs(request: Request):
    """Test endpoint for the documentation system."""
    return templates.TemplateResponse(
        "test/index.html", 
        {"request": request}
    ) 