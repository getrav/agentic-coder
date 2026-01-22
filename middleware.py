from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
import time
import logging
from typing import Callable
from datetime import datetime

logger = logging.getLogger(__name__)

async def log_requests(request: Request, call_next: Callable):
    """Middleware to log all requests"""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    
    logger.info(
        f"{request.method} {request.url} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.2f}ms"
    )
    
    return response

def add_cors_middleware(app):
    """Add CORS middleware to the app"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

def add_gzip_middleware(app):
    """Add GZip compression middleware"""
    app.add_middleware(GZipMiddleware, minimum_size=1000)

def add_https_redirect_middleware(app):
    """Add HTTPS redirect middleware (for production)"""
    app.add_middleware(HTTPSRedirectMiddleware)

def add_request_id_middleware(app):
    """Add request ID middleware for tracking"""
    @app.middleware("http")
    async def add_request_id(request: Request, call_next: Callable):
        request_id = request.headers.get("X-Request-ID", "unknown")
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

def add_security_headers_middleware(app):
    """Add security headers middleware"""
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next: Callable):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

def setup_middleware(app, environment="development"):
    """Setup all middleware for the application"""
    
    # Add request logging
    app.middleware("http")(log_requests)
    
    # Add CORS
    add_cors_middleware(app)
    
    # Add GZip compression
    add_gzip_middleware(app)
    
    # Add request ID
    add_request_id_middleware(app)
    
    # Add security headers
    add_security_headers_middleware(app)
    
    # Add HTTPS redirect in production
    if environment == "production":
        add_https_redirect_middleware(app)
    
    logger.info("Middleware setup completed")