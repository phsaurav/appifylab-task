"""
This module provides standardized error handling and API error responses with
detailed logging and request context tracking.

Usage:
    # Create a new API error
    err = APIError.server_error(message="Database connection failed")

    # Use predefined error types
    err = APIError.invalid_json()
    err = APIError.internal_server_error()
    err = APIError.bad_request(message="Invalid parameter")
    err = APIError.not_found(entity="User")

    except Exception as e:
         raise AppError("A critical calculation failed", original_error=e, context={"user_id": user.id})

    # Handle errors in FastAPI endpoints
    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError):
        return handle_api_error(request, exc)

This module integrates with the logging system for comprehensive error tracking and analysis.
"""

import traceback
from typing import Any, Dict, Optional, List
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ValidationError
from core.logger import Logger, get_request_logger


class ErrorLocation(BaseModel):
    """Represents the location of a validation error."""

    field: str
    path: List[str]


class ErrorDetail(BaseModel):
    """Detailed information about an error."""

    location: Optional[str] = None
    message: str
    type: str
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response model for API errors."""

    code: int
    message: str
    error: str
    request_id: Optional[str] = None
    trace_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    errors: Optional[List[ErrorDetail]] = None


class AppError(Exception):
    """Base class for application-level errors with context support."""

    def __init__(
        self,
        message: str,
        original_error: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
    ):
        self.message = message
        self.original_error = original_error
        self.context = context or {}
        self.error_code = error_code
        super().__init__(message)

        # Loggging for Apperror
        error_context = {
            "error_type": "app_error",
            "error_code": error_code,
            **self.context,
        }

        if original_error:
            error_context.update(
                {
                    "original_error_type": type(original_error).__name__,
                    "original_error_message": str(original_error),
                }
            )
            Logger.error(
                f"AppError created: {message}",
                exc_info=original_error,
                error_context=error_context,
            )
        else:
            Logger.error(f"AppError created: {message}", error_context=error_context)


class APIError(HTTPException):
    """API error class with standardized response format and enhanced logging."""

    def __init__(
        self,
        status_code: int,
        message: str,
        error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a new API error.

        Args:
            status_code: HTTP status code
            message: Human-readable error message
            error: Error identifier (default: derived from status_code)
            details: Additional error details
            headers: Additional response headers
            context: Additional context information for logging
        """
        self.status_code = status_code
        self.message = message
        self.error = error or self._default_error_code(status_code)
        self.details = details or {}
        self.context = context or {}
        super().__init__(status_code=status_code, detail=message, headers=headers)

        # API Error Logging
        log_level = "error"
        log_method = getattr(Logger, log_level)

        log_method(
            f"API Error Created: {self.error}",
            error_context={
                "error_type": self.error,
                "status_code": self.status_code,
                "message": self.message,
                **self.context,
            },
            **self.details,
        )

    @staticmethod
    def _default_error_code(status_code: int) -> str:
        """Get a default error code based on the HTTP status code."""
        error_codes = {
            status.HTTP_400_BAD_REQUEST: "bad_request",
            status.HTTP_401_UNAUTHORIZED: "unauthorized",
            status.HTTP_403_FORBIDDEN: "forbidden",
            status.HTTP_404_NOT_FOUND: "not_found",
            status.HTTP_409_CONFLICT: "conflict",
            status.HTTP_422_UNPROCESSABLE_ENTITY: "validation_error",
            status.HTTP_429_TOO_MANY_REQUESTS: "rate_limit_exceeded",
            status.HTTP_500_INTERNAL_SERVER_ERROR: "internal_server_error",
            status.HTTP_502_BAD_GATEWAY: "bad_gateway",
            status.HTTP_503_SERVICE_UNAVAILABLE: "service_unavailable",
            status.HTTP_504_GATEWAY_TIMEOUT: "gateway_timeout",
        }
        return error_codes.get(status_code, f"http_{status_code}")

    @classmethod
    def bad_request(cls, message: str = "Invalid request", **kwargs) -> "APIError":
        """Create a 400 Bad Request error."""
        return cls(status.HTTP_400_BAD_REQUEST, message, **kwargs)

    @classmethod
    def unauthorized(
        cls, message: str = "Authentication required", **kwargs
    ) -> "APIError":
        """Create a 401 Unauthorized error."""
        return cls(status.HTTP_401_UNAUTHORIZED, message, **kwargs)

    @classmethod
    def forbidden(cls, message: str = "Access denied", **kwargs) -> "APIError":
        """Create a 403 Forbidden error."""
        return cls(status.HTTP_403_FORBIDDEN, message, **kwargs)

    @classmethod
    def not_found(cls, entity: str = "Resource", **kwargs) -> "APIError":
        """Create a 404 Not Found error."""
        message = f"{entity} not found"
        return cls(status.HTTP_404_NOT_FOUND, message, **kwargs)

    @classmethod
    def conflict(cls, message: str = "Resource conflict", **kwargs) -> "APIError":
        """Create a 409 Conflict error."""
        return cls(status.HTTP_409_CONFLICT, message, **kwargs)

    @classmethod
    def validation_error(
        cls, message: str = "Validation error", **kwargs
    ) -> "APIError":
        """Create a 422 Unprocessable Entity error."""
        return cls(status.HTTP_422_UNPROCESSABLE_ENTITY, message, **kwargs)

    @classmethod
    def rate_limit_exceeded(
        cls, message: str = "Rate limit exceeded", **kwargs
    ) -> "APIError":
        """Create a 429 Too Many Requests error."""
        return cls(status.HTTP_429_TOO_MANY_REQUESTS, message, **kwargs)

    @classmethod
    def internal_server_error(
        cls, message: str = "Internal server error", **kwargs
    ) -> "APIError":
        """Create a 500 Internal Server Error."""
        return cls(status.HTTP_500_INTERNAL_SERVER_ERROR, message, **kwargs)

    @classmethod
    def bad_gateway(cls, message: str = "Bad gateway", **kwargs) -> "APIError":
        """Create a 502 Bad Gateway error."""
        return cls(status.HTTP_502_BAD_GATEWAY, message, **kwargs)

    @classmethod
    def service_unavailable(
        cls, message: str = "Service unavailable", **kwargs
    ) -> "APIError":
        """Create a 503 Service Unavailable error."""
        return cls(status.HTTP_503_SERVICE_UNAVAILABLE, message, **kwargs)

    @classmethod
    def gateway_timeout(cls, message: str = "Gateway timeout", **kwargs) -> "APIError":
        """Create a 504 Gateway Timeout error."""
        return cls(status.HTTP_504_GATEWAY_TIMEOUT, message, **kwargs)

    @classmethod
    def invalid_json(cls, **kwargs) -> "APIError":
        """Create an error for invalid JSON data."""
        return cls.bad_request(message="Invalid JSON data", **kwargs)

    @classmethod
    def from_exception(
        cls,
        exc: Exception,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        context: Optional[Dict[str, Any]] = None,
    ) -> "APIError":
        """Create an API error from any exception with enhanced details."""
        error_context = context or {}

        # Extract exception details
        exc_details = {
            "type": type(exc).__name__,
            "module": getattr(exc, "__module__", "unknown"),
        }

        # Extract exception chain
        if exc.__cause__:
            cause = exc.__cause__
            exc_details["cause"] = {"type": type(cause).__name__, "message": str(cause)}

        # Extract context info if it's a ContextError or similar
        if hasattr(exc, "context") and isinstance(getattr(exc, "context"), dict):
            error_context.update(getattr(exc, "context"))

        # Add traceback for additional debug info
        tb_summary = traceback.format_exc(limit=10).splitlines()
        exc_details["traceback_summary"] = (
            tb_summary[-5:] if len(tb_summary) > 5 else tb_summary
        )

        error_code = cls._default_error_code(status_code)
        if hasattr(exc, "error_code") and getattr(exc, "error_code"):
            error_code = getattr(exc, "error_code")

        return cls(
            status_code=status_code,
            message=str(exc) or "An unexpected error occurred",
            error=error_code,
            details=exc_details,
            context=error_context,
        )


