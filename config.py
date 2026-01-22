import os
from pydantic import BaseSettings, Field
from typing import Optional, List
import secrets

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "Agentic Coder API"
    app_version: str = "1.0.0"
    app_description: str = "A comprehensive FastAPI application for agentic coding tasks"
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    reload: bool = Field(default=False, env="RELOAD")
    
    # Security
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    api_key_prefix: str = Field(default="ac_")
    
    # Database (would be used with real database)
    database_url: str = Field(default="sqlite:///./app.db", env="DATABASE_URL")
    database_test_url: str = Field(default="sqlite:///./test.db", env="DATABASE_TEST_URL")
    
    # CORS
    cors_origins: List[str] = Field(default=["*"])
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: List[str] = Field(default=["*"])
    cors_allow_headers: List[str] = Field(default=["*"])
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # API Settings
    api_prefix: str = Field(default="/api/v1")
    docs_url: str = Field(default="/docs")
    redoc_url: str = Field(default="/redoc")
    
    # Pagination
    default_page_size: int = Field(default=10)
    max_page_size: int = Field(default=100)
    
    # Rate Limiting (would be implemented with proper rate limiting)
    rate_limit_enabled: bool = Field(default=False)
    rate_limit_requests: int = Field(default=100)
    rate_limit_window: int = Field(default=60)  # seconds
    
    # File Upload (would be implemented for file handling)
    upload_dir: str = Field(default="uploads")
    max_file_size: int = Field(default=10 * 1024 * 1024)  # 10MB
    allowed_extensions: List[str] = Field(default=["jpg", "jpeg", "png", "gif", "pdf", "txt"])
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

class DevelopmentSettings(Settings):
    """Development settings"""
    debug: bool = True
    environment: str = "development"
    reload: bool = True
    log_level: str = "DEBUG"

class TestingSettings(Settings):
    """Testing settings"""
    debug: bool = True
    environment: str = "testing"
    database_url: str = "sqlite:///./test.db"

class ProductionSettings(Settings):
    """Production settings"""
    debug: bool = False
    environment: str = "production"
    cors_origins: List[str] = Field(default=["https://yourdomain.com"])
    rate_limit_enabled: bool = True

def get_settings() -> Settings:
    """Get settings based on environment"""
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment == "production":
        return ProductionSettings()
    elif environment == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()

# Create default settings instance
settings = get_settings()

# Database configuration (would be used with SQLAlchemy)
DATABASE_CONFIG = {
    "development": {
        "url": settings.database_url,
        "echo": True
    },
    "testing": {
        "url": settings.database_test_url,
        "echo": False
    },
    "production": {
        "url": settings.database_url,
        "echo": False
    }
}

# Security configuration
SECURITY_CONFIG = {
    "secret_key": settings.secret_key,
    "algorithm": settings.algorithm,
    "access_token_expire_minutes": settings.access_token_expire_minutes
}

# CORS configuration
CORS_CONFIG = {
    "allow_origins": settings.cors_origins,
    "allow_credentials": settings.cors_allow_credentials,
    "allow_methods": settings.cors_allow_methods,
    "allow_headers": settings.cors_allow_headers
}

# API configuration
API_CONFIG = {
    "prefix": settings.api_prefix,
    "version": settings.app_version,
    "docs_url": settings.docs_url,
    "redoc_url": settings.redoc_url
}

# Pagination configuration
PAGINATION_CONFIG = {
    "default_page_size": settings.default_page_size,
    "max_page_size": settings.max_page_size
}

# Rate limiting configuration
RATE_LIMIT_CONFIG = {
    "enabled": settings.rate_limit_enabled,
    "requests": settings.rate_limit_requests,
    "window": settings.rate_limit_window
}

# File upload configuration
UPLOAD_CONFIG = {
    "directory": settings.upload_dir,
    "max_size": settings.max_file_size,
    "allowed_extensions": settings.allowed_extensions
}