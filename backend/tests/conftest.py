"""pytest 公共夹具。

约定（文档/07 §2）：
- 测试库与开发库隔离，自动化测试使用独立测试库；
- 使用合成账户与合成食材，不导入真实个人数据；
- 固定测试时钟或显式传入日期。
"""

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import app

# Keep test-only database URLs in the ignored repository-root .env file.
# Explicit process environment values remain higher priority for CI.
load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


def _legacy_client() -> Generator[TestClient, None, None]:
    """提供 API 测试客户端。"""
    with TestClient(app) as test_client:
        yield test_client


def _unsafe_legacy_db_session() -> Generator[Session, None, None]:
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


# These definitions supersede the initial bootstrap fixtures above. Existing test databases are
# migrated separately; tests must never create or drop their business schema.
@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    if not TEST_DATABASE_URL:
        raise RuntimeError("TEST_DATABASE_URL is required for database tests")
    if make_url(TEST_DATABASE_URL).database != "pantrypilot_test":
        raise RuntimeError("TEST_DATABASE_URL must point to the pantrypilot_test database")

    engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True, future=True)
    with engine.connect() as connection:
        transaction = connection.begin()
        testing_session = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        session = testing_session()

        def override_get_db() -> Generator[Session, None, None]:
            yield session

        app.dependency_overrides[get_db] = override_get_db
        try:
            yield session
        finally:
            app.dependency_overrides.pop(get_db, None)
            session.close()
            transaction.rollback()
    engine.dispose()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client
