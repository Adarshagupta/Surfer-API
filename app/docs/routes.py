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

from app.api.routes.chat import router as chat_router
from app.api.routes.health import router as health_router
from app.api.routes.travel import router as travel_router
from app.services.llm_service import get_llm_response
from app.services.web_surfing_service import WebSurfingService
from app.models.chat_models import (
    ChatMessage, ChatResponse, AdvancedChatMessage, 
    FunctionCallingMessage, DocumentChatMessage, 
    WebSearchChatMessage, WebSearchResponse, 
    TravelItineraryRequest, TravelItineraryResponse,
    ComplexTaskRequest, ComplexTaskResponse
)
from app.docs.api_docs import API_DOCS

# Create the documentation router
docs_router = APIRouter(tags=["documentation"])

# Set up templates
templates_path = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))

# Tutorials
TUTORIALS = [
    {
        "id": "getting-started",
        "title": "Getting Started with Surfer API",
        "description": "Learn how to make your first API call to the Surfer API.",
        "content": """
# Getting Started with Surfer API

Welcome to the Surfer API! This tutorial will guide you through making your first API call to interact with our powerful language models.

## Prerequisites

Before you begin, make sure you have:

- Python 3.8 or higher installed
- `requests` library installed (`pip install requests`)
- An API key (see the [Authentication Tutorial](/docs/tutorials/authentication) for how to get one)

## Making Your First API Call

Let's start by making a simple chat request to the API:

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

To enable the thinking process, simply add the `show_thinking` parameter to your API request and set it to `true`:

```python
import requests

response = requests.post(
    "http://localhost:8000/api/chat",
    json={
        "prompt": "What would happen if humans could photosynthesize like plants?",
        "model": "deepseek-r1:7b",
        "show_thinking": True
    }
)

result = response.json()
print("Thinking Process:")
print(result["thinking"])
print("\nFinal Response:")
print(result["content"])
```

## Example Output

Here's an example of what the thinking process might look like:

```
Thinking Process:
I need to consider the implications of humans having photosynthesis capabilities like plants.

First, let me understand what photosynthesis is:
- Photosynthesis is the process where plants convert sunlight, water, and carbon dioxide into glucose and oxygen
- Plants use chlorophyll to capture sunlight energy
- This provides plants with their energy source

If humans could photosynthesize:

1. Energy production:
   - Humans would be able to produce some of their own energy from sunlight
   - This would supplement our caloric intake from food
   - We wouldn't completely eliminate the need for food since photosynthesis is less efficient than our digestive system for energy

2. Physiological changes:
   - We would need chlorophyll in our skin, making us appear green
   - We would need larger surface areas exposed to sunlight
   - Our skin would likely develop specialized structures similar to leaves

3. Behavioral changes:
   - People would spend more time outdoors in sunlight
   - Clothing styles would change to maximize sun exposure
   - Work and school schedules might revolve around daylight hours

4. Global implications:
   - Reduced food consumption could help address hunger
   - Agricultural land use might decrease
   - Carbon dioxide consumption would increase, potentially helping with climate change
   - Oxygen production would increase

5. Limitations:
   - Winter and cloudy days would create energy shortages
   - People in regions with less sunlight would be disadvantaged
   - Indoor workers would need special lighting

Final Response:
If humans could photosynthesize like plants, it would fundamentally transform our biology, society, and relationship with the environment...
```

## Benefits of Using the Thinking Process

The thinking process feature offers several benefits:

1. **Transparency**: See how the model arrives at its conclusions
2. **Educational value**: Learn about the model's reasoning approach
3. **Debugging**: Identify where the model might be making incorrect assumptions
4. **Prompt improvement**: Understand how to better structure your prompts
5. **Trust building**: Verify the model's thought process aligns with expectations

## When to Use the Thinking Process

The thinking process is particularly useful for:

- Complex reasoning tasks
- Problem-solving scenarios
- Educational contexts
- Debugging unexpected responses
- Evaluating model capabilities

## Technical Details

The `show_thinking` parameter works with all models supported by the Surfer API, but the quality and detail of the thinking process may vary between models. Larger models typically provide more sophisticated reasoning.

The thinking process is generated before the final response and uses additional tokens, which may affect your usage limits and response time.

## Next Steps

Try experimenting with the thinking process feature on different types of queries to see how it can enhance your understanding of the model's responses. You can also combine it with other parameters like `temperature` to see how they affect the reasoning process.
"""
    },
    {
        "id": "web-surfing",
        "title": "Web Surfing Capabilities",
        "description": "Learn how to use the web surfing features to get real-time information.",
        "content": """
# Web Surfing Capabilities

The Surfer API includes powerful web surfing capabilities that allow the LLM to access and process real-time information from the internet. This tutorial explains how to use these features and how they can enhance your applications.

## What is Web Surfing?

Web surfing in the context of the Surfer API refers to the ability of the LLM to:

1. Search the web for relevant information
2. Visit and read web pages
3. Extract and synthesize information from multiple sources
4. Provide up-to-date responses based on current information

This capability is particularly useful for questions about current events, recent developments, or topics that require the most up-to-date information.

## Basic Web Search

The simplest way to use web surfing is through the `/api/chat/websearch` endpoint:

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

result = response.json()
print("Response:", result["content"])
print("\nSources:")
for citation in result["citations"]:
    print(f"- {citation['title']}: {citation['url']}")
```

### Parameters

- `search_enabled`: Set to `True` to enable web search
- `num_results`: Number of search results to consider (1-10)
- `include_citations`: Whether to include source citations in the response

## Advanced Web Surfing

For more complex tasks that require deeper web navigation and understanding, use the `/api/chat/complex-task` endpoint:

```python
import requests

response = requests.post(
    "http://localhost:8000/api/chat/complex-task",
    json={
        "task_description": "Compare the top 3 electric vehicles in 2023 based on range, price, and features.",
        "task_type": "comparison",
        "visual_understanding": True,
        "max_depth": 2
    }
)

result = response.json()
print(result["content"])
```

### Parameters

- `task_description`: Detailed description of the task
- `task_type`: Type of task (comparison, research, analysis, etc.)
- `visual_understanding`: Whether to process images on web pages
- `max_depth`: How many links deep to follow from search results

## Use Cases

Web surfing capabilities are ideal for:

1. **Research assistance**: Gathering information on specific topics
2. **Competitive analysis**: Comparing products, services, or companies
3. **News summaries**: Getting updates on current events
4. **Fact checking**: Verifying claims against current information
5. **Travel planning**: Getting up-to-date information about destinations

## Best Practices

To get the most out of web surfing:

1. **Be specific**: Clearly define what information you're looking for
2. **Use appropriate parameters**: Adjust search depth and result count based on your needs
3. **Verify sources**: Always check the citations provided
4. **Consider recency**: For time-sensitive topics, explicitly ask for recent information
5. **Respect privacy**: Don't use web surfing for accessing private or sensitive information

## Limitations

While powerful, web surfing has some limitations:

- Results depend on search engine quality and availability
- Some websites may block access
- Complex web applications may not be fully navigable
- Visual understanding is limited to static images
- Processing time increases with search depth and complexity

## Example: Travel Research

Here's an example of using web surfing for travel planning:

```python
import requests

response = requests.post(
    "http://localhost:8000/api/travel/itinerary",
    json={
        "destination": "Kyoto, Japan",
        "start_date": "2023-10-15",
        "end_date": "2023-10-20",
        "interests": ["historical sites", "local cuisine", "nature"],
        "budget_range": "medium",
        "special_requests": "Include some off-the-beaten-path locations"
    }
)

result = response.json()
print(result["summary"])
print("\nDetailed Itinerary:")
for section in result["detailed_sections"]:
    print(f"\n{section['title']}")
    print(section['content'])
```

This will generate a complete travel itinerary with up-to-date information about attractions, opening hours, and local conditions.

## Next Steps

Try experimenting with different types of queries and parameters to see how web surfing can enhance your applications. You can also combine web surfing with the thinking process feature to see how the model processes and synthesizes information from the web.
"""
    },
    {
        "id": "authentication",
        "title": "Authentication and API Keys",
        "description": "Learn how to authenticate with the Surfer API and manage API keys.",
        "content": """
# Authentication and API Keys

This tutorial covers how to authenticate with the Surfer API, manage API keys, and track usage. The Surfer API provides a comprehensive authentication system that supports both user accounts and API keys.

## User Registration and Login

### Creating a New User Account

To create a new user account, send a POST request to the `/api/auth/signup` endpoint:

```python
import requests

response = requests.post(
    "http://localhost:8000/api/auth/signup",
    json={
        "email": "user@example.com",
        "username": "johndoe",
        "password": "Password123!",
        "full_name": "John Doe"
    }
)

print(response.json())
```

### Logging In

To log in and obtain an access token, send a POST request to the `/api/auth/token` endpoint:

```python
import requests

response = requests.post(
    "http://localhost:8000/api/auth/token",
    data={
        "username": "johndoe",
        "password": "Password123!"
    }
)

token_data = response.json()
access_token = token_data["access_token"]
print(f"Access Token: {access_token}")
```

Save this access token for use in subsequent requests.

### Using the Access Token

Include the access token in the `Authorization` header for authenticated requests:

```python
import requests

headers = {
    "Authorization": f"Bearer {access_token}"
}

response = requests.get(
    "http://localhost:8000/api/auth/me",
    headers=headers
)

print(response.json())
```

## API Key Management

API keys provide a more convenient way to authenticate API requests, especially for applications and scripts.

### Creating an API Key

To create a new API key, send a POST request to the `/api/api-keys` endpoint:

```python
import requests

headers = {
    "Authorization": f"Bearer {access_token}"
}

response = requests.post(
    "http://localhost:8000/api/api-keys",
    headers=headers,
    json={
        "name": "My Application",
        "expires_at": "2024-12-31T23:59:59Z"  # Optional expiration date
    }
)

api_key_data = response.json()
api_key = api_key_data["key"]
print(f"API Key: {api_key}")
```

**Important**: The full API key is only shown once when created. Make sure to save it securely.

### Listing Your API Keys

To list all your API keys, send a GET request to the `/api/api-keys` endpoint:

```python
import requests

headers = {
    "Authorization": f"Bearer {access_token}"
}

response = requests.get(
    "http://localhost:8000/api/api-keys",
    headers=headers
)

api_keys = response.json()
for key in api_keys:
    print(f"ID: {key['id']}, Name: {key['name']}, Created: {key['created_at']}")
```

### Revoking an API Key

To revoke an API key, send a DELETE request to the `/api/api-keys/{api_key_id}` endpoint:

```python
import requests

headers = {
    "Authorization": f"Bearer {access_token}"
}

api_key_id = 123  # Replace with the actual API key ID

response = requests.delete(
    f"http://localhost:8000/api/api-keys/{api_key_id}",
    headers=headers
)

if response.status_code == 204:
    print("API key revoked successfully")
else:
    print(f"Error: {response.status_code}")
```

## Using API Keys for Chat

Once you have an API key, you can use it to access the chat API:

```python
import requests

headers = {
    "X-API-Key": api_key
}

response = requests.post(
    "http://localhost:8000/api/chat",
    headers=headers,
    json={
        "prompt": "What is the capital of France?",
        "model": "deepseek-r1:1.5b"
    }
)

print(response.json())
```

## User Profile Management

### Getting Your Profile

To get your user profile information, send a GET request to the `/api/users/me/profile` endpoint:

```python
import requests

headers = {
    "Authorization": f"Bearer {access_token}"
}

response = requests.get(
    "http://localhost:8000/api/users/me/profile",
    headers=headers
)

profile = response.json()
print(profile)
```

### Updating Your Profile

To update your profile information, send a PUT request to the `/api/users/me/profile` endpoint:

```python
import requests

headers = {
    "Authorization": f"Bearer {access_token}"
}

response = requests.put(
    "http://localhost:8000/api/users/me/profile",
    headers=headers,
    json={
        "email": "newemail@example.com",
        "full_name": "John Smith",
        "password": "NewPassword123!"  # Optional - only include if changing password
    }
)

updated_profile = response.json()
print(updated_profile)
```

## Usage Tracking

### Getting Usage History

To get your API usage history, send a GET request to the `/api/users/me/usage` endpoint:

```python
import requests

headers = {
    "Authorization": f"Bearer {access_token}"
}

response = requests.get(
    "http://localhost:8000/api/users/me/usage",
    headers=headers,
    params={
        "limit": 10,  # Number of records to return
        "offset": 0   # Pagination offset
    }
)

usage_records = response.json()
for record in usage_records:
    print(f"Endpoint: {record['endpoint']}, Tokens: {record['tokens_used']}, Date: {record['created_at']}")
```

### Getting Usage Summary

To get a summary of your API usage, send a GET request to the `/api/users/me/usage/summary` endpoint:

```python
import requests

headers = {
    "Authorization": f"Bearer {access_token}"
}

response = requests.get(
    "http://localhost:8000/api/users/me/usage/summary",
    headers=headers
)

summary = response.json()
print(f"Total tokens used: {summary['total_tokens_used']}")
print(f"Total requests: {summary['total_requests']}")
print(f"Most used model: {summary['most_used_model']}")
```

## Security Best Practices

1. **Secure your tokens and passwords**: Never expose your access tokens or API keys in client-side code.
2. **Use HTTPS**: Always use HTTPS for production environments to encrypt data in transit.
3. **Set expiration dates**: Consider setting expiration dates for API keys that aren't needed indefinitely.
4. **Limit permissions**: Use the principle of least privilege - only grant the permissions necessary.
5. **Rotate keys regularly**: Regularly rotate API keys, especially for sensitive applications.
6. **Monitor usage**: Regularly check your usage statistics to detect any unusual activity.

## Next Steps

Now that you understand how to authenticate and manage API keys, you can:

- Explore the [API Documentation](/docs/api) for detailed information about all available endpoints
- Try the [API Tester](/docs/tester) to experiment with different API calls
- Check out the [Getting Started Tutorial](/docs/tutorials/getting-started) for basic usage examples
"""
    },
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