async def handle_api_error(request: Request, exc: APIError) -> JSONResponse:
    """Handle APIError exceptions with enhanced logging and create a standardized error response."""
    request_logger = get_logger(request)

    # Extract trace context for response and logging
    trace_context = {
        "request_id": getattr(request.state, "request_id", None),
        "trace_id": getattr(request.state, "trace_id", None),
        "span_id": getattr(request.state, "span_id", None),
    }

    # Add request path and method to context
    error_context = {
        "status_code": exc.status_code,
        "error_type": exc.error,
        "path": request.url.path,
        "method": request.method,
        **exc.context,
    }

    # Log the error with context
    request_logger.error(
        f"API Error: {exc.error} - {exc.message}",
        error_context=error_context,
        **trace_context,
    )

    # Prepare response model
    response = ErrorResponse(
        code=exc.status_code,
        message=exc.message,
        error=exc.error,
        details=exc.details,
        request_id=trace_context.get("request_id"),
        trace_id=trace_context.get("trace_id"),
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(exclude_none=True),
        headers=exc.headers or {},
    )


async def handle_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle FastAPI request validation errors with structured error details."""
    # Get request-aware logger
    request_logger = get_request_logger(request)

    # Extract error details
    error_details = []
    for error in exc.errors():
        loc = " -> ".join(str(x) for x in error.get("loc", []))
        error_details.append(
            ErrorDetail(
                location=loc,
                message=error.get("msg", ""),
                type=error.get("type", "validation_error"),
            ).model_dump()
        )

    trace_context = {
        "request_id": getattr(request.state, "request_id", None),
        "trace_id": getattr(request.state, "trace_id", None),
    }

    # Add path and query parameters for context
    request_data = {
        "path_params": dict(request.path_params),
        "query_params": dict(request.query_params),
    }

    # Log the error with context
    request_logger.warning(
        "Request validation error",
        error_context={
            "error_type": "validation_error",
            "path": request.url.path,
            "method": request.method,
            "error_count": len(error_details),
        },
        validation_errors=error_details,
        request_data=request_data,
        **trace_context,
    )

    response = ErrorResponse(
        code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Request validation error",
        error="validation_error",
        request_id=trace_context.get("request_id"),
        trace_id=trace_context.get("trace_id"),
        errors=error_details,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response.model_dump(exclude_none=True),
    )


async def handle_pydantic_validation_error(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors with structured error details."""
    request_logger = get_request_logger(request)

    # Extract error details
    error_details = []
    for error in exc.errors():
        loc = " -> ".join(str(x) for x in error.get("loc", []))
        error_details.append(
            ErrorDetail(
                location=loc,
                message=error.get("msg", ""),
                type=error.get("type", "validation_error"),
            ).dict()
        )

    trace_context = {
        "request_id": getattr(request.state, "request_id", None),
        "trace_id": getattr(request.state, "trace_id", None),
    }

    request_logger.warning(
        "Pydantic validation error",
        error_context={
            "error_type": "pydantic_validation_error",
            "path": request.url.path,
            "method": request.method,
            "error_count": len(error_details),
        },
        validation_errors=error_details,
        **trace_context,
    )

    response = ErrorResponse(
        code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Data validation error",
        error="validation_error",
        request_id=trace_context.get("request_id"),
        trace_id=trace_context.get("trace_id"),
        errors=error_details,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response.dict(exclude_none=True),
    )


