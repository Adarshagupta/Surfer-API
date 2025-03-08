import logging
import json
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DIR = os.getenv("LOG_DIR", "logs")

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Create logger
logger = logging.getLogger("surfer-api")
logger.setLevel(getattr(logging, LOG_LEVEL))

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(getattr(logging, LOG_LEVEL))
console_formatter = logging.Formatter(LOG_FORMAT)
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# Create file handler for general logs
general_log_file = os.path.join(LOG_DIR, "api.log")
file_handler = logging.FileHandler(general_log_file)
file_handler.setLevel(getattr(logging, LOG_LEVEL))
file_formatter = logging.Formatter(LOG_FORMAT)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Create file handler for request logs
request_log_file = os.path.join(LOG_DIR, "requests.log")
request_handler = logging.FileHandler(request_log_file)
request_handler.setLevel(logging.INFO)
request_formatter = logging.Formatter("%(message)s")
request_handler.setFormatter(request_formatter)
request_logger = logging.getLogger("surfer-api-requests")
request_logger.setLevel(logging.INFO)
request_logger.addHandler(request_handler)

# Create file handler for error logs
error_log_file = os.path.join(LOG_DIR, "errors.log")
error_handler = logging.FileHandler(error_log_file)
error_handler.setLevel(logging.ERROR)
error_formatter = logging.Formatter(LOG_FORMAT)
error_handler.setFormatter(error_formatter)
logger.addHandler(error_handler)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = f"{int(time.time())}-{os.urandom(4).hex()}"
        
        # Get request details
        method = request.method
        url = str(request.url)
        client_host = request.client.host if request.client else "unknown"
        
        # Log request
        start_time = time.time()
        logger.info(f"Request {request_id}: {method} {url} from {client_host}")
        
        # Get request body for specific endpoints
        request_body = None
        if method in ["POST", "PUT"] and any(path in url for path in ["/api/chat", "/api/function"]):
            try:
                request_body = await request.json()
            except Exception as e:
                logger.warning(f"Could not parse request body: {str(e)}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            status_code = response.status_code
            logger.info(f"Response {request_id}: {status_code} in {process_time:.4f}s")
            
            # Log detailed request/response for analysis
            self._log_request_response(
                request_id=request_id,
                method=method,
                url=url,
                client_host=client_host,
                request_body=request_body,
                status_code=status_code,
                process_time=process_time,
                error=None
            )
            
            return response
        except Exception as e:
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log error
            logger.error(f"Error {request_id}: {str(e)}", exc_info=True)
            
            # Log detailed request/response for analysis
            self._log_request_response(
                request_id=request_id,
                method=method,
                url=url,
                client_host=client_host,
                request_body=request_body,
                status_code=500,
                process_time=process_time,
                error=str(e)
            )
            
            # Re-raise the exception
            raise
    
    def _log_request_response(
        self,
        request_id: str,
        method: str,
        url: str,
        client_host: str,
        request_body: Optional[Dict[str, Any]],
        status_code: int,
        process_time: float,
        error: Optional[str]
    ):
        """Log detailed request/response information for analysis."""
        # Create log entry
        log_entry = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "method": method,
            "url": url,
            "client_host": client_host,
            "status_code": status_code,
            "process_time": process_time,
            "error": error
        }
        
        # Add request body for specific endpoints (excluding sensitive data)
        if request_body:
            # Create a sanitized copy of the request body
            sanitized_body = dict(request_body)
            
            # Remove sensitive fields
            if "system_prompt" in sanitized_body:
                sanitized_body["system_prompt"] = "[REDACTED]"
            
            log_entry["request_body"] = sanitized_body
        
        # Log as JSON
        request_logger.info(json.dumps(log_entry))

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name."""
    child_logger = logging.getLogger(f"surfer-api.{name}")
    return child_logger 