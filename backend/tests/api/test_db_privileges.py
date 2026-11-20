"""Permission regression: the application account must never modify the ledger."""

import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError

APP_DATABASE_URL = os.getenv("TEST_APP_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not APP_DATABASE_URL, reason="TEST_APP_DATABASE_URL is not configured"
)


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE inventory_transactions SET unit = unit WHERE false",
        "DELETE FROM inventory_transactions WHERE false",
        "TRUNCATE inventory_transactions",
    ],
)
def test_app_role_cannot_modify_inventory_ledger(statement: str) -> None:
    engine = create_engine(APP_DATABASE_URL, pool_pre_ping=True, future=True)
    try:
        with engine.connect() as connection:
            with pytest.raises(ProgrammingError) as error:
                connection.execute(text(statement))
            assert "permission denied" in str(error.value).lower()
            connection.rollback()
    finally:
        engine.dispose()
