from pydantic import BaseModel, Field


class ClientIn(BaseModel):
    name: str
    email: str = ""
    phone: str = ""
    notes: str = ""


class ProjectIn(BaseModel):
    client_id: int
    name: str
    description: str = ""
    status: str = "active"
    start_date: str = ""
    end_date: str = ""
    budget: float = 0.0


class ExpenseIn(BaseModel):
    category: str
    vendor: str
    amount: float
    expense_date: str
    project_id: int | None = None
    receipt_path: str = ""
    notes: str = ""


class InvoiceItemIn(BaseModel):
    description: str
    quantity: float
    rate: float
    taxable: bool = True


class InvoiceIn(BaseModel):
    client_id: int
    project_id: int | None = None
    job_id: int | None = None
    invoice_number: str
    issue_date: str
    due_date: str
    items: list[InvoiceItemIn] = Field(default_factory=list)
    tax_rate: float = 0.0
    discount: float = 0.0
    custom_fields: dict = Field(default_factory=dict)
    notes: str = ""
    reminder_days: int = 3
    recurring_rule: str = "none"
    next_run_date: str | None = None


class PaymentIn(BaseModel):
    invoice_id: int
    amount: float
    method: str
    paid_on: str
    notes: str = ""


class AgentTaskIn(BaseModel):
    client_id: int
    task_type: str
    payload: str
