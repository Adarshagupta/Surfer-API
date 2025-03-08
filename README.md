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

## Development

This project uses Ollama for the development phase only. For production, consider using a more robust LLM solution. 