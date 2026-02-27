from __future__ import annotations

from app.services.repository import fetch_all


def _memory_context() -> str:
    tips = fetch_all("SELECT memory FROM memories ORDER BY priority DESC, created_at DESC LIMIT 5")
    return " ".join(t["memory"] for t in tips) if tips else "No stored memory context yet."


def generate_quote(client_name: str, scope: str, budget: float) -> str:
    return (
        f"Quote for {client_name}\n"
        f"Scope: {scope}\n"
        f"Estimated budget: ${budget:,.2f}\n"
        "Milestones: 50% deposit, 30% midpoint, 20% final delivery.\n"
        "Timeline: 2-4 weeks depending on revision cycles.\n"
        "Terms: Net-15 final payment, support window 30 days."
    )


def generate_contract(client_name: str, project_name: str, fee: float) -> str:
    return (
        f"SERVICE AGREEMENT\nClient: {client_name}\nProject: {project_name}\nFee: ${fee:,.2f}\n"
        "Payment: 50% upfront, remainder Net-15.\n"
        "IP Transfer: upon full payment.\n"
        "Termination: either party with written notice.\n"
        "Signature: __________________ Date: __________"
    )


def generate_follow_up_email(client_name: str, invoice_number: str, amount_due: float) -> str:
    return (
        f"Subject: Friendly reminder for invoice {invoice_number}\n\n"
        f"Hi {client_name},\n"
        f"Just a quick reminder that ${amount_due:,.2f} is currently outstanding on invoice {invoice_number}.\n"
        "Please let me know if you need a copy or payment link.\n\n"
        "Thank you!"
    )


def ask_bizhaven(prompt: str) -> str:
    prompt_l = prompt.lower()
    if "quote" in prompt_l:
        return "Use value-based tiers: Essential, Growth, Premium. Include deliverables and payment milestones."
    if "contract" in prompt_l:
        return "Keep clauses for scope limits, revision count, late fees, and IP transfer on full payment."
    if "tax" in prompt_l:
        return "For US freelancers, reserve 20-30% of net income and track software, mileage, and home-office deductions."
    if "follow up" in prompt_l or "email" in prompt_l:
        return "Keep reminders polite and concise, include invoice number, amount due, and clear next step."

    return f"Ask BizHaven (local mode): {prompt}\nContext: {_memory_context()}"