async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    """Handle application-level errors with enhanced context and logging."""
    request_logger = get_request_logger(request)

    trace_context = {
        "request_id": getattr(request.state, "request_id", None),
        "trace_id": getattr(request.state, "trace_id", None),
    }

    error_context = {
        "error_type": "app_error",
        "error_code": exc.error_code,
        "path": request.url.path,
        "method": request.method,
        **exc.context,
    }

    request_data = {
        "path_params": dict(request.path_params),
        "query_params": dict(request.query_params),
    }

    if exc.original_error:
        error_context.update(
            {
                "original_error_type": type(exc.original_error).__name__,
                "original_error_message": str(exc.original_error),
                "original_error_module": getattr(
                    exc.original_error, "__module__", "unknown"
                ),
            }
        )

        # Log with traceback
        request_logger.error(
            f"Application Error: {exc.message}",
            exc_info=exc.original_error,
            error_context=error_context,
            request_data=request_data,
            **trace_context,
        )
    else:
        # Log without traceback
        request_logger.error(
            f"Application Error: {exc.message}",
            error_context=error_context,
            request_data=request_data,
            **trace_context,
        )

    api_error = APIError.internal_server_error(
        message="An internal server error occurred",
        details={"app_error_message": exc.message, "app_error_code": exc.error_code},
        context=error_context,
    )

    # Add trace context to the API error for the response
    api_error.details.update(trace_context)

    return await handle_api_error(request, api_error)


