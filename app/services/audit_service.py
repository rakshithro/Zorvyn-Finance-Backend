from sqlalchemy.orm import Session
from fastapi import Request

from app.models.audit_log import AuditLog


def log_action(
    db: Session,
    *,
    user_id: int | None,
    action: str,
    entity: str,
    entity_id: int | None = None,
    detail: str | None = None,
    request: Request | None = None,
) -> AuditLog:
    """
    Append an immutable audit record.

    Usage example for reference:
        log_action(db, user_id=user.id, action="CREATE_TRANSACTION",
                   entity="Transaction", entity_id=tx.id, request=request)
    """
    ip = None
    if request:
        forwarded = request.headers.get("X-Forwarded-For")
        ip = forwarded.split(",")[0].strip() if forwarded else (
            request.client.host if request.client else None
        )

    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        detail=detail,
        ip_address=ip,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_audit_logs(
    db: Session,
    *,
    user_id: int | None = None,
    entity: str | None = None,
    action: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[AuditLog]:
    query = db.query(AuditLog)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if entity:
        query = query.filter(AuditLog.entity == entity)
    if action:
        query = query.filter(AuditLog.action == action)
    return query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()