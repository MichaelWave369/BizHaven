from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.database import init_db
from app.services.repository import execute


def run() -> None:
    init_db()
    execute("INSERT INTO clients (name,email,phone,notes) VALUES (?,?,?,?)", ("Acme Bakery", "hello@acme.test", "555-1000", "Prefers morning calls."))
    execute("INSERT INTO clients (name,email,phone,notes) VALUES (?,?,?,?)", ("Northside Repairs", "ops@northside.test", "555-2000", "Needs monthly maintenance invoices."))
    execute(
        "INSERT INTO invoices (client_id,invoice_number,issue_date,due_date,status,subtotal,tax,total,notes) VALUES (?,?,date('now'),date('now','+14 day'),'sent',?,?,?,?)",
        (1, "INV-1001", 1200, 96, 1296, "Website refresh"),
    )
    execute("INSERT INTO payments (invoice_id,amount,method,paid_on,notes) VALUES (?,?,?,?,?)", (1, 600, "bank", "2026-01-15", "Partial deposit"))
    execute("INSERT INTO expenses (category,vendor,amount,expense_date,notes) VALUES (?,?,?,?,?)", ("Software", "Hosting Co", 49, "2026-01-10", "Monthly infra"))
    execute("INSERT INTO memories (client_id,memory,source) VALUES (?,?,?)", (1, "Client wants minimal pastel branding and quick iterations.", "memoria"))


if __name__ == "__main__":
    run()
