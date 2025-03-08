from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Query
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Optional, Dict, Any
import os
from pydantic import BaseModel

from app.services.document_service import document_processor
from app.services.llm_service import get_llm_response
from app.core.config import settings

# Create router
document_router = APIRouter(tags=["documents"])

class DocumentAnalysisRequest(BaseModel):
    """Model for document analysis requests."""
    document_id: str
    prompt: Optional[str] = "Analyze this document and extract the key information."
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    show_thinking: Optional[bool] = False

# Upload document endpoint
@document_router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    analysis: bool = Form(False),
    prompt: Optional[str] = Form(None)
):
    """
    Upload a document (image or PDF) and optionally analyze it.
    
    Args:
        file: The document file to upload
        analysis: Whether to analyze the document
        prompt: Custom prompt for document analysis
        
    Returns:
        Document metadata and analysis results if requested
    """
    try:
        # Process the document
        document_data = await document_processor.process_document(file)
        
        # Analyze the document if requested
        if analysis:
            # Use the extracted text for analysis
            extracted_text = document_data.get("extracted_text", "")
            
            # Default prompt if not provided
            if not prompt:
                prompt = "Analyze this document and extract the key information."
            
            # Prepare the full prompt with the extracted text
            full_prompt = f"{prompt}\n\nDocument content:\n{extracted_text}"
            
            # Get response from LLM
            response_data = await get_llm_response(
                prompt=full_prompt,
                model=settings.DEFAULT_MODEL,
                system_prompt="You are a document analysis assistant. Analyze the provided document text and extract key information.",
                temperature=0.3,  # Lower temperature for more focused analysis
                max_tokens=1024,
                show_thinking=True
            )
            
            # Add analysis to the response
            document_data["analysis"] = {
                "prompt": prompt,
                "response": response_data["response"],
                "thinking_process": response_data.get("thinking_process")
            }
        
        return document_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get document by ID endpoint
@document_router.get("/documents/{document_id}")
async def get_document(document_id: str):
    """
    Get a document by its ID.
    
    Args:
        document_id: The document ID
        
    Returns:
        Document metadata
    """
    try:
        document_data = document_processor.get_document_by_id(document_id)
        
        if not document_data:
            raise HTTPException(status_code=404, detail=f"Document not found: {document_id}")
        
        return document_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Download document endpoint
@document_router.get("/documents/{document_id}/download")
async def download_document(document_id: str):
    """
    Download a document by its ID.
    
    Args:
        document_id: The document ID
        
    Returns:
        The document file
    """
    try:
        document_data = document_processor.get_document_by_id(document_id)
        
        if not document_data:
            raise HTTPException(status_code=404, detail=f"Document not found: {document_id}")
        
        file_path = document_data["file_path"]
        
        return FileResponse(
            path=file_path,
            filename=document_id.split("_", 1)[1] if "_" in document_id else document_id,
            media_type="application/octet-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Extract text from document endpoint
@document_router.get("/documents/{document_id}/text")
async def extract_text(document_id: str):
    """
    Extract text from a document.
    
    Args:
        document_id: The document ID
        
    Returns:
        Extracted text
    """
    try:
        extracted_text = document_processor.extract_text_from_document(document_id)
        
        return {"document_id": document_id, "text": extracted_text}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Analyze document endpoint
@document_router.post("/documents/analyze")
async def analyze_document(request: DocumentAnalysisRequest):
    """
    Analyze a document using the LLM.
    
    Args:
        request: The analysis request
        
    Returns:
        Analysis results
    """
    try:
        # Get the document
        document_data = document_processor.get_document_by_id(request.document_id)
        
        if not document_data:
            raise HTTPException(status_code=404, detail=f"Document not found: {request.document_id}")
        
        # Extract text from the document
        extracted_text = document_processor.extract_text_from_document(request.document_id)
        
        # Prepare the full prompt with the extracted text
        full_prompt = f"{request.prompt}\n\nDocument content:\n{extracted_text}"
        
        # Get response from LLM
        response_data = await get_llm_response(
            prompt=full_prompt,
            model=request.model or settings.DEFAULT_MODEL,
            system_prompt=request.system_prompt or "You are a document analysis assistant. Analyze the provided document text and extract key information.",
            temperature=request.temperature or 0.3,
            max_tokens=request.max_tokens or 1024,
            show_thinking=request.show_thinking
        )
        
        # Return the analysis results
        return {
            "document_id": request.document_id,
            "prompt": request.prompt,
            "response": response_data["response"],
            "thinking_process": response_data.get("thinking_process") if request.show_thinking else None,
            "model": request.model or settings.DEFAULT_MODEL
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Chat with document endpoint
@document_router.post("/documents/chat")
async def chat_with_document(
    document_id: str = Form(...),
    prompt: str = Form(...),
    model: Optional[str] = Form(None),
    system_prompt: Optional[str] = Form(None),
    temperature: Optional[float] = Form(None),
    max_tokens: Optional[int] = Form(None),
    show_thinking: Optional[bool] = Form(False)
):
    """
    Chat with a document using the LLM.
    
    Args:
        document_id: The document ID
        prompt: The user's message
        model: The model to use
        system_prompt: System prompt to guide the model's behavior
        temperature: Temperature for response generation
        max_tokens: Maximum number of tokens to generate
        show_thinking: Whether to include the model's thinking process
        
    Returns:
        Chat response
    """
    try:
        # Get the document
        document_data = document_processor.get_document_by_id(document_id)
        
        if not document_data:
            raise HTTPException(status_code=404, detail=f"Document not found: {document_id}")
        
        # Extract text from the document
        extracted_text = document_processor.extract_text_from_document(document_id)
        
        # Prepare the system prompt
        default_system_prompt = f"""You are a document assistant. You are given a document to analyze and answer questions about.
        
Document type: {document_data.get('type', 'unknown')}
Document filename: {document_id.split('_', 1)[1] if '_' in document_id else document_id}

When answering questions:
1. Only use information from the provided document.
2. If the answer is not in the document, say so clearly.
3. Provide specific references to parts of the document when possible.
"""
        
        effective_system_prompt = system_prompt or default_system_prompt
        
        # Prepare the full prompt with the extracted text
        full_prompt = f"{prompt}\n\nDocument content:\n{extracted_text}"
        
        # Get response from LLM
        response_data = await get_llm_response(
            prompt=full_prompt,
            model=model or settings.DEFAULT_MODEL,
            system_prompt=effective_system_prompt,
            temperature=temperature or 0.7,
            max_tokens=max_tokens or 1024,
            show_thinking=show_thinking
        )
        
        # Return the chat response
        return {
            "document_id": document_id,
            "prompt": prompt,
            "response": response_data["response"],
            "thinking_process": response_data.get("thinking_process") if show_thinking else None,
            "model": model or settings.DEFAULT_MODEL
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 