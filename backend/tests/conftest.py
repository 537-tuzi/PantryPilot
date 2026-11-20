import os

import pytest
from sqlalchemy.orm import Session

test_database_url = os.getenv("TEST_DATABASE_URL")
if not test_database_url:
    raise RuntimeError("TEST_DATABASE_URL must be set so tests never use the development database.")
if not test_database_url.rstrip("/").endswith("/pantrypilot_test"):
    raise RuntimeError("TEST_DATABASE_URL must point to the isolated pantrypilot_test database.")

os.environ["DATABASE_URL"] = test_database_url

from app.db.session import engine


@pytest.fixture
def db_session() -> Session:
    """Run each database test in a transaction that is rolled back afterwards."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()
