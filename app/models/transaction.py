from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Enum, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, date
import enum

from app.db.database import Base

"""transaction.py - defines the Transaction model representing financial transactions in the system. Each transaction has an amount, type (income or expense), category, date, and optional notes. Transactions are linked to a User (the owner) and support soft deletion via the is_deleted flag. The model also includes created_at and updated_at timestamps for auditing purposes."""

class TransactionType(str, enum.Enum):
    income = "income"
    expense = "expense"

  

class TransactionCategory(str, enum.Enum):
    salary = "salary"
    freelance = "freelance"
    investment = "investment"
    food = "food"
    rent = "rent"
    utilities = "utilities"
    transport = "transport"
    healthcare = "healthcare"
    entertainment = "entertainment"
    education = "education"
    shopping = "shopping"
    other = "other"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    category = Column(Enum(TransactionCategory), nullable=False)
    date = Column(Date, nullable=False, default=date.today)
    notes = Column(Text, nullable=True)
    is_deleted = Column(Boolean, default=False)  # soft delete

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="transactions")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)