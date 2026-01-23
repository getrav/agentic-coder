import json
import logging
import os
import sys
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, asdict


class LogLevel(Enum):
    """Log levels for structured logging."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


@dataclass
class LogConfig:
    """Configuration for structured JSON logging."""
    level: LogLevel = LogLevel.INFO
    format_json: bool = True
    include_timestamp: bool = True
    include_level: bool = True
    include_logger_name: bool = True
    output_file: Optional[str] = None
    console_output: bool = True
    context_fields: Optional[list] = None
    
    def __post_init__(self):
        if self.context_fields is None:
            self.context_fields = ['session_id', 'user_id', 'request_id', 'correlation_id']


class StructuredLogger:
    """Structured JSON logger with context support."""
    
    def __init__(self, name: str, config: Optional[LogConfig] = None):
        self.name = name
        self.config = config or LogConfig()
        self.context: Dict[str, Any] = {}
        self._file_handler = None
        
        # Set up file handler if output file is specified
        if self.config.output_file:
            self._setup_file_handler()
    
    def _setup_file_handler(self):
        """Set up file handler for log output."""
        try:
            # Ensure log directory exists
            log_dir = os.path.dirname(self.config.output_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            # Create file handler
            self._file_handler = open(self.config.output_file, 'a', encoding='utf-8')
        except Exception as e:
            # Fall back to console output if file handler fails
            print(f"Failed to set up file handler: {e}", file=sys.stderr)
    
    def _format_log(self, level: LogLevel, message: str, **kwargs) -> str:
        """Format log entry as JSON or plain text."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z' if self.config.include_timestamp else None,
            'level': level.value if self.config.include_level else None,
            'logger': self.name if self.config.include_logger_name else None,
            'message': message,
            **kwargs
        }
        
        # Add context fields
        if self.config.context_fields:
            for field in self.config.context_fields:
                if field in self.context:
                    log_entry[field] = self.context[field]
        
        # Remove None values
        log_entry = {k: v for k, v in log_entry.items() if v is not None}
        
        if self.config.format_json:
            return json.dumps(log_entry, separators=(',', ':'), ensure_ascii=False)
        else:
            # Plain text format
            parts = []
            if 'timestamp' in log_entry:
                parts.append(f"[{log_entry['timestamp']}]")
            if 'level' in log_entry:
                parts.append(f"[{log_entry['level']}]")
            if 'logger' in log_entry:
                parts.append(f"[{log_entry['logger']}]")
            parts.append(log_entry['message'])
            
            # Add context as key=value pairs
            for key, value in log_entry.items():
                if key not in ['timestamp', 'level', 'logger', 'message']:
                    parts.append(f"{key}={value}")
            
            return " ".join(parts)
    
    def _write_log(self, log_entry: str):
        """Write log entry to output destinations."""
        if self.config.console_output:
            print(log_entry)
        
        if self._file_handler:
            try:
                self._file_handler.write(log_entry + '\n')
                self._file_handler.flush()
            except Exception as e:
                # Fall back to console output if file write fails
                print(f"Failed to write to log file: {e}", file=sys.stderr)
                print(log_entry)
    
    def _log(self, level: LogLevel, message: str, **kwargs):
        """Internal logging method."""
        if not self._should_log(level):
            return
        
        log_entry = self._format_log(level, message, **kwargs)
        self._write_log(log_entry)
    
    def _should_log(self, level: LogLevel) -> bool:
        """Check if message should be logged based on level."""
        level_hierarchy = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARN: 2,
            LogLevel.ERROR: 3
        }
        
        return level_hierarchy[level] >= level_hierarchy[self.config.level]
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log(LogLevel.INFO, message, **kwargs)
    
    def warn(self, message: str, **kwargs):
        """Log warning message."""
        self._log(LogLevel.WARN, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message (alias for warn)."""
        self.warn(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log(LogLevel.ERROR, **kwargs)
    
    def exception(self, message: str, exception: Exception = None, **kwargs):
        """Log exception with traceback."""
        if exception:
            kwargs['exception_type'] = type(exception).__name__
            kwargs['exception_message'] = str(exception)
        
        self.error(message, **kwargs)
    
    def set_context(self, **kwargs):
        """Set logging context."""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear all logging context."""
        self.context.clear()
    
    def with_context(self, **kwargs):
        """Create a new logger instance with additional context."""
        new_logger = StructuredLogger(self.name, self.config)
        new_logger.context = self.context.copy()
        new_logger.context.update(kwargs)
        return new_logger
    
    def close(self):
        """Close file handler if open."""
        if self._file_handler:
            try:
                self._file_handler.close()
            except Exception:
                pass  # Ignore errors during close


class LoggerFactory:
    """Factory for creating structured loggers."""
    
    _loggers: Dict[str, StructuredLogger] = {}
    _default_config: Optional[LogConfig] = None
    
    @classmethod
    def set_default_config(cls, config: LogConfig):
        """Set default configuration for all loggers."""
        cls._default_config = config
    
    @classmethod
    def get_logger(cls, name: str, config: Optional[LogConfig] = None) -> StructuredLogger:
        """Get or create a logger with the given name."""
        if name not in cls._loggers:
            logger_config = config or cls._default_config or LogConfig()
            cls._loggers[name] = StructuredLogger(name, logger_config)
        
        return cls._loggers[name]
    
    @classmethod
    def close_all(cls):
        """Close all loggers."""
        for logger in cls._loggers.values():
            logger.close()
        cls._loggers.clear()


# Global logger factory
_logger_factory = LoggerFactory()


def get_logger(name: str, config: Optional[LogConfig] = None) -> StructuredLogger:
    """Get a structured logger instance."""
    return _logger_factory.get_logger(name, config)


def configure_logging(config: LogConfig):
    """Configure default logging settings."""
    _logger_factory.set_default_config(config)


def shutdown_logging():
    """Shutdown all loggers and clean up resources."""
    _logger_factory.close_all()