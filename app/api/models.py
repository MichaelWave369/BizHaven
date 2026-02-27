from pydantic import BaseModel


class ClientIn(BaseModel):
    name: str
    email: str = ""
    phone: str = ""
    notes: str = ""


class ExpenseIn(BaseModel):
    category: str
    vendor: str
    amount: float
    expense_date: str
    receipt_path: str = ""
    notes: str = ""


class InvoiceIn(BaseModel):
    client_id: int
    job_id: int | None = None
    invoice_number: str
    issue_date: str
    due_date: str
    subtotal: float
    tax: float
    total: float
    notes: str = ""


class PaymentIn(BaseModel):
    invoice_id: int
    amount: float
    method: str
    paid_on: str
    notes: str = ""
