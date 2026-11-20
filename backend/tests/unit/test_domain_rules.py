"""Unit tests for pure domain rules."""

from datetime import date, timedelta
from decimal import Decimal

from app.domain.expiry import EXPIRING_WINDOW_DAYS, inventory_status
from app.domain.inventory import reason_direction_error
from app.domain.shopping import can_transition


def test_inventory_status_boundaries() -> None:
    today = date(2026, 11, 21)

    assert inventory_status(None, today) == "normal"
    assert inventory_status(today - timedelta(days=1), today) == "expired"
    assert inventory_status(today, today) == "expiring"
    assert inventory_status(today + timedelta(days=EXPIRING_WINDOW_DAYS), today) == "expiring"
    assert inventory_status(today + timedelta(days=EXPIRING_WINDOW_DAYS + 1), today) == "normal"


def test_reason_direction_rules() -> None:
    assert reason_direction_error("add", Decimal("1.000")) is None
    assert reason_direction_error("add", Decimal("0.000")) is not None
    assert reason_direction_error("consume", Decimal("-1.000")) is None
    assert reason_direction_error("consume", Decimal("1.000")) is not None
    assert reason_direction_error("adjust", Decimal("1.000")) is None
    assert reason_direction_error("adjust", Decimal("-1.000")) is None


def test_shopping_status_machine() -> None:
    assert can_transition("pending", "purchased")
    assert can_transition("pending", "cancelled")
    assert can_transition("purchased", "cancelled")
    assert can_transition("cancelled", "cancelled")
    assert not can_transition("purchased", "pending")
    assert not can_transition("cancelled", "pending")
    assert not can_transition("cancelled", "purchased")
