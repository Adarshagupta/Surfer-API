# Surfer API

A FastAPI backend for a ChatGPT-like application using Ollama with the deepseek-r1:1.5b model.

## Features

- FastAPI backend with async support
- Integration with Ollama for LLM capabilities
- Custom processing and prompt engineering
- RESTful API endpoints for chat functionality
- Advanced prompt template system with versioning
- Function calling capabilities
- Document processing (Images and PDFs)
- OCR for image text extraction
- PDF parsing and analysis
- Perplexity-like web search capabilities
- Real-time information retrieval with citations
- Multi-source content aggregation

## Requirements

- Python 3.9+
- Ollama installed locally with deepseek-r1:1.5b model
- Tesseract OCR for image text extraction

## Setup

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Install Tesseract OCR:
   - On macOS: `brew install tesseract`
   - On Ubuntu: `sudo apt-get install tesseract-ocr`
   - On Windows: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
4. Make sure Ollama is running with the deepseek-r1:1.5b model:
   ```
   ollama pull deepseek-r1:1.5b
   ollama run deepseek-r1:1.5b
   ```
5. Start the FastAPI server:
   ```
   uvicorn app.main:app --reload
   ```

## API Endpoints

### Chat Endpoints
- `POST /api/chat`: Send a message and get a response from the LLM
- `POST /api/chat/stream`: Stream a response from the LLM
- `POST /api/chat/advanced`: Use advanced features like templates
- `POST /api/chat/function`: Use function calling capabilities
- `POST /api/chat/document`: Chat with a document
- `POST /api/chat/websearch`: Chat with web search capabilities (Perplexity-like)

### Document Endpoints
- `POST /api/documents/upload`: Upload a document (image or PDF)
- `GET /api/documents/{document_id}`: Get document metadata
- `GET /api/documents/{document_id}/download`: Download a document
- `GET /api/documents/{document_id}/text`: Extract text from a document
- `POST /api/documents/analyze`: Analyze a document using the LLM
- `POST /api/documents/chat`: Chat with a document

### Template Endpoints
- `GET /api/templates`: Get all templates
- `GET /api/templates/{template_id}`: Get a template by ID
- `POST /api/templates`: Create a new template
- `PUT /api/templates/{template_id}`: Update a template
- `DELETE /api/templates/{template_id}`: Delete a template
- `POST /api/templates/{template_id}/render`: Render a template

### Function Endpoints
- `GET /api/functions`: Get available functions
- `POST /api/function/execute`: Execute a function

### Utility Endpoints
- `GET /api/models`: Get available models
- `GET /api/health`: Check if the API is running

## Document Processing

The API supports processing and analyzing both images and PDFs:

### Image Processing
- Upload images in common formats (JPG, PNG, GIF, BMP)
- Extract text using OCR (Optical Character Recognition)
- Generate thumbnails
- Analyze image content using LLM

### PDF Processing
- Upload and parse PDF documents
- Extract text and metadata
- Extract images from PDFs
- Generate thumbnails
- Analyze PDF content using LLM

## Web Search Features

The API includes Perplexity-like web search capabilities:

### Web Search Integration
- Real-time web search for up-to-date information
- Multiple search backends (Google Custom Search, Serper API, web scraping)
- Content extraction and relevance ranking
- Source citation in responses

### Search Configuration
- Configurable number of search results
- Adjustable search depth (basic snippets or deep content analysis)
- Citation formatting options
- Time limits for search operations

### Use Cases
- Answer questions about current events
- Provide up-to-date information not in the model's training data
- Research topics across multiple sources
- Generate responses with proper citations

## Testing the API

This section provides examples for testing all features of the Surfer API using curl commands. Make sure the API server is running before executing these commands.

### Testing Utility Endpoints

#### Health Check
```bash
curl -X GET http://localhost:8000/api/health
```

#### Get Available Models
```bash
curl -X GET http://localhost:8000/api/models
```

### Testing Basic Chat

#### Simple Chat Request
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is artificial intelligence?",
    "temperature": 0.7,
    "max_tokens": 500
  }'
```

#### Streaming Chat Response
```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a short poem about technology",
    "temperature": 0.8,
    "max_tokens": 200
  }'
