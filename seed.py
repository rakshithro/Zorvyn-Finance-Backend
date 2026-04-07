"""
seed.py — Populate the database with realistic sample data for development.

Usage:
    python seed.py

Creates:
  • 1 admin, 2 analysts, 3 viewers
  • ~60 transactions spread over the last 6 months
  • Covers all categories and both income/expense types
"""

import sys
import random
from datetime import date, timedelta
from pathlib import Path

# Make sure project root is on the path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.database import SessionLocal, init_db
from app.models.user import User, UserRole
from app.models.transaction import Transaction, TransactionType, TransactionCategory
from app.core.security import get_password_hash


# ── Sample data ───────────────────────────────────────────────────────────────
USERS = [
    dict(full_name="Admin User",    email="admin@finance.com",    password="admin123",   role=UserRole.admin),
    dict(full_name="Alice Analyst", email="alice@finance.com",    password="analyst123", role=UserRole.analyst),
    dict(full_name="Bob Analyst",   email="bob@finance.com",      password="analyst123", role=UserRole.analyst),
    dict(full_name="Carol Viewer",  email="carol@finance.com",    password="viewer123",  role=UserRole.viewer),
    dict(full_name="David Viewer",  email="david@finance.com",    password="viewer123",  role=UserRole.viewer),
    dict(full_name="Eve Viewer",    email="eve@finance.com",      password="viewer123",  role=UserRole.viewer),
]

INCOME_TEMPLATES = [
    (TransactionCategory.salary,    4500, 6000, "Monthly salary"),
    (TransactionCategory.freelance, 500,  2000, "Freelance project"),
    (TransactionCategory.investment,200,  1500, "Dividend / returns"),
    (TransactionCategory.other,     100,  500,  "Miscellaneous income"),
]

EXPENSE_TEMPLATES = [
    (TransactionCategory.rent,          1200, 2000, "Monthly rent"),
    (TransactionCategory.food,          200,  600,  "Groceries & dining"),
    (TransactionCategory.utilities,     80,   200,  "Electricity / water / internet"),
    (TransactionCategory.transport,     50,   300,  "Fuel / commute"),
    (TransactionCategory.healthcare,    100,  400,  "Medical / pharmacy"),
    (TransactionCategory.entertainment, 30,   150,  "Streaming / outings"),
    (TransactionCategory.education,     50,   300,  "Courses / books"),
    (TransactionCategory.shopping,      100,  500,  "Clothing / electronics"),
    (TransactionCategory.other,         20,   200,  "Miscellaneous expense"),
]


def random_date_in_last_n_months(n: int = 6) -> date:
    end   = date.today()
    start = end - timedelta(days=n * 30)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def seed():
    init_db()
    db = SessionLocal()

    try:
        # ── Wipe existing data ────────────────────────────────────────────────
        db.query(Transaction).delete()
        db.query(User).delete()
        db.commit()
        print("🗑  Cleared existing data.")

        # ── Create users ──────────────────────────────────────────────────────
        user_objs = []
        for u in USERS:
            user = User(
                full_name=u["full_name"],
                email=u["email"],
                hashed_password=get_password_hash(u["password"]),
                role=u["role"],
                is_active=True,
            )
            db.add(user)
            user_objs.append(user)
        db.commit()
        for u in user_objs:
            db.refresh(u)
        print(f"👤 Created {len(user_objs)} users.")

        # ── Create transactions (analysts + admin only) ───────────────────────
        writers = [u for u in user_objs if u.role in (UserRole.admin, UserRole.analyst)]
        txs = []

        for writer in writers:
            # 2–3 income entries per month for 6 months
            for _ in range(random.randint(10, 15)):
                cat, lo, hi, note = random.choice(INCOME_TEMPLATES)
                txs.append(Transaction(
                    amount=round(random.uniform(lo, hi), 2),
                    type=TransactionType.income,
                    category=cat,
                    date=random_date_in_last_n_months(),
                    notes=note,
                    owner_id=writer.id,
                ))
            # 4–6 expense entries per month
            for _ in range(random.randint(20, 25)):
                cat, lo, hi, note = random.choice(EXPENSE_TEMPLATES)
                txs.append(Transaction(
                    amount=round(random.uniform(lo, hi), 2),
                    type=TransactionType.expense,
                    category=cat,
                    date=random_date_in_last_n_months(),
                    notes=note,
                    owner_id=writer.id,
                ))

        db.bulk_save_objects(txs)
        db.commit()
        print(f"💰 Created {len(txs)} transactions.")

        # ── Summary ───────────────────────────────────────────────────────────
        print("\n✅ Seed complete! Credentials:\n")
        for u in USERS:
            print(f"   {u['role'].value:<10}  {u['email']:<28}  password: {u['password']}")
        print()

    finally:
        db.close()


if __name__ == "__main__":
    seed()