async def handle_generic_exception(request: Request, exc: Exception) -> JSONResponse:
    """Handle any unhandled exceptions with comprehensive logging."""
    request_logger = get_request_logger(request)

    trace_context = {
        "request_id": getattr(request.state, "request_id", None),
        "trace_id": getattr(request.state, "trace_id", None),
    }

    tb = traceback.extract_tb(exc.__traceback__)
    if tb:
        last_frame = tb[-1]
        frame_info = {
            "file": last_frame.filename,
            "line": last_frame.lineno,
            "function": last_frame.name,
            "code": last_frame.line,
        }
    else:
        frame_info = {"file": "unknown", "line": 0, "function": "unknown"}

    # Extract exception hierarchy
    exception_chain = []
    current_exc = exc
    while current_exc.__cause__ is not None:
        exception_chain.append(
            {"type": type(current_exc).__name__, "message": str(current_exc)}
        )
        current_exc = current_exc.__cause__

    request_data = {
        "path_params": dict(request.path_params),
        "query_params": dict(request.query_params),
    }

    error_context = {
        "error_type": "unhandled_exception",
        "exception_class": type(exc).__name__,
        "exception_module": getattr(exc, "__module__", "unknown"),
        "path": request.url.path,
        "method": request.method,
        "exception_chain": exception_chain if exception_chain else None,
        **frame_info,
    }

    # Log the exception with full traceback and context
    request_logger.error(
        f"Unhandled exception: {type(exc).__name__} - {str(exc)}",
        exc_info=exc,
        error_context=error_context,
        request_data=request_data,
        **trace_context,
    )

    api_error = APIError.from_exception(exc, context={**error_context, **trace_context})

    return await handle_api_error(request, api_error)


# Function to register all error handlers
def setup_exception_handlers(app):
    """Register all exception handlers with a FastAPI app instance."""
    app.add_exception_handler(APIError, handle_api_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(ValidationError, handle_pydantic_validation_error)
    app.add_exception_handler(AppError, handle_app_error)
    app.add_exception_handler(Exception, handle_generic_exception)

    # Log successful registration
    Logger.info("Registered exception handlers for FastAPI application")


# Helper functions for simplified error tracking
def track_error(error_type: str, **context):
    """Set global error context for subsequent error logs"""
    Logger.set_error_context(error_type=error_type, **context)


def clear_error_tracking():
    """Clear the global error context"""
    Logger.clear_error_context()


# Contextual error handling helper
class ErrorContext:
    """Context manager for tracking errors with context"""

    def __init__(self, context_name: str, **context):
        self.context_name = context_name
        self.context = context

    def __enter__(self):
        track_error(self.context_name, **self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # If an exception occurred
        if exc_type is not None:
            Logger.log_exception(
                exc_val,
                f"Error in {self.context_name}",
                error_context={"exit_context": self.context_name, **self.context},
            )

        clear_error_tracking()
        return False