```

### Testing Advanced Chat Features

#### Using Templates
First, create a template:
```bash
curl -X POST http://localhost:8000/api/templates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "code_explanation",
    "description": "Template for explaining code",
    "template": "Explain the following code in simple terms:\n\n```{{language}}\n{{code}}\n```",
    "version": "1.0",
    "category": "code"
  }'
```

Then use the template in a chat:
```bash
curl -X POST http://localhost:8000/api/chat/advanced \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "I need help understanding this code",
    "template_id": "code_explanation",
    "template_variables": {
      "language": "python",
      "code": "def fibonacci(n):\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a"
    },
    "temperature": 0.5
  }'
```

#### Function Calling
```bash
curl -X POST http://localhost:8000/api/chat/function \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is the weather in New York?",
    "enable_function_calling": true,
    "auto_execute_functions": true,
    "temperature": 0.7
  }'
```

#### Get Available Functions
```bash
curl -X GET http://localhost:8000/api/functions
```

#### Execute a Function Manually
```bash
curl -X POST http://localhost:8000/api/function/execute \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_weather",
    "arguments": {
      "location": "San Francisco"
    }
  }'
```

### Testing Web Search Features

#### Web Search Chat
```bash
curl -X POST http://localhost:8000/api/chat/websearch \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What are the latest developments in quantum computing?",
    "search_enabled": true,
    "num_results": 3,
    "include_citations": true,
    "search_depth": "deep",
    "temperature": 0.7,
    "max_tokens": 1000
  }'
```

### Testing Document Processing

#### Upload a Document
```bash
# Upload an image
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@/path/to/your/image.jpg"

# Upload a PDF
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@/path/to/your/document.pdf"
```

#### Get Document Metadata
```bash
# Replace document_id with the ID returned from the upload
curl -X GET http://localhost:8000/api/documents/document_id
```

#### Extract Text from a Document
```bash
# Replace document_id with the ID returned from the upload
curl -X GET http://localhost:8000/api/documents/document_id/text
```

#### Download a Document
```bash
# Replace document_id with the ID returned from the upload
curl -X GET http://localhost:8000/api/documents/document_id/download --output downloaded_document
```

#### Analyze a Document
```bash
# Replace document_id with the ID returned from the upload
curl -X POST http://localhost:8000/api/documents/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "document_id",
    "prompt": "Summarize the key points in this document",
    "temperature": 0.5,
    "max_tokens": 500
  }'
```

#### Chat with a Document
```bash
# Replace document_id with the ID returned from the upload
curl -X POST http://localhost:8000/api/documents/chat \
  -F "document_id=document_id" \
  -F "prompt=What is the main topic of this document?" \
  -F "temperature=0.7" \
  -F "max_tokens=300" \
  -F "show_thinking=true"
```

#### Chat with a Document (Using Chat API)
```bash
curl -X POST http://localhost:8000/api/chat/document \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain the key concepts in this document",
    "document_id": "document_id",
    "include_document_content": true,
    "temperature": 0.7,
    "max_tokens": 500
  }'
```

### Testing Template Management

#### Get All Templates
```bash
curl -X GET http://localhost:8000/api/templates
```

#### Get a Specific Template
```bash
# Replace template_id with an actual template ID
curl -X GET http://localhost:8000/api/templates/template_id
```

#### Create a New Template
```bash
curl -X POST http://localhost:8000/api/templates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "summarization",
    "description": "Template for summarizing text",
    "template": "Summarize the following text in {{words}} words or less:\n\n{{text}}",
    "version": "1.0",
    "category": "general"
  }'
```

#### Update a Template
```bash
# Replace template_id with an actual template ID
curl -X PUT http://localhost:8000/api/templates/template_id \
  -H "Content-Type: application/json" \
  -d '{
    "name": "summarization",
    "description": "Updated template for summarizing text",
    "template": "Provide a concise summary of the following text in {{words}} words or less:\n\n{{text}}",
    "version": "1.1",
    "category": "general"
  }'
```

#### Delete a Template
```bash
# Replace template_id with an actual template ID
curl -X DELETE http://localhost:8000/api/templates/template_id
```

#### Render a Template
```bash
# Replace template_id with an actual template ID
curl -X POST http://localhost:8000/api/templates/template_id/render \
  -H "Content-Type: application/json" \
  -d '{
    "variables": {
      "words": "100",
      "text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
    }
  }'
