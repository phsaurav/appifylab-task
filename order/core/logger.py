"""
A simplified logging system for FastAPI applications.

Basic Usage:
from core.logger import Logger
Logger.info("User logged in", user_id="123")

@app.get("/users/{user_id}")
async def get_user(user_id: str, logger=Depends(get_request_logger)):
    logger.info("Fetching user profile", user_id=user_id)
"""

import json
import logging
import sys
import uuid
from datetime import datetime, timezone
from typing import Optional, Any, Dict

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from core import config


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for easier parsing and analysis."""

    def format(self, record: logging.LogRecord) -> str:
        # Basic log structure
        log_data = {
            "level": record.levelname,
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add request context if available
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        # Add exception info if present
        if record.exc_info:
            exc_type, exc_value, _ = record.exc_info
            log_data["exception"] = {
                "type": exc_type.__name__,
                "message": str(exc_value),
            }

        # Add extra fields
        if hasattr(record, "extra") and record.extra:
            log_data.update(record.extra)

        return json.dumps(log_data)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Add request ID and log basic request/response information"""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        # Log the request
        Logger.info(
            f"Request started: {request.method} {request.url.path}",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        start_time = datetime.now()

        try:
            # Process the request
            response = await call_next(request)

            # Log successful response
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            Logger.info(
                f"Request completed: {response.status_code}",
                request_id=request_id,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            )

            return response

        except Exception as e:
            # Log failed request
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            Logger.error(
                f"Request failed: {type(e).__name__} - {str(e)}",
                request_id=request_id,
                exc_info=True,
                duration_ms=round(duration_ms, 2),
            )
            raise


class Logger:
    _logger: Optional[logging.Logger] = None
    _APP_LOGGER_NAME = f"{config.cfg.title}_log"

    @classmethod
    def setup(
        cls,
        app: Optional[FastAPI] = None,
        log_level: str = "INFO",
        json_format: bool = True,
    ) -> logging.Logger:
        logger = logging.getLogger(cls._APP_LOGGER_NAME)
        logger.setLevel(log_level.upper())
        logger.handlers = []  # Clear existing handlers
        logger.propagate = False

        # Create and configure handler
        handler = logging.StreamHandler(sys.stdout)
        if json_format:
            formatter = JSONFormatter()
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s [%(module)s:%(funcName)s:%(lineno)d]"
            )

        handler.setFormatter(formatter)
        logger.addHandler(handler)
        cls._logger = logger

        # Add middleware to app if provided
        if app:
            app.add_middleware(LoggingMiddleware)

        logger.info(f"Logger initialized with level: {log_level}")
        return logger

    @classmethod
    def _get_logger(cls) -> logging.Logger:
        if cls._logger is None:
            cls.setup()
        return cls._logger

    @classmethod
    def info(cls, message, **kwargs):
        cls._get_logger().info(message, extra={"extra": kwargs})

    @classmethod
    def error(cls, message, exc_info=False, **kwargs):
        cls._get_logger().error(message, exc_info=exc_info, extra={"extra": kwargs})

    @classmethod
    def warning(cls, message, **kwargs):
        cls._get_logger().warning(message, extra={"extra": kwargs})

    @classmethod
    def debug(cls, message, **kwargs):
        cls._get_logger().debug(message, extra={"extra": kwargs})

    @classmethod
    def critical(cls, message, exc_info=False, **kwargs):
        cls._get_logger().critical(message, exc_info=exc_info, extra={"extra": kwargs})


def get_request_logger(request: Request):
    """Return a logger that includes the request ID in all log messages"""
    logger = Logger._get_logger()

    class RequestLogger:
        """Simple adapter to include request ID with all logs"""

        def info(self, message, **kwargs):
            kwargs["request_id"] = request.state.request_id
            logger.info(message, extra={"extra": kwargs})

        def error(self, message, exc_info=False, **kwargs):
            kwargs["request_id"] = request.state.request_id
            logger.error(message, exc_info=exc_info, extra={"extra": kwargs})

        def warning(self, message, **kwargs):
            kwargs["request_id"] = request.state.request_id
            logger.warning(message, extra={"extra": kwargs})

        def debug(self, message, **kwargs):
            kwargs["request_id"] = request.state.request_id
            logger.debug(message, extra={"extra": kwargs})

        def critical(self, message, exc_info=False, **kwargs):
            kwargs["request_id"] = request.state.request_id
            logger.critical(message, exc_info=exc_info, extra={"extra": kwargs})

    return RequestLogger()
