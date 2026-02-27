from __future__ import annotations

from datetime import date
from typing import Any

from app.core.database import get_conn


def fetch_all(query: str, params: tuple = ()) -> list[dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.execute(query, params)
        return cur.fetchall()


def fetch_one(query: str, params: tuple = ()) -> dict[str, Any] | None:
    with get_conn() as conn:
        cur = conn.execute(query, params)
        return cur.fetchone()


def execute(query: str, params: tuple = ()) -> int:
    with get_conn() as conn:
        cur = conn.execute(query, params)
        return cur.lastrowid


def dashboard_summary() -> dict[str, Any]:
    earnings = fetch_one("SELECT COALESCE(SUM(amount),0) AS total FROM payments")
    upcoming = fetch_one(
        "SELECT COUNT(*) AS count FROM invoices WHERE status IN ('sent','partial') AND due_date >= ?",
        (str(date.today()),),
    )
    expenses = fetch_one("SELECT COALESCE(SUM(amount),0) AS total FROM expenses")
    unpaid = fetch_one(
        "SELECT COALESCE(SUM(total),0) AS total FROM invoices WHERE status IN ('sent','partial')"
    )
    return {
        "earnings": earnings["total"],
        "upcoming_invoices": upcoming["count"],
        "expenses": expenses["total"],
        "outstanding": unpaid["total"],
    }


def estimate_tax(month: str, tax_rate: float = 0.22) -> dict[str, float]:
    income = fetch_one(
        "SELECT COALESCE(SUM(amount),0) AS total FROM payments WHERE strftime('%Y-%m', paid_on)=?",
        (month,),
    )["total"]
    costs = fetch_one(
        "SELECT COALESCE(SUM(amount),0) AS total FROM expenses WHERE strftime('%Y-%m', expense_date)=?",
        (month,),
    )["total"]
    taxable = max(income - costs, 0)
    return {"income": income, "costs": costs, "taxable": taxable, "estimate": taxable * tax_rate}
