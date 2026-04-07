from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException, status
from math import ceil

from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionFilter, PaginatedTransactions


def get_transaction_by_id(db: Session, tx_id: int, owner_id: int | None = None) -> Transaction:
    query = db.query(Transaction).filter(
        Transaction.id == tx_id,
        Transaction.is_deleted == False,
    )
    if owner_id is not None:
        query = query.filter(Transaction.owner_id == owner_id)
    tx = query.first()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return tx


def get_transactions(
    db: Session,
    filters: TransactionFilter,
    owner_id: int | None = None,
) -> PaginatedTransactions:
    query = db.query(Transaction).filter(Transaction.is_deleted == False)

    if owner_id is not None:
        query = query.filter(Transaction.owner_id == owner_id)
    if filters.type:
        query = query.filter(Transaction.type == filters.type)
    if filters.category:
        query = query.filter(Transaction.category == filters.category)
    if filters.date_from:
        query = query.filter(Transaction.date >= filters.date_from)
    if filters.date_to:
        query = query.filter(Transaction.date <= filters.date_to)

    total = query.count()
    offset = (filters.page - 1) * filters.page_size
    items = (
        query.order_by(Transaction.date.desc(), Transaction.id.desc())
        .offset(offset)
        .limit(filters.page_size)
        .all()
    )

    return PaginatedTransactions(
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        total_pages=ceil(total / filters.page_size) if total else 1,
        items=items,
    )


def create_transaction(db: Session, data: TransactionCreate, owner_id: int) -> Transaction:
    dump = data.model_dump(by_alias=False)
    # renaming transaction_date -> date to match 
    dump["date"] = dump.pop("transaction_date", dump.get("date"))
    tx = Transaction(**dump, owner_id=owner_id)
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


def update_transaction(
    db: Session, tx_id: int, data: TransactionUpdate, owner_id: int
) -> Transaction:
    tx = get_transaction_by_id(db, tx_id, owner_id)
    dump = data.model_dump(exclude_unset=True, by_alias=False)
    # rename transaction_date -> date to match 
    if "transaction_date" in dump:
        dump["date"] = dump.pop("transaction_date")
    for field, value in dump.items():
        setattr(tx, field, value)
    db.commit()
    db.refresh(tx)
    return tx


def delete_transaction(db: Session, tx_id: int, owner_id: int) -> None:
    """Soft delete — sets is_deleted = True."""
    tx = get_transaction_by_id(db, tx_id, owner_id)
    tx.is_deleted = True
    db.commit()