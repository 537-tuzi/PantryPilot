"""健康检查接口测试（TC-DEP 系列的冒烟前置）。"""

import asyncio
import json

from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from app.core.errors import http_exception_handler
from app.main import app


def test_root_health(client: TestClient) -> None:
    """根路径健康检查应返回 ok。"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_health(client: TestClient) -> None:
    """版本化健康检查应返回 ok。"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_request_id_header(client: TestClient) -> None:
    """响应应带上 request_id，便于日志追踪（NFR-008）。"""
    response = client.get("/health")
    assert "X-Request-ID" in response.headers


def test_method_not_allowed_uses_uniform_error_envelope(client: TestClient) -> None:
    response = client.put("/health")

    assert response.status_code == 405
    assert response.json()["code"] == "METHOD_NOT_ALLOWED"
    assert response.headers["Allow"] == "GET"
    assert response.json()["request_id"] == response.headers["X-Request-ID"]


def test_unmapped_http_status_preserves_status_and_headers() -> None:
    response = asyncio.run(
        http_exception_handler(
            Request({"type": "http"}),
            StarletteHTTPException(
                status_code=413, detail="Payload too large", headers={"X-Test": "1"}
            ),
        )
    )

    assert response.status_code == 413
    assert json.loads(response.body)["code"] == "HTTP_ERROR"
    assert response.headers["X-Test"] == "1"


def test_unhandled_error_uses_uniform_error_envelope() -> None:
    @app.get("/_test-unhandled-error")
    def raise_unhandled_error() -> None:
        raise RuntimeError("internal detail must not be returned")

    try:
        with TestClient(app, raise_server_exceptions=False) as test_client:
            response = test_client.get("/_test-unhandled-error")
    finally:
        app.router.routes.pop()

    assert response.status_code == 500
    assert response.json() == {
        "code": "INTERNAL_SERVER_ERROR",
        "message": "Internal server error",
        "request_id": response.headers["X-Request-ID"],
    }
