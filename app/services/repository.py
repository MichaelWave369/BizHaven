from __future__ import annotations

import csv
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.core.database import get_conn


def fetch_all(query: str, params: tuple = ()) -> list[dict[str, Any]]:
    with get_conn() as conn:
        return conn.execute(query, params).fetchall()


def fetch_one(query: str, params: tuple = ()) -> dict[str, Any] | None:
    with get_conn() as conn:
        return conn.execute(query, params).fetchone()


def execute(query: str, params: tuple = ()) -> int:
    with get_conn() as conn:
        cur = conn.execute(query, params)
        return cur.lastrowid


def ensure_client_portal_token(client_id: int) -> str:
    client = fetch_one("SELECT portal_token FROM clients WHERE id=?", (client_id,))
    if client and client.get("portal_token"):
        return client["portal_token"]
    token = str(uuid4())
    execute("UPDATE clients SET portal_token=? WHERE id=?", (token, client_id))
    return token


def add_invoice_with_items(payload: dict[str, Any]) -> int:
    custom_fields = json.dumps(payload.get("custom_fields", {}))
    discount = float(payload.get("discount", 0.0))
    subtotal = 0.0
    taxable_total = 0.0
    for item in payload.get("items", []):
        amount = float(item["quantity"]) * float(item["rate"])
        subtotal += amount
        if item.get("taxable", True):
            taxable_total += amount
    taxable_total = max(taxable_total - discount, 0)
    tax = taxable_total * float(payload.get("tax_rate", 0.0))
    total = max(subtotal - discount, 0) + tax

    iid = execute(
        """INSERT INTO invoices (client_id,project_id,job_id,invoice_number,issue_date,due_date,status,discount,custom_fields,subtotal,tax,total,notes,reminder_days,recurring_rule,next_run_date)
        VALUES (?,?,?,?,?,'sent',?,?,?,?,?,?,?,?,?,?)""",
        (
            payload["client_id"],
            payload.get("project_id"),
            payload.get("job_id"),
            payload["invoice_number"],
            payload["issue_date"],
            payload["due_date"],
            discount,
            custom_fields,
            subtotal,
            tax,
            total,
            payload.get("notes", ""),
            int(payload.get("reminder_days", 3)),
            payload.get("recurring_rule", "none"),
            payload.get("next_run_date"),
        ),
    )

    for item in payload.get("items", []):
        amount = float(item["quantity"]) * float(item["rate"])
        execute(
            "INSERT INTO invoice_items (invoice_id,description,quantity,rate,amount,taxable) VALUES (?,?,?,?,?,?)",
            (iid, item["description"], item["quantity"], item["rate"], amount, 1 if item.get("taxable", True) else 0),
        )

    if payload.get("reminder_days"):
        reminder_date = datetime.fromisoformat(payload["due_date"]).date() - timedelta(days=int(payload["reminder_days"]))
        execute("INSERT INTO reminders (invoice_id,reminder_date,channel,sent) VALUES (?,?,?,0)", (iid, str(reminder_date), "email"))

    return iid


def update_invoice_payment_status(invoice_id: int) -> None:
    execute(
        """
        UPDATE invoices
        SET status = CASE
            WHEN (SELECT COALESCE(SUM(amount),0) FROM payments WHERE invoice_id=?) >= total THEN 'paid'
            ELSE 'partial'
        END
        WHERE id=?
        """,
        (invoice_id, invoice_id),
    )


def run_recurring_invoices(today: date | None = None) -> int:
    today = today or date.today()
    due = fetch_all(
        "SELECT * FROM invoices WHERE recurring_rule IN ('weekly','monthly','quarterly') AND next_run_date IS NOT NULL AND next_run_date <= ?",
        (str(today),),
    )
    created = 0
    for inv in due:
        items = fetch_all("SELECT description, quantity, rate, taxable FROM invoice_items WHERE invoice_id=?", (inv["id"],))
        next_number = f"{inv['invoice_number']}-R{today.strftime('%Y%m%d')}"
        next_run = today + timedelta(days={"weekly": 7, "monthly": 30, "quarterly": 90}[inv["recurring_rule"]])
        add_invoice_with_items(
            {
                "client_id": inv["client_id"],
                "project_id": inv.get("project_id"),
                "job_id": inv.get("job_id"),
                "invoice_number": next_number,
                "issue_date": str(today),
                "due_date": str(today + timedelta(days=14)),
                "items": items,
                "tax_rate": (inv["tax"] / inv["subtotal"]) if inv["subtotal"] else 0.0,
                "discount": inv.get("discount", 0),
                "custom_fields": json.loads(inv.get("custom_fields") or "{}"),
                "notes": inv.get("notes", ""),
                "reminder_days": inv.get("reminder_days", 3),
                "recurring_rule": inv["recurring_rule"],
                "next_run_date": str(next_run),
            }
        )
        execute("UPDATE invoices SET next_run_date=? WHERE id=?", (str(next_run), inv["id"]))
        created += 1
    return created