```

## Using the API with Python

Here's a simple Python script to interact with the API:

```python
import requests
import json

BASE_URL = "http://localhost:8000/api"

# Basic chat
def simple_chat(prompt):
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"prompt": prompt}
    )
    return response.json()

# Upload a document
def upload_document(file_path):
    with open(file_path, "rb") as f:
        response = requests.post(
            f"{BASE_URL}/documents/upload",
            files={"file": f}
        )
    return response.json()

# Chat with a document
def document_chat(document_id, prompt):
    response = requests.post(
        f"{BASE_URL}/chat/document",
        json={
            "document_id": document_id,
            "prompt": prompt,
            "include_document_content": True
        }
    )
    return response.json()

# Web search chat
def web_search_chat(prompt):
    response = requests.post(
        f"{BASE_URL}/chat/websearch",
        json={
            "prompt": prompt,
            "search_enabled": True,
            "num_results": 3,
            "include_citations": True
        }
    )
    return response.json()

# Example usage
if __name__ == "__main__":
    # Simple chat
    result = simple_chat("What is machine learning?")
    print(json.dumps(result, indent=2))
    
    # Web search chat
    web_result = web_search_chat("What are the latest developments in fusion energy?")
    print(json.dumps(web_result, indent=2))
    
    # Upload a document
    doc_result = upload_document("path/to/your/document.pdf")
    document_id = doc_result["document_id"]
    
    # Chat with the document
    doc_chat_result = document_chat(document_id, "Summarize this document")
    print(json.dumps(doc_chat_result, indent=2))
