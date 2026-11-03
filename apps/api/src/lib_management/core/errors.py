"""Uniform ErrorResponse for every API failure (docs/design/api-contract.md)."""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from lib_management.core.request_id import HEADER, accept_or_generate

logger = logging.getLogger(__name__)


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    details: list[dict[str, Any]] = Field(default_factory=list)
    request_id: str


class AppError(Exception):
    """Base for expected failures; modules add business codes on these statuses."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: list[dict[str, Any]] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or []
        self.headers = headers or {}


class InvalidToken(AppError):
    def __init__(self, message: str = "Token không hợp lệ") -> None:
        super().__init__(
            401, "INVALID_TOKEN", message, headers={"WWW-Authenticate": "Bearer"}
        )


class Forbidden(AppError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(403, code, message)


class NotFound(AppError):
    def __init__(self, message: str = "Không tìm thấy tài nguyên") -> None:
        super().__init__(404, "NOT_FOUND", message)


class Conflict(AppError):
    def __init__(
        self,
        message: str,
        code: str = "CONFLICT",
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(409, code, message, headers=headers)


class ValidationFailed(AppError):
    def __init__(
        self, message: str, details: list[dict[str, Any]] | None = None
    ) -> None:
        super().__init__(422, "VALIDATION_ERROR", message, details)


class ServiceUnavailable(AppError):
    def __init__(self, message: str = "Dịch vụ tạm thời không sẵn sàng") -> None:
        super().__init__(503, "SERVICE_UNAVAILABLE", message)


ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    401: {"model": ErrorResponse, "description": "Unauthenticated"},
    403: {"model": ErrorResponse, "description": "Forbidden"},
    422: {"model": ErrorResponse, "description": "Validation error"},
    503: {"model": ErrorResponse, "description": "Service unavailable"},
}


def _request_id(request: Request) -> str:
    existing = getattr(request.state, "request_id", None)
    return existing if isinstance(existing, str) else accept_or_generate(None)


def _respond(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    request_id = _request_id(request)
    body = ErrorResponse(
        code=code, message=message, details=details or [], request_id=request_id
    )
    return JSONResponse(
        body.model_dump(),
        status_code=status_code,
        headers={**(headers or {}), HEADER: request_id},
    )


def _validation_details(exc: RequestValidationError) -> list[dict[str, Any]]:
    # Drop "input"/"ctx": they can echo secrets or non-JSON values.
    return [
        {
            "loc": list(error.get("loc", ())),
            "msg": error.get("msg"),
            "type": error.get("type"),
        }
        for error in exc.errors()
    ]


def install_error_handlers(app: FastAPI) -> None:
    async def app_error(request: Request, exc: Exception) -> JSONResponse:
        assert isinstance(exc, AppError)
        return _respond(
            request, exc.status_code, exc.code, exc.message, exc.details, exc.headers
        )

    async def http_error(request: Request, exc: Exception) -> JSONResponse:
        assert isinstance(exc, StarletteHTTPException)
        mapping = {
            404: ("NOT_FOUND", "Không tìm thấy tài nguyên"),
            405: ("METHOD_NOT_ALLOWED", "Phương thức không được hỗ trợ"),
            401: ("INVALID_TOKEN", "Token không hợp lệ"),
            403: ("PERMISSION_DENIED", "Không có quyền"),
        }
        code, message = mapping.get(exc.status_code, ("HTTP_ERROR", "Yêu cầu lỗi"))
        return _respond(
            request, exc.status_code, code, message, headers=dict(exc.headers or {})
        )

    async def validation_error(request: Request, exc: Exception) -> JSONResponse:
        assert isinstance(exc, RequestValidationError)
        return _respond(
            request,
            422,
            "VALIDATION_ERROR",
            "Dữ liệu không hợp lệ",
            _validation_details(exc),
        )

    async def unexpected(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error", extra={"request_id": _request_id(request)})
        return _respond(request, 500, "INTERNAL_ERROR", "Lỗi hệ thống")

    app.add_exception_handler(AppError, app_error)
    app.add_exception_handler(StarletteHTTPException, http_error)
    app.add_exception_handler(RequestValidationError, validation_error)
    app.add_exception_handler(Exception, unexpected)
