from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard_service import get_dashboard_summary
from app.core.security import get_current_user, require_roles
from app.models.user import UserRole

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Return aggregated financial summary.
    - Admin / Analyst: system-wide summary
    - Viewer: summary scoped to their own records only
    """
    owner_id = (
        None
        if current_user.role in (UserRole.admin, UserRole.analyst)
        else current_user.id
    )
    return get_dashboard_summary(db, owner_id=owner_id)