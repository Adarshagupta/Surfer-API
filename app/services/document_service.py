import os
import io
import base64
from typing import Dict, List, Optional, Any, Union
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
import numpy as np
from fastapi import UploadFile
import logging

# Set up logging
from app.core.logging import get_logger
logger = get_logger("document_service")

# Configure document storage
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "data/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

class DocumentProcessor:
    """Service for processing various document types (images, PDFs)."""
    
    @staticmethod
    async def process_image(file: UploadFile) -> Dict[str, Any]:
        """
        Process an uploaded image file.
        
        Args:
            file: The uploaded image file
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            # Read the file content
            content = await file.read()
            
            # Save the file
            filename = f"{os.urandom(8).hex()}_{file.filename}"
            file_path = os.path.join(UPLOAD_DIR, filename)
            
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Process the image
            image = Image.open(io.BytesIO(content))
            
            # Extract text using OCR
            extracted_text = pytesseract.image_to_string(image)
            
            # Get image metadata
            width, height = image.size
            format_type = image.format
            mode = image.mode
            
            # Create a thumbnail
            image.thumbnail((200, 200))
            thumbnail_buffer = io.BytesIO()
            image.save(thumbnail_buffer, format="JPEG")
            thumbnail_base64 = base64.b64encode(thumbnail_buffer.getvalue()).decode("utf-8")
            
            return {
                "filename": file.filename,
                "stored_filename": filename,
                "file_path": file_path,
                "file_size": len(content),
                "width": width,
                "height": height,
                "format": format_type,
                "mode": mode,
                "extracted_text": extracted_text,
                "thumbnail": thumbnail_base64,
                "type": "image"
            }
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def process_pdf(file: UploadFile) -> Dict[str, Any]:
        """
        Process an uploaded PDF file.
        
        Args:
            file: The uploaded PDF file
            
        Returns:
            Dictionary with extracted text, metadata, and page information
        """
        try:
            # Read the file content
            content = await file.read()
            
            # Save the file
            filename = f"{os.urandom(8).hex()}_{file.filename}"
            file_path = os.path.join(UPLOAD_DIR, filename)
            
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Process the PDF
            pdf_document = fitz.open(stream=content, filetype="pdf")
            num_pages = len(pdf_document)
            
            # Extract text and images from each page
            pages = []
            all_text = []
            
            for page_num in range(num_pages):
                page = pdf_document[page_num]
                page_text = page.get_text()
                all_text.append(page_text)
                
                # Get page dimensions
                page_width = page.rect.width
                page_height = page.rect.height
                
                # Create a thumbnail of the first page
                if page_num == 0:
                    pix = page.get_pixmap(matrix=fitz.Matrix(0.2, 0.2))
                    thumbnail_bytes = pix.tobytes("jpeg")
                    thumbnail_base64 = base64.b64encode(thumbnail_bytes).decode("utf-8")
                
                # Extract images from the page
                page_images = []
                image_list = page.get_images(full=True)
                
                for img_index, img_info in enumerate(image_list):
                    xref = img_info[0]
                    base_image = pdf_document.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    # Only store metadata about the image, not the full image
                    page_images.append({
                        "index": img_index,
                        "extension": image_ext,
                        "size": len(image_bytes)
                    })
                
                pages.append({
                    "page_number": page_num + 1,
                    "width": page_width,
                    "height": page_height,
                    "text": page_text,
                    "image_count": len(page_images),
                    "images": page_images
                })
            
            # Close the document
            pdf_document.close()
            
            return {
                "filename": file.filename,
                "stored_filename": filename,
                "file_path": file_path,
                "file_size": len(content),
                "num_pages": num_pages,
                "pages": pages,
                "extracted_text": "\n".join(all_text),
                "thumbnail": thumbnail_base64,
                "type": "pdf"
            }
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def process_document(file: UploadFile) -> Dict[str, Any]:
        """
        Process an uploaded document file (image or PDF).
        
        Args:
            file: The uploaded file
            
        Returns:
            Dictionary with extracted text and metadata
        """
        # Determine file type
        content_type = file.content_type.lower()
        filename = file.filename.lower()
        
        if content_type.startswith("image/") or filename.endswith((".jpg", ".jpeg", ".png", ".gif", ".bmp")):
            return await DocumentProcessor.process_image(file)
        elif content_type == "application/pdf" or filename.endswith(".pdf"):
            return await DocumentProcessor.process_pdf(file)
        else:
            raise ValueError(f"Unsupported file type: {content_type}")
    
    @staticmethod
    def get_document_by_id(document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document by its ID (stored filename).
        
        Args:
            document_id: The document ID (stored filename)
            
        Returns:
            Document metadata if found, None otherwise
        """
        try:
            file_path = os.path.join(UPLOAD_DIR, document_id)
            
            if not os.path.exists(file_path):
                return None
            
            # Determine file type
            if document_id.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".bmp")):
                # Process image
                image = Image.open(file_path)
                width, height = image.size
                format_type = image.format
                mode = image.mode
                
                # Create a thumbnail
                image.thumbnail((200, 200))
                thumbnail_buffer = io.BytesIO()
                image.save(thumbnail_buffer, format="JPEG")
                thumbnail_base64 = base64.b64encode(thumbnail_buffer.getvalue()).decode("utf-8")
                
                return {
                    "document_id": document_id,
                    "file_path": file_path,
                    "width": width,
                    "height": height,
                    "format": format_type,
                    "mode": mode,
                    "thumbnail": thumbnail_base64,
                    "type": "image"
                }
            elif document_id.lower().endswith(".pdf"):
                # Process PDF
                pdf_document = fitz.open(file_path)
                num_pages = len(pdf_document)
                
                # Create a thumbnail of the first page
                page = pdf_document[0]
                pix = page.get_pixmap(matrix=fitz.Matrix(0.2, 0.2))
                thumbnail_bytes = pix.tobytes("jpeg")
                thumbnail_base64 = base64.b64encode(thumbnail_bytes).decode("utf-8")
                
                # Close the document
                pdf_document.close()
                
                return {
                    "document_id": document_id,
                    "file_path": file_path,
                    "num_pages": num_pages,
                    "thumbnail": thumbnail_base64,
                    "type": "pdf"
                }
            else:
                return {
                    "document_id": document_id,
                    "file_path": file_path,
                    "type": "unknown"
                }
        except Exception as e:
            logger.error(f"Error getting document: {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    def extract_text_from_document(document_id: str) -> str:
        """
        Extract text from a document.
        
        Args:
            document_id: The document ID (stored filename)
            
        Returns:
            Extracted text
        """
        try:
            file_path = os.path.join(UPLOAD_DIR, document_id)
            
            if not os.path.exists(file_path):
                raise ValueError(f"Document not found: {document_id}")
            
            # Determine file type
            if document_id.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".bmp")):
                # Extract text from image using OCR
                image = Image.open(file_path)
                extracted_text = pytesseract.image_to_string(image)
                return extracted_text
            elif document_id.lower().endswith(".pdf"):
                # Extract text from PDF
                pdf_document = fitz.open(file_path)
                text = ""
                
                for page_num in range(len(pdf_document)):
                    page = pdf_document[page_num]
                    text += page.get_text()
                
                # Close the document
                pdf_document.close()
                
                return text
            else:
                raise ValueError(f"Unsupported file type: {document_id}")
        except Exception as e:
            logger.error(f"Error extracting text from document: {str(e)}", exc_info=True)
            raise

# Create a singleton instance
document_processor = DocumentProcessor() 