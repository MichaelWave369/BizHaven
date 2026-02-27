import sqlite3
from contextlib import contextmanager

from app.core.config import DB_PATH, DOCS_DIR, RECEIPTS_DIR


def _dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def ensure_storage() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)


def _add_column_if_missing(conn: sqlite3.Connection, table: str, column: str, col_type: str) -> None:
    cols = [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")


def init_db() -> None:
    ensure_storage()
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                notes TEXT,
                portal_token TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'active',
                start_date TEXT,
                end_date TEXT,
                budget REAL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(client_id) REFERENCES clients(id)
            );

            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                project_id INTEGER,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'open',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(client_id) REFERENCES clients(id),
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );

            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                project_id INTEGER,
                job_id INTEGER,
                invoice_number TEXT UNIQUE,
                issue_date TEXT,
                due_date TEXT,
                status TEXT DEFAULT 'draft',
                discount REAL DEFAULT 0,
                custom_fields TEXT DEFAULT '{}',
                subtotal REAL DEFAULT 0,
                tax REAL DEFAULT 0,
                total REAL DEFAULT 0,
                notes TEXT,
                reminder_days INTEGER DEFAULT 3,
                recurring_rule TEXT DEFAULT 'none',
                next_run_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(client_id) REFERENCES clients(id),
                FOREIGN KEY(project_id) REFERENCES projects(id),
                FOREIGN KEY(job_id) REFERENCES jobs(id)
            );

            CREATE TABLE IF NOT EXISTS invoice_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER,
                description TEXT,
                quantity REAL,
                rate REAL,
                amount REAL,
                taxable INTEGER DEFAULT 1,
                FOREIGN KEY(invoice_id) REFERENCES invoices(id)
            );

            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER,
                amount REAL,
                method TEXT,
                paid_on TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(invoice_id) REFERENCES invoices(id)
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                category TEXT,
                vendor TEXT,
                amount REAL,
                expense_date TEXT,
                receipt_path TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );

            CREATE TABLE IF NOT EXISTS contracts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                project_id INTEGER,
                title TEXT,
                body TEXT,
                signed INTEGER DEFAULT 0,
                file_path TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(client_id) REFERENCES clients(id),
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );

            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                memory TEXT,
                source TEXT DEFAULT 'memoria',
                priority INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(client_id) REFERENCES clients(id)
            );

            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER,
                reminder_date TEXT,
                channel TEXT DEFAULT 'email',
                sent INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(invoice_id) REFERENCES invoices(id)
            );

            CREATE TABLE IF NOT EXISTS agent_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                task_type TEXT,
                payload TEXT,
                status TEXT DEFAULT 'queued',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(client_id) REFERENCES clients(id)
            );
            """
        )

        _add_column_if_missing(conn, "clients", "portal_token", "TEXT")
        _add_column_if_missing(conn, "jobs", "project_id", "INTEGER")
        _add_column_if_missing(conn, "invoices", "project_id", "INTEGER")
        _add_column_if_missing(conn, "invoices", "discount", "REAL DEFAULT 0")
        _add_column_if_missing(conn, "invoices", "custom_fields", "TEXT DEFAULT '{}' ")
        _add_column_if_missing(conn, "invoices", "reminder_days", "INTEGER DEFAULT 3")
        _add_column_if_missing(conn, "invoices", "recurring_rule", "TEXT DEFAULT 'none'")
        _add_column_if_missing(conn, "invoices", "next_run_date", "TEXT")
        _add_column_if_missing(conn, "invoice_items", "taxable", "INTEGER DEFAULT 1")
        _add_column_if_missing(conn, "expenses", "project_id", "INTEGER")
        _add_column_if_missing(conn, "contracts", "project_id", "INTEGER")
        _add_column_if_missing(conn, "memories", "priority", "INTEGER DEFAULT 1")


@contextmanager
def get_conn():
    ensure_storage()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = _dict_factory
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
