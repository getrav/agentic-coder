import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import re
from fastapi import HTTPException, status

class SecurityUtils:
    """Security utilities for the application"""
    
    @staticmethod
    def generate_token(data: Dict[str, Any], expires_in: int = 3600) -> str:
        """Generate JWT token"""
        payload = {
            **data,
            "exp": datetime.utcnow() + timedelta(seconds=expires_in),
            "iat": datetime.utcnow()
        }
        # In production, use a proper secret key
        secret_key = "your-secret-key-here"
        return jwt.encode(payload, secret_key, algorithm="HS256")
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            secret_key = "your-secret-key-here"
            return jwt.decode(token, secret_key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256 (in production, use bcrypt)"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify password"""
        return SecurityUtils.hash_password(password) == hashed_password
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate API key"""
        return f"ac_{secrets.token_hex(16)}"
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

class ValidationUtils:
    """Validation utilities"""
    
    @staticmethod
    def validate_task_title(title: str) -> bool:
        """Validate task title"""
        if not title or len(title.strip()) == 0:
            return False
        if len(title) > 200:
            return False
        return True
    
    @staticmethod
    def validate_task_description(description: Optional[str]) -> bool:
        """Validate task description"""
        if description is None:
            return True
        if len(description) > 1000:
            return False
        return True
    
    @staticmethod
    def validate_user_name(name: str) -> bool:
        """Validate user name"""
        if not name or len(name.strip()) == 0:
            return False
        if len(name) > 100:
            return False
        return True

class DateUtils:
    """Date utilities"""
    
    @staticmethod
    def format_datetime(dt: datetime) -> str:
        """Format datetime to ISO string"""
        return dt.isoformat() if dt else None
    
    @staticmethod
    def parse_datetime(dt_str: str) -> Optional[datetime]:
        """Parse datetime from string"""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except ValueError:
            return None

class ResponseUtils:
    """Response utilities"""
    
    @staticmethod
    def success_response(data: Any, message: str = "Success") -> Dict[str, Any]:
        """Create success response"""
        return {
            "success": True,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def error_response(
        error: str, 
        message: str = "Error occurred",
        status_code: int = 400
    ) -> Dict[str, Any]:
        """Create error response"""
        return {
            "success": False,
            "error": error,
            "message": message,
            "status_code": status_code,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def paginated_response(
        data: list,
        total: int,
        page: int,
        per_page: int
    ) -> Dict[str, Any]:
        """Create paginated response"""
        return {
            "success": True,
            "data": data,
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page
            },
            "timestamp": datetime.now().isoformat()
        }

class DatabaseUtils:
    """Database utilities (for in-memory storage)"""
    
    @staticmethod
    def find_by_id(items: list, item_id: int) -> Optional[Any]:
        """Find item by ID in list"""
        for item in items:
            if hasattr(item, 'id') and item.id == item_id:
                return item
        return None
    
    @staticmethod
    def delete_by_id(items: list, item_id: int) -> bool:
        """Delete item by ID from list"""
        for i, item in enumerate(items):
            if hasattr(item, 'id') and item.id == item_id:
                del items[i]
                return True
        return False
    
    @staticmethod
    def get_next_id(items: list) -> int:
        """Get next available ID"""
        if not items:
            return 1
        max_id = max(item.id for item in items if hasattr(item, 'id'))
        return max_id + 1

class LoggerUtils:
    """Logging utilities"""
    
    @staticmethod
    def log_action(action: str, user_id: Optional[int] = None, details: Optional[Dict] = None):
        """Log user action"""
        log_entry = {
            "action": action,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        # In production, log to proper logging system
        print(f"ACTION_LOG: {log_entry}")
    
    @staticmethod
    def log_error(error: Exception, context: Optional[Dict] = None):
        """Log error"""
        error_entry = {
            "error": str(error),
            "type": type(error).__name__,
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        }
        # In production, log to proper error tracking system
        print(f"ERROR_LOG: {error_entry}")