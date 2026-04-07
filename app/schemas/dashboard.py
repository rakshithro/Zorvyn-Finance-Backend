from pydantic import BaseModel
from typing import Optional


class CategoryTotal(BaseModel):
    category: str
    total: float
    count: int


class MonthlyTrend(BaseModel):
    year: int
    month: int
    month_name: str
    income: float
    expense: float
    net: float


class RecentTransaction(BaseModel):
    id: int
    amount: float
    type: str
    category: str
    date: str
    notes: Optional[str]

    class Config:
        from_attributes = True


class DashboardSummary(BaseModel):
    total_income: float
    total_expenses: float
    net_balance: float
    total_transactions: int
    income_transactions: int
    expense_transactions: int
    top_expense_category: Optional[str]
    top_income_category: Optional[str]
    category_totals: list[CategoryTotal]
    monthly_trends: list[MonthlyTrend]
    recent_transactions: list[RecentTransaction]