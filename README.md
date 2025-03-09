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