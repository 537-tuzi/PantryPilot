"""统一业务异常与错误码。

错误码与 文档/05 §8 保持一致，前端依赖 code 做分支处理。
"""

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """业务异常基类。"""

    status_code = 400
    code = "VALIDATION_ERROR"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(AppError):
    status_code = 400
    code = "VALIDATION_ERROR"


class UnauthenticatedError(AppError):
    status_code = 401
    code = "UNAUTHENTICATED"


class ForbiddenError(AppError):
    status_code = 403
    code = "FORBIDDEN"


class ResourceNotFoundError(AppError):
    status_code = 404
    code = "RESOURCE_NOT_FOUND"


class InsufficientStockError(AppError):
    status_code = 409
    code = "INSUFFICIENT_STOCK"


class StateConflictError(AppError):
    status_code = 409
    code = "STATE_CONFLICT"


class AIOutputInvalidError(AppError):
    """模型输出未通过 Schema 或业务校验。"""

    status_code = 422
    code = "AI_OUTPUT_INVALID"


class RateLimitedError(AppError):
    status_code = 429
    code = "RATE_LIMITED"


class AIProviderError(AppError):
    """模型服务不可用或超时。"""

    status_code = 502
    code = "AI_PROVIDER_ERROR"


class AITimeoutError(AppError):
    status_code = 504
    code = "AI_TIMEOUT"


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """把业务异常转换为统一错误结构。"""
    from app.core.request_id import get_request_id

    payload: dict[str, Any] = {
        "code": exc.code,
        "message": exc.message,
        "request_id": get_request_id(),
    }
    if exc.details:
        payload["details"] = exc.details
    return JSONResponse(status_code=exc.status_code, content=payload)
