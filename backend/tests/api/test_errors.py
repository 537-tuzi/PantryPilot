"""统一错误响应结构测试。

所有业务异常都经 core/errors.py 的全局处理器转换，响应结构固定为
{code, message, request_id}（文档/05 §5、§8）。
"""

from fastapi.testclient import TestClient

from app.core.errors import InsufficientStockError, ValidationError
from app.main import app


def test_validation_error_returns_standard_shape(client: TestClient) -> None:
    """字段校验失败应返回 400 与统一错误结构。"""

    @app.get("/__test__/validation-error", include_in_schema=False)
    def _raise_validation_error() -> None:
        raise ValidationError("食材名称不能为空")

    response = client.get("/__test__/validation-error")

    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert body["message"] == "食材名称不能为空"
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]


def test_insufficient_stock_returns_409(client: TestClient) -> None:
    """库存不足应返回 409 与 INSUFFICIENT_STOCK。"""

    @app.get("/__test__/insufficient-stock", include_in_schema=False)
    def _raise_stock_error() -> None:
        raise InsufficientStockError("库存不足，仅剩 100g")

    response = client.get("/__test__/insufficient-stock")

    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "INSUFFICIENT_STOCK"
    assert "100g" in body["message"]


def test_unknown_route_returns_404(client: TestClient) -> None:
    """未注册路由返回 404。"""
    response = client.get("/__test__/not-exist")
    assert response.status_code == 404