def dashboard_summary() -> dict[str, Any]:
    earnings = fetch_one("SELECT COALESCE(SUM(amount),0) AS total FROM payments")
    upcoming = fetch_one("SELECT COUNT(*) AS count FROM invoices WHERE status IN ('sent','partial') AND due_date >= ?", (str(date.today()),))
    expenses = fetch_one("SELECT COALESCE(SUM(amount),0) AS total FROM expenses")
    unpaid = fetch_one("SELECT COALESCE(SUM(total),0) AS total FROM invoices WHERE status IN ('sent','partial')")
    projects = fetch_one("SELECT COUNT(*) AS count FROM projects WHERE status='active'")
    return {
        "earnings": earnings["total"],
        "upcoming_invoices": upcoming["count"],
        "expenses": expenses["total"],
        "outstanding": unpaid["total"],
        "active_projects": projects["count"],
    }


def estimate_tax(month: str, tax_rate: float = 0.22) -> dict[str, float]:
    income = fetch_one("SELECT COALESCE(SUM(amount),0) AS total FROM payments WHERE strftime('%Y-%m', paid_on)=?", (month,))["total"]
    costs = fetch_one("SELECT COALESCE(SUM(amount),0) AS total FROM expenses WHERE strftime('%Y-%m', expense_date)=?", (month,))["total"]
    taxable = max(income - costs, 0)
    return {"income": income, "costs": costs, "taxable": taxable, "estimate": taxable * tax_rate}


def profit_loss(period: str = "monthly") -> list[dict[str, Any]]:
    income_rows = fetch_all("SELECT strftime('%Y-%m', paid_on) AS period, COALESCE(SUM(amount),0) AS income FROM payments GROUP BY 1")
    expense_rows = fetch_all("SELECT strftime('%Y-%m', expense_date) AS period, COALESCE(SUM(amount),0) AS expenses FROM expenses GROUP BY 1")
    merged: dict[str, dict[str, Any]] = {}
    for row in income_rows:
        merged[row["period"]] = {"period": row["period"], "income": row["income"], "expenses": 0.0}
    for row in expense_rows:
        merged.setdefault(row["period"], {"period": row["period"], "income": 0.0, "expenses": 0.0})
        merged[row["period"]]["expenses"] = row["expenses"]

    output = []
    for k in sorted(merged.keys()):
        val = merged[k]
        if period == "quarterly":
            y, m = val["period"].split("-")
            q = ((int(m) - 1) // 3) + 1
            val["period"] = f"{y}-Q{q}"
        val["profit"] = val["income"] - val["expenses"]
        output.append(val)
    return output


def expense_category_breakdown() -> list[dict[str, Any]]:
    return fetch_all("SELECT category, COALESCE(SUM(amount),0) AS total FROM expenses GROUP BY category ORDER BY total DESC")


def export_tax_summary(path: Path, year: str) -> Path:
    rows = fetch_all(
        "SELECT expense_date, category, vendor, amount, notes FROM expenses WHERE strftime('%Y', expense_date)=? ORDER BY expense_date",
        (year,),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["expense_date", "category", "vendor", "amount", "notes"])
        writer.writeheader()
        writer.writerows(rows)
    return path


def backup_database(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = fetch_all("SELECT name FROM sqlite_master WHERE type='table'")
    snapshot = {"tables": [r["name"] for r in rows], "created_at": datetime.utcnow().isoformat()}
    path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    return path


def memoria_autosave(client_id: int, memory: str, priority: int = 2) -> int:
    return execute("INSERT INTO memories (client_id,memory,source,priority) VALUES (?,?,?,?)", (client_id, memory, "bizhaven", priority))
