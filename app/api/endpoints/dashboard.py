from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.repositories.dashboard_repository import DashboardRepository
from app.schemas.dashboard import DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Operations Reporting"])


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    db: Session = Depends(get_db)
):
    """
    Retrieve executive Invoice Operations Dashboard summary:
    Real-time SQL aggregate KPIs, financial monetary values, verification issue breakdown, recent invoices, and review activity logs.
    """
    repo = DashboardRepository()
    return repo.get_summary(session=db)