```

## Development

This project uses Ollama for the development phase only. For production, consider using a more robust LLM solution.


## Test API 

# Surfer API Tutorial: Testing All Endpoints

This tutorial will guide you through testing all the API endpoints in the Surfer API application using Postman or any other API testing tool.

## Authentication Endpoints

### 1. Signup

**Endpoint:** `POST /api/auth/signup`

**Request Body:**
```json
{
  "email": "test@example.com",
  "username": "testuser",
  "password": "Password123!",
  "full_name": "Test User"
}
```

**Headers:**
- Content-Type: application/json

### 2. Login (Get Token)

**Endpoint:** `POST /api/auth/token`

**Request Body (Form Data):**
- username: testuser
- password: Password123!

**Headers:**
- Content-Type: application/x-www-form-urlencoded

**Response:** Will include an access token that you'll need for authenticated endpoints.

### 3. Get Current User

**Endpoint:** `GET /api/auth/me`

**Headers:**
- Authorization: Bearer {your_access_token}

### 4. Logout

**Endpoint:** `POST /api/auth/logout`

**Headers:**
- Authorization: Bearer {your_access_token}

## API Key Management

### 1. Create API Key

**Endpoint:** `POST /api/api-keys`

**Request Body:**
```json
{
  "name": "My Test API Key",
  "expires_at": "2025-12-31T23:59:59Z"
}
```

**Headers:**
- Content-Type: application/json
- Authorization: Bearer {your_access_token}

### 2. List API Keys

**Endpoint:** `GET /api/api-keys`

**Headers:**
- Authorization: Bearer {your_access_token}

### 3. Delete API Key

**Endpoint:** `DELETE /api/api-keys/{key_id}`

**Headers:**
- Authorization: Bearer {your_access_token}

## Chat Endpoints

### 1. Basic Chat

**Endpoint:** `POST /api/chat`

**Request Body:**
```json
{
  "prompt": "What is artificial intelligence?",
  "model": "deepseek-r1:1.5b",
  "temperature": 0.7,
  "max_tokens": 500,
  "show_thinking": false
}
```

**Headers:**
- Content-Type: application/json
- Authorization: Bearer {your_access_token}

### 2. Get Available Models

**Endpoint:** `GET /api/chat/models`

**Headers:**
- Authorization: Bearer {your_access_token}

### 3. Streaming Chat

**Endpoint:** `POST /api/chat/stream`

**Request Body:**
```json
{
  "prompt": "Write a short poem about technology",
  "model": "deepseek-r1:1.5b",
  "temperature": 0.8,
  "max_tokens": 200
}
```

**Headers:**
- Content-Type: application/json
- Authorization: Bearer {your_access_token}

### 4. Advanced Chat with Templates

**Endpoint:** `POST /api/chat/advanced`

**Request Body:**
```json
{
  "prompt": "I need help understanding this code",
  "template_id": "code_explanation",
  "template_variables": {
    "language": "python",
    "code": "def fibonacci(n):\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a"
  },
  "temperature": 0.5
}
```

**Headers:**
- Content-Type: application/json
- Authorization: Bearer {your_access_token}

### 5. Chat with Context

**Endpoint:** `POST /api/chat/context`

**Request Body:**
```json
{
  "prompt": "Tell me more about that",
  "context_id": 1,
  "update_context": true
}
```

**Headers:**
- Content-Type: application/json
- Authorization: Bearer {your_access_token}

### 6. Web Search Chat

**Endpoint:** `POST /api/chat/websearch`

**Request Body:**
```json
{
  "prompt": "What are the latest developments in quantum computing?",
  "search_enabled": true,
  "num_results": 3,
  "include_citations": true,
  "search_depth": "deep",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**Headers:**
- Content-Type: application/json
- Authorization: Bearer {your_access_token}

## Context Management

### 1. Create Context

**Endpoint:** `POST /api/chat/contexts`

**Request Body:**
```json
{
  "name": "Project Research",
  "description": "Research for my quantum computing project",
  "context_data": {
    "topic": "quantum computing",
    "history": []
  }
}
```

**Headers:**
- Content-Type: application/json
- Authorization: Bearer {your_access_token}

### 2. List Contexts

**Endpoint:** `GET /api/chat/contexts`

**Headers:**
- Authorization: Bearer {your_access_token}

### 3. Get Specific Context

**Endpoint:** `GET /api/chat/contexts/{context_id}`

**Headers:**
- Authorization: Bearer {your_access_token}

### 4. Update Context

**Endpoint:** `PUT /api/chat/contexts/{context_id}`

**Request Body:**
```json
{
  "name": "Updated Project Research",
  "description": "Updated research for my quantum computing project",
  "context_data": {
    "topic": "quantum computing advances",
    "history": []
  }
}
```

**Headers:**
- Content-Type: application/json
- Authorization: Bearer {your_access_token}

### 5. Delete Context

**Endpoint:** `DELETE /api/chat/contexts/{context_id}`

**Headers:**
- Authorization: Bearer {your_access_token}

## Chat History

### 1. Get Chat History

**Endpoint:** `GET /api/chat/chat-history`

**Query Parameters (all optional):**
- context_id: 1
- start_date: 2023-01-01
- end_date: 2023-12-31
- page: 1
- page_size: 10

**Headers:**
- Authorization: Bearer {your_access_token}

### 2. Delete Chat History Entry

**Endpoint:** `DELETE /api/chat/chat-history/{chat_id}`

**Headers:**
- Authorization: Bearer {your_access_token}

## Testing Multi-Provider LLM Selection

To test different LLM providers, you can specify the model in your chat requests. The system will use the appropriate provider based on the model name:

### OpenAI Models

```json
{
  "prompt": "What is artificial intelligence?",
  "model": "gpt-4o",
  "temperature": 0.7
}
```

### Anthropic Models

```json
{
  "prompt": "What is artificial intelligence?",
  "model": "claude-3-opus-20240229",
  "temperature": 0.7
}
```

### Ollama Models

```json
{
  "prompt": "What is artificial intelligence?",
  "model": "deepseek-r1:1.5b",
  "temperature": 0.7
}
```

### Hugging Face Models

```json
{
  "prompt": "What is artificial intelligence?",
  "model": "mistralai/Mistral-7B-Instruct-v0.1",
  "temperature": 0.7
}
```

## Testing Multi-Provider Search

The search provider is configured at the server level, but you can test web search functionality with:

```json
{
  "prompt": "What are the latest developments in quantum computing?",
  "search_enabled": true,
  "num_results": 3,
  "include_citations": true
}
```

## Tips for Testing

1. **Save the Token**: After logging in, save the access token for use in subsequent requests.
2. **Use Collections**: In Postman, organize your requests in collections for easier testing.
3. **Use Environment Variables**: Store your base URL, token, and other common values as environment variables.
4. **Check Response Codes**: Successful requests typically return 200 OK or 201 Created status codes.
5. **Error Handling**: If you get errors, check the response body for detailed error messages.

Would you like me to provide more details on any specific endpoint or feature?
