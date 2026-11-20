"""pytest 公共夹具。

约定（文档/07 §2）：
- 测试库与开发库隔离，自动化测试使用独立测试库；
- 使用合成账户与合成食材，不导入真实个人数据；
- 固定测试时钟或显式传入日期。
"""

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.main import app

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """提供 API 测试客户端。"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """提供测试数据库会话；未配置 TEST_DATABASE_URL 时跳过。"""
    if not TEST_DATABASE_URL:
        pytest.skip("未配置 TEST_DATABASE_URL，跳过数据库用例")

    engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True, future=True)
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    session = testing_session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
