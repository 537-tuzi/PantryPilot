from fastapi import APIRouter, Request

from app.db.session import check_database_connection
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check(request: Request) -> HealthResponse:
    """Report application and database readiness without exposing connection details."""
    check_database_connection()
    return HealthResponse(status="ok", request_id=request.state.request_id)
