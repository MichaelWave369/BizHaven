from pathlib import Path
import sys
from uuid import uuid4

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.database import init_db
from app.services.repository import add_invoice_with_items, execute


def run() -> None:
    init_db()
    acme_id = execute(
        "INSERT INTO clients (name,email,phone,notes,portal_token) VALUES (?,?,?,?,?)",
        ("Acme Bakery", "hello@acme.test", "555-1000", "Prefers morning calls.", str(uuid4())),
    )
    north_id = execute(
        "INSERT INTO clients (name,email,phone,notes,portal_token) VALUES (?,?,?,?,?)",
        ("Northside Repairs", "ops@northside.test", "555-2000", "Needs monthly maintenance invoices.", str(uuid4())),
    )

    p1 = execute(
        "INSERT INTO projects (client_id,name,description,status,start_date,budget) VALUES (?,?,?,?,date('now'),?)",
        (acme_id, "Website Refresh", "Modernize website + SEO basics", "active", 3000),
    )

    iid = add_invoice_with_items(
        {
            "client_id": acme_id,
            "project_id": p1,
            "invoice_number": "INV-1001",
            "issue_date": "2026-01-01",
            "due_date": "2026-01-15",
            "items": [
                {"description": "Design", "quantity": 4, "rate": 150, "taxable": True},
                {"description": "Development", "quantity": 6, "rate": 100, "taxable": True},
            ],
            "tax_rate": 0.08,
            "discount": 50,
            "custom_fields": {"po_number": "PO-44"},
            "notes": "Website refresh milestone billing",
            "reminder_days": 3,
            "recurring_rule": "monthly",
            "next_run_date": "2026-02-01",
        }
    )

    execute("INSERT INTO payments (invoice_id,amount,method,paid_on,notes) VALUES (?,?,?,?,?)", (iid, 600, "bank", "2026-01-15", "Partial deposit"))
    execute("INSERT INTO expenses (project_id,category,vendor,amount,expense_date,notes) VALUES (?,?,?,?,?,?)", (p1, "Software", "Hosting Co", 49, "2026-01-10", "Monthly infra"))
    execute("INSERT INTO memories (client_id,memory,source,priority) VALUES (?,?,?,?)", (acme_id, "Client wants minimal pastel branding and quick iterations.", "memoria", 3))

    execute(
        "INSERT INTO agent_tasks (client_id,task_type,payload,status) VALUES (?,?,?,?)",
        (north_id, "check_in", '{"channel":"email","cadence":"monthly"}', "queued"),
    )


if __name__ == "__main__":
    run()
