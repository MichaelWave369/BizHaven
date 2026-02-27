from fastapi import FastAPI

from app.api.models import ClientIn, ExpenseIn, InvoiceIn, PaymentIn
from app.core.config import APP_NAME, APP_VERSION
from app.core.database import init_db
from app.services.repository import dashboard_summary, estimate_tax, execute, fetch_all

app = FastAPI(title=APP_NAME, version=APP_VERSION)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/dashboard")
def dashboard() -> dict:
    return dashboard_summary()


@app.get("/clients")
def clients() -> list[dict]:
    return fetch_all("SELECT * FROM clients ORDER BY created_at DESC")


@app.post("/clients")
def add_client(payload: ClientIn) -> dict:
    cid = execute(
        "INSERT INTO clients (name, email, phone, notes) VALUES (?,?,?,?)",
        (payload.name, payload.email, payload.phone, payload.notes),
    )
    return {"id": cid}


@app.get("/expenses")
def expenses() -> list[dict]:
    return fetch_all("SELECT * FROM expenses ORDER BY expense_date DESC")


@app.post("/expenses")
def add_expense(payload: ExpenseIn) -> dict:
    eid = execute(
        "INSERT INTO expenses (category,vendor,amount,expense_date,receipt_path,notes) VALUES (?,?,?,?,?,?)",
        (
            payload.category,
            payload.vendor,
            payload.amount,
            payload.expense_date,
            payload.receipt_path,
            payload.notes,
        ),
    )
    return {"id": eid}


@app.get("/invoices")
def invoices() -> list[dict]:
    return fetch_all(
        """
        SELECT i.*, c.name as client_name,
        COALESCE((SELECT SUM(amount) FROM payments p WHERE p.invoice_id=i.id),0) AS paid
        FROM invoices i LEFT JOIN clients c ON c.id=i.client_id
        ORDER BY i.created_at DESC
        """
    )


@app.post("/invoices")
def add_invoice(payload: InvoiceIn) -> dict:
    iid = execute(
        """INSERT INTO invoices (client_id,job_id,invoice_number,issue_date,due_date,status,subtotal,tax,total,notes)
        VALUES (?,?,?,?,?,'sent',?,?,?,?)""",
        (
            payload.client_id,
            payload.job_id,
            payload.invoice_number,
            payload.issue_date,
            payload.due_date,
            payload.subtotal,
            payload.tax,
            payload.total,
            payload.notes,
        ),
    )
    return {"id": iid}


@app.post("/payments")
def add_payment(payload: PaymentIn) -> dict:
    pid = execute(
        "INSERT INTO payments (invoice_id,amount,method,paid_on,notes) VALUES (?,?,?,?,?)",
        (payload.invoice_id, payload.amount, payload.method, payload.paid_on, payload.notes),
    )
    execute(
        """
        UPDATE invoices
        SET status = CASE
            WHEN (SELECT COALESCE(SUM(amount),0) FROM payments WHERE invoice_id=?) >= total THEN 'paid'
            ELSE 'partial'
        END
        WHERE id=?
        """,
        (payload.invoice_id, payload.invoice_id),
    )
    return {"id": pid}


@app.get("/tax-estimate/{month}")
def tax(month: str) -> dict:
    return estimate_tax(month)
