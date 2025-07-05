"""Comprehensive logging infrastructure for kubectl-ld."""

import json
import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .interfaces import Logger
from .container import singleton


class StructuredLogger:
    """Structured logger with context support."""
    
    def __init__(
        self, 
        name: str, 
        level: str = "INFO",
        log_file: Optional[Path] = None,
        structured: bool = True
    ) -> None:
        self.name = name
        self.structured = structured
        self.context: Dict[str, Any] = {}
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(getattr(logging, level.upper()))
        
        if structured:
            console_handler.setFormatter(JsonFormatter())
        else:
            console_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            )
        
        self.logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(JsonFormatter())
            self.logger.addHandler(file_handler)
    
    def with_context(self, **kwargs: Any) -> 'StructuredLogger':
        """Create logger with additional context."""
        new_logger = StructuredLogger(
            self.name, 
            structured=self.structured
        )
        new_logger.logger = self.logger
        new_logger.context = {**self.context, **kwargs}
        return new_logger
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message."""
        self._log(logging.CRITICAL, message, **kwargs)
    
    def _log(self, level: int, message: str, **kwargs: Any) -> None:
        """Internal logging method."""
        extra = {
            'structured_data': {
                **self.context,
                **kwargs,
                'timestamp': datetime.utcnow().isoformat(),
                'logger_name': self.name
            }
        }
        self.logger.log(level, message, extra=extra)


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            'timestamp': datetime.utcfromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add structured data if available
        if hasattr(record, 'structured_data'):
            log_data.update(record.structured_data)
        
        # Add exception info if available
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, default=str)


@singleton(Logger)
class DefaultLogger(StructuredLogger):
    """Default logger implementation."""
    
    def __init__(self) -> None:
        level = os.environ.get('LDCTL_LOG_LEVEL', 'INFO')
        
        # Determine log file location
        log_file = None
        if os.environ.get('LDCTL_LOG_FILE'):
            log_file = Path(os.environ['LDCTL_LOG_FILE'])
        elif os.environ.get('LDCTL_LOG_DIR'):
            log_dir = Path(os.environ['LDCTL_LOG_DIR'])
            log_file = log_dir / 'kubectl-ld.log'
        
        structured = os.environ.get('LDCTL_LOG_FORMAT', 'structured') == 'structured'
        
        super().__init__(
            name='kubectl-ld',
            level=level,
            log_file=log_file,
            structured=structured
        )


class OperationLogger:
    """Logger for tracking operations with timing and context."""
    
    def __init__(self, logger: Logger, operation: str) -> None:
        self.logger = logger
        self.operation = operation
        self.start_time = datetime.utcnow()
        self.context: Dict[str, Any] = {'operation': operation}
    
    def __enter__(self) -> 'OperationLogger':
        self.logger.info(f"Starting {self.operation}", **self.context)
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        duration = (datetime.utcnow() - self.start_time).total_seconds()
        
        if exc_type:
            self.logger.error(
                f"Operation {self.operation} failed after {duration:.2f}s",
                duration=duration,
                error=str(exc_val),
                **self.context
            )
        else:
            self.logger.info(
                f"Operation {self.operation} completed in {duration:.2f}s",
                duration=duration,
                **self.context
            )
    
    def add_context(self, **kwargs: Any) -> None:
        """Add context to the operation."""
        self.context.update(kwargs)
    
    def log_progress(self, message: str, **kwargs: Any) -> None:
        """Log progress during operation."""
        elapsed = (datetime.utcnow() - self.start_time).total_seconds()
        self.logger.info(
            f"{self.operation}: {message}",
            elapsed=elapsed,
            **self.context,
            **kwargs
        )


def get_logger(name: Optional[str] = None) -> Logger:
    """Get a logger instance."""
    if name:
        level = os.environ.get('LDCTL_LOG_LEVEL', 'INFO')
        return StructuredLogger(name, level)
    else:
        from .container import inject
        return inject(Logger)


def operation(name: str, logger: Optional[Logger] = None) -> OperationLogger:
    """Create an operation logger context manager."""
    if logger is None:
        logger = get_logger()
    return OperationLogger(logger, name)


def configure_logging(
    level: str = "INFO",
    log_file: Optional[Union[str, Path]] = None,
    structured: bool = True
) -> None:
    """Configure global logging settings."""
    # Set environment variables for default logger
    os.environ['LDCTL_LOG_LEVEL'] = level
    if log_file:
        os.environ['LDCTL_LOG_FILE'] = str(log_file)
    os.environ['LDCTL_LOG_FORMAT'] = 'structured' if structured else 'simple'
    
    # Suppress urllib3 warnings in kubectl operations
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    # Suppress other noisy loggers
    logging.getLogger('asyncio').setLevel(logging.WARNING)