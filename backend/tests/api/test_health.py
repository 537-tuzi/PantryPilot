"""健康检查接口测试（TC-DEP 系列的冒烟前置）。"""

from fastapi.testclient import TestClient


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
