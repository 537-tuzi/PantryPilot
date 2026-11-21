"""FR-010 dashboard summary use case."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.inventory_service import current_date


class DashboardService:
    def __init__(self, dashboard: DashboardRepository | None = None) -> None:
        self._dashboard = dashboard or DashboardRepository()

    def summary(self, db: Session, user_id: UUID) -> DashboardSummaryResponse:
        today = current_date()
        inventory_count, expiring_count, expired_count = self._dashboard.summary(db, user_id, today)
        return DashboardSummaryResponse(
            statistics_date=today,
            inventory_count=inventory_count,
            expiring_count=expiring_count,
            expired_count=expired_count,
        )
