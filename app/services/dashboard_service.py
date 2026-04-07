from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import date
import calendar

from app.models.transaction import Transaction, TransactionType
from app.schemas.dashboard import DashboardSummary, CategoryTotal, MonthlyTrend, RecentTransaction


def get_dashboard_summary(db: Session, owner_id: int | None = None) -> DashboardSummary:
    base_query = db.query(Transaction).filter(Transaction.is_deleted == False)
    if owner_id:
        base_query = base_query.filter(Transaction.owner_id == owner_id)

    # ── Totals and counts ─
    income_row = (
        base_query.filter(Transaction.type == TransactionType.income)
        .with_entities(func.coalesce(func.sum(Transaction.amount), 0.0), func.count())
        .first()
    )
    expense_row = (
        base_query.filter(Transaction.type == TransactionType.expense)
        .with_entities(func.coalesce(func.sum(Transaction.amount), 0.0), func.count())
        .first()
    )

    total_income = round(income_row[0], 2)
    income_count = income_row[1]
    total_expenses = round(expense_row[0], 2)
    expense_count = expense_row[1]
    net_balance = round(total_income - total_expenses, 2)

    # ── Category totals -
    category_rows = (
        base_query.with_entities(
            Transaction.category,
            func.sum(Transaction.amount).label("total"),
            func.count().label("cnt"),
        )
        .group_by(Transaction.category)
        .all()
    )
    category_totals = [
        CategoryTotal(category=r.category, total=round(r.total, 2), count=r.cnt)
        for r in category_rows
    ]

    # Top categories for income and expense
    expense_cats = (
        base_query.filter(Transaction.type == TransactionType.expense)
        .with_entities(Transaction.category, func.sum(Transaction.amount).label("total"))
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
        .first()
    )
    income_cats = (
        base_query.filter(Transaction.type == TransactionType.income)
        .with_entities(Transaction.category, func.sum(Transaction.amount).label("total"))
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
        .first()
    )

    # ── (transactions for last 6 months) ─
    monthly_rows = (
        base_query.with_entities(
            extract("year", Transaction.date).label("yr"),
            extract("month", Transaction.date).label("mo"),
            Transaction.type,
            func.sum(Transaction.amount).label("total"),
        )
        .group_by("yr", "mo", Transaction.type)
        .order_by("yr", "mo")
        .all()
    )

    
    trend_map: dict[tuple, dict] = {}
    for row in monthly_rows:
        key = (int(row.yr), int(row.mo))
        if key not in trend_map:
            trend_map[key] = {"income": 0.0, "expense": 0.0}
        if row.type == TransactionType.income:
            trend_map[key]["income"] = round(row.total, 2)
        else:
            trend_map[key]["expense"] = round(row.total, 2)

    monthly_trends = [
        MonthlyTrend(
            year=yr,
            month=mo,
            month_name=calendar.month_abbr[mo],
            income=vals["income"],
            expense=vals["expense"],
            net=round(vals["income"] - vals["expense"], 2),
        )
        for (yr, mo), vals in sorted(trend_map.items())
    ]

    # ── Recent transactions (last 10) ─
    recent = (
        base_query.order_by(Transaction.date.desc(), Transaction.id.desc())
        .limit(10)
        .all()
    )
    recent_txs = [
        RecentTransaction(
            id=t.id,
            amount=t.amount,
            type=t.type,
            category=t.category,
            date=str(t.date),
            notes=t.notes,
        )
        for t in recent
    ]

    return DashboardSummary(
        total_income=total_income,
        total_expenses=total_expenses,
        net_balance=net_balance,
        total_transactions=income_count + expense_count,
        income_transactions=income_count,
        expense_transactions=expense_count,
        top_expense_category=expense_cats.category if expense_cats else None,
        top_income_category=income_cats.category if income_cats else None,
        category_totals=category_totals,
        monthly_trends=monthly_trends,
        recent_transactions=recent_txs,
    )