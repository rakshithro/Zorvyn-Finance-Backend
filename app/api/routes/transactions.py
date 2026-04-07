from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.db.database import get_db
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionFilter,
    PaginatedTransactions,
)
from app.models.transaction import TransactionType, TransactionCategory
from app.models.user import UserRole
from app.services import transaction_service
from app.services.audit_service import log_action
from app.core.security import require_roles, get_current_user

router = APIRouter(prefix="/transactions", tags=["Transactions"])


def _resolve_owner(current_user, admin_see_all: bool = True) -> int | None:
    """Admins and analysts can see all records; viewers see only their own."""
    if admin_see_all and current_user.role in (UserRole.admin, UserRole.analyst):
        return None
    return current_user.id


@router.get("/", response_model=PaginatedTransactions)
def list_transactions(
    type: Optional[TransactionType] = Query(None),
    category: Optional[TransactionCategory] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    List transactions with optional filters and pagination.
    - Admin / Analyst: all transactions
    - Viewer: own transactions only
    """
    filters = TransactionFilter(
        type=type, category=category,
        date_from=date_from, date_to=date_to,
        page=page, page_size=page_size,
    )
    owner_id = _resolve_owner(current_user)
    return transaction_service.get_transactions(db, filters, owner_id=owner_id)


@router.get("/{tx_id}", response_model=TransactionResponse)
def get_transaction(
    tx_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get a single transaction. Admins/Analysts see any; Viewers see own."""
    owner_id = _resolve_owner(current_user)
    return transaction_service.get_transaction_by_id(db, tx_id, owner_id=owner_id)


@router.post("/", response_model=TransactionResponse, status_code=201)
def create_transaction(
    data: TransactionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "analyst")),
):
    """Create a new financial record. Admin / Analyst only."""
    tx = transaction_service.create_transaction(db, data, owner_id=current_user.id)
    log_action(
        db, user_id=current_user.id,
        action="CREATE_TRANSACTION", entity="Transaction", entity_id=tx.id,
        detail=f"type={tx.type} amount={tx.amount} category={tx.category}",
        request=request,
    )
    return tx


@router.patch("/{tx_id}", response_model=TransactionResponse)
def update_transaction(
    tx_id: int,
    data: TransactionUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "analyst")),
):
    """Update a transaction. Admin / Analyst only (own records for analyst)."""
    owner_id = None if current_user.role == UserRole.admin else current_user.id
    tx = transaction_service.update_transaction(db, tx_id, data, owner_id=owner_id)
    log_action(
        db, user_id=current_user.id,
        action="UPDATE_TRANSACTION", entity="Transaction", entity_id=tx.id,
        detail=f"fields={list(data.model_dump(exclude_unset=True).keys())}",
        request=request,
    )
    return tx


@router.delete("/{tx_id}", status_code=204)
def delete_transaction(
    tx_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "analyst")),
):
    """Soft-delete a transaction. Admin / Analyst only (own records for analyst)."""
    owner_id = None if current_user.role == UserRole.admin else current_user.id
    transaction_service.delete_transaction(db, tx_id, owner_id=owner_id)
    log_action(
        db, user_id=current_user.id,
        action="DELETE_TRANSACTION", entity="Transaction", entity_id=tx_id,
        request=request,
    )