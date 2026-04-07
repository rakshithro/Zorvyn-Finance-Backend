from pydantic import BaseModel, Field, field_validator
from typing import Optional
import datetime as dt
from app.models.transaction import TransactionType, TransactionCategory


class TransactionCreate(BaseModel):
    amount: float = Field(..., gt=0, description="Amount must be positive")
    type: TransactionType
    category: TransactionCategory
    transaction_date: dt.date = Field(default_factory=dt.date.today, alias="date")
    notes: Optional[str] = Field(None, max_length=500)

    model_config = {"populate_by_name": True}

    @field_validator("amount")
    @classmethod
    def round_amount(cls, v: float) -> float:
        return round(v, 2)


class TransactionUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    type: Optional[TransactionType] = None
    category: Optional[TransactionCategory] = None
    transaction_date: Optional[dt.date] = Field(None, alias="date")
    notes: Optional[str] = Field(None, max_length=500)

    model_config = {"populate_by_name": True}


class TransactionResponse(BaseModel):
    id: int
    amount: float
    type: TransactionType
    category: TransactionCategory
    date: dt.date
    notes: Optional[str]
    owner_id: int
    created_at: dt.datetime

    model_config = {"from_attributes": True}


class TransactionFilter(BaseModel):
    type: Optional[TransactionType] = None
    category: Optional[TransactionCategory] = None
    date_from: Optional[dt.date] = None
    date_to: Optional[dt.date] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class PaginatedTransactions(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: list[TransactionResponse]