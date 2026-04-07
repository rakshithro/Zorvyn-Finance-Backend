from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.schemas.audit_log import AuditLogResponse
from app.services.audit_service import get_audit_logs
from app.core.security import require_roles

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])   
admin_only = require_roles("admin")

@router.get("/", response_model=list[AuditLogResponse])
def list_audit_logs(
    user_id: Optional[int] = Query(None, description="Filter by user"),
    entity: Optional[str] = Query(None, description="Filter by entity, e.g. Transaction"),
    action: Optional[str] = Query(None, description="Filter by action, e.g. CREATE_TRANSACTION"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _=Depends(admin_only),
):
    """
    Audit trail entries. For Admin only.
    Filter by user, entity type, or action name.
    """
    return get_audit_logs(db, user_id=user_id, entity=entity, action=action, skip=skip, limit=limit)    
    