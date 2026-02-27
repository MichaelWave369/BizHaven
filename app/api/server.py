from pathlib import Path

from fastapi import FastAPI

from app.api.models import AgentTaskIn, ClientIn, ExpenseIn, InvoiceIn, PaymentIn, ProjectIn
from app.core.config import APP_NAME, APP_VERSION
from app.core.database import init_db
from app.services.repository import (
    add_invoice_with_items,
    backup_database,
    dashboard_summary,
    ensure_client_portal_token,
    estimate_tax,
    execute,
    expense_category_breakdown,
    export_tax_summary,
    fetch_all,
    memoria_autosave,
    profit_loss,
    run_recurring_invoices,
    update_invoice_payment_status,
)

app = FastAPI(title=APP_NAME, version=APP_VERSION)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/automation/run-recurring")
def run_recurring() -> dict:
    return {"created": run_recurring_invoices()}


@app.get("/dashboard")
def dashboard() -> dict:
    return dashboard_summary()


@app.get("/reports/profit-loss")
def report_profit_loss(period: str = "monthly") -> list[dict]:
    return profit_loss(period)


@app.get("/reports/expense-categories")
def report_expense_categories() -> list[dict]:
    return expense_category_breakdown()


@app.get("/reports/tax-summary/{year}")
def report_tax_summary(year: str) -> dict:
    out = export_tax_summary(Path("data/exports") / f"tax_summary_{year}.csv", year)
    return {"path": str(out)}


@app.post("/backup")
def backup() -> dict:
    out = backup_database(Path("data/exports/backup_snapshot.json"))
    return {"path": str(out)}


@app.get("/clients")
def clients() -> list[dict]:
    return fetch_all("SELECT * FROM clients ORDER BY created_at DESC")


@app.post("/clients")
def add_client(payload: ClientIn) -> dict:
    cid = execute(
        "INSERT INTO clients (name, email, phone, notes) VALUES (?,?,?,?)",
        (payload.name, payload.email, payload.phone, payload.notes),
    )
    token = ensure_client_portal_token(cid)
    memoria_autosave(cid, f"New client added: {payload.name}", priority=2)
    return {"id": cid, "portal_token": token}


@app.get("/projects")
def projects() -> list[dict]:
    return fetch_all(
        "SELECT p.*, c.name AS client_name FROM projects p LEFT JOIN clients c ON c.id=p.client_id ORDER BY p.created_at DESC"
    )


@app.post("/projects")
def add_project(payload: ProjectIn) -> dict:
    pid = execute(
        "INSERT INTO projects (client_id,name,description,status,start_date,end_date,budget) VALUES (?,?,?,?,?,?,?)",
        (payload.client_id, payload.name, payload.description, payload.status, payload.start_date, payload.end_date, payload.budget),
    )
    memoria_autosave(payload.client_id, f"Project created: {payload.name}", priority=3)
    return {"id": pid}


@app.get("/expenses")
def expenses() -> list[dict]:
    return fetch_all("SELECT * FROM expenses ORDER BY expense_date DESC")


@app.post("/expenses")
def add_expense(payload: ExpenseIn) -> dict:
    eid = execute(
        "INSERT INTO expenses (project_id,category,vendor,amount,expense_date,receipt_path,notes) VALUES (?,?,?,?,?,?,?)",
        (payload.project_id, payload.category, payload.vendor, payload.amount, payload.expense_date, payload.receipt_path, payload.notes),
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


@app.get("/portal/{token}")
def portal_preview(token: str) -> dict:
    client = fetch_all("SELECT * FROM clients WHERE portal_token=?", (token,))
    if not client:
        return {"error": "Invalid token"}
    client_id = client[0]["id"]
    invoices = fetch_all("SELECT invoice_number,due_date,status,total FROM invoices WHERE client_id=? ORDER BY due_date DESC", (client_id,))
    return {"client": client[0]["name"], "invoices": invoices}


@app.post("/invoices")
def add_invoice(payload: InvoiceIn) -> dict:
    iid = add_invoice_with_items(payload.model_dump())
    return {"id": iid}


@app.post("/payments")
def add_payment(payload: PaymentIn) -> dict:
    pid = execute(
        "INSERT INTO payments (invoice_id,amount,method,paid_on,notes) VALUES (?,?,?,?,?)",
        (payload.invoice_id, payload.amount, payload.method, payload.paid_on, payload.notes),
    )
    update_invoice_payment_status(payload.invoice_id)
    return {"id": pid}


@app.post("/agentora/tasks")
def queue_agent_task(payload: AgentTaskIn) -> dict:
    tid = execute(
        "INSERT INTO agent_tasks (client_id,task_type,payload,status) VALUES (?,?,?,?)",
        (payload.client_id, payload.task_type, payload.payload, "queued"),
    )
    return {"id": tid}


@app.get("/tax-estimate/{month}")
def tax(month: str) -> dict:
    return estimate_tax(month)
