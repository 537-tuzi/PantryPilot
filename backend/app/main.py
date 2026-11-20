"""PantryPilot 后端入口。

开发：uvicorn app.main:app --reload --port 8000
"""

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import (
    AppError,
    app_error_handler,
    http_exception_handler,
    request_validation_error_handler,
)
from app.core.logging import configure_logging
from app.core.request_id import set_request_id

configure_logging()

app = FastAPI(
    title="PantryPilot API",
    version="1.1.0",
    description="家庭食材库存与 AI 膳食规划服务",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """为每个请求分配 request_id，并在响应头回传。"""
    rid = set_request_id(request.headers.get("X-Request-ID"))
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    return response


app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, request_validation_error_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health", tags=["health"], summary="存活探测")
def root_health() -> dict[str, str]:
    """部署手册使用的根路径健康检查。"""
    return {"status": "ok", "version": "1.1.0"}
