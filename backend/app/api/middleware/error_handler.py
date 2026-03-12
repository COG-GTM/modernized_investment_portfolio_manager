"""
Global error handling middleware — replaces ERRHNDL.cbl (Centralized Error Handler).

COBOL ERRHNDL performed:
  P100-INIT-ERROR-HANDLER — Initialize error area, generate trace ID
  P200-LOG-ERROR          — INSERT INTO ERRLOG (timestamp, program, paragraph, ...)
  P300-FORMAT-MESSAGE     — STRING 'Error in ' + program + ' - ' + message + '(' + trace_id + ')'
  P400-DETERMINE-ACTION   — EVALUATE severity: FATAL->ABEND, WARNING->CONTINUE, INFO->CONTINUE

This module replaces all of the above with FastAPI exception handlers:
  - Trace IDs generated via uuid4 (replacing FUNCTION RANDOM)
  - Errors logged via Python logging (replacing DB2 ERRLOG table INSERT)
  - Structured JSON error responses (replacing BMS ERRMAP screen)
  - HTTP status codes replace COBOL ERR-ACTION (ABEND->500, WARNING->4xx, INFO->200)
"""

import logging
import traceback
import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.schemas import ErrorDetail, ErrorResponse, ErrorSeverity

logger = logging.getLogger(__name__)


def _generate_trace_id() -> str:
    """
    Generate a unique trace ID for error tracking.
    Replaces ERRHNDL P100: MOVE FUNCTION RANDOM TO ERR-TRACE-ID.
    """
    return uuid.uuid4().hex[:16]


def _log_error(
    trace_id: str,
    source: str,
    message: str,
    severity: ErrorSeverity,
    detail: Optional[str] = None,
) -> None:
    """
    Log error details — replaces ERRHNDL P200-LOG-ERROR which inserted into
    DB2 ERRLOG table with fields:
      LOG-TIMESTAMP, LOG-PROGRAM, LOG-PARAGRAPH, LOG-SQLCODE,
      LOG-CICS-RESP, LOG-SEVERITY, LOG-MESSAGE, LOG-TRACE-ID
    """
    log_data = {
        "trace_id": trace_id,
        "source": source,
        "message": message,
        "severity": severity.value,
        "detail": detail,
    }
    if severity == ErrorSeverity.FATAL:
        logger.error("Error logged: %s", log_data)
    elif severity == ErrorSeverity.WARNING:
        logger.warning("Error logged: %s", log_data)
    else:
        logger.info("Error logged: %s", log_data)


def _format_error_message(source: str, message: str, trace_id: str) -> str:
    """
    Format error message with source and trace ID.
    Replaces ERRHNDL P300-FORMAT-MESSAGE:
      STRING 'Error in ' + ERR-PROGRAM + ' - ' + ERR-MESSAGE + '(' + ERR-TRACE-ID + ')'
    """
    return f"Error in {source} - {message} ({trace_id})"


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register global exception handlers on the FastAPI app.

    Replaces ERRHNDL P400-DETERMINE-ACTION:
      ERR-FATAL   -> ERR-ABEND   (mapped to HTTP 500)
      ERR-WARNING -> ERR-CONTINUE (mapped to HTTP 4xx)
      ERR-INFO    -> ERR-CONTINUE (mapped to HTTP 2xx with info)
    """

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        trace_id = _generate_trace_id()
        severity = ErrorSeverity.WARNING if exc.status_code < 500 else ErrorSeverity.FATAL

        _log_error(
            trace_id=trace_id,
            source="http",
            message=str(exc.detail),
            severity=severity,
        )

        error_response = ErrorResponse(
            error=ErrorDetail(
                code=f"HTTP_{exc.status_code}",
                message=str(exc.detail),
                severity=severity,
                trace_id=trace_id,
                source="api",
            )
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        trace_id = _generate_trace_id()
        errors = exc.errors()
        message = "; ".join(
            f"{'.'.join(str(loc) for loc in e.get('loc', []))}: {e.get('msg', '')}"
            for e in errors
        )

        _log_error(
            trace_id=trace_id,
            source="validation",
            message=message,
            severity=ErrorSeverity.WARNING,
        )

        error_response = ErrorResponse(
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message="Request validation failed",
                detail=message,
                severity=ErrorSeverity.WARNING,
                trace_id=trace_id,
                source="validation",
            )
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.model_dump(),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        Catch-all handler — replaces ERRHNDL ERR-FATAL -> ERR-ABEND path.
        COBOL: EXEC CICS ABEND ABCODE('IERR')
        Python: Return HTTP 500 with trace ID for debugging.
        """
        trace_id = _generate_trace_id()
        tb = traceback.format_exc()

        _log_error(
            trace_id=trace_id,
            source="unhandled",
            message=str(exc),
            severity=ErrorSeverity.FATAL,
            detail=tb,
        )

        error_response = ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_ERROR",
                message="An unexpected error occurred",
                detail=f"Trace ID: {trace_id}",
                severity=ErrorSeverity.FATAL,
                trace_id=trace_id,
                source="system",
            )
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(),
        )
