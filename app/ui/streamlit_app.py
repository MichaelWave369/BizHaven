from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import streamlit as st

from app.core.database import init_db
from app.services.assistant import local_assistant_reply
from app.services.repository import dashboard_summary, estimate_tax, execute, fetch_all

init_db()
st.set_page_config(page_title="BizHaven", page_icon="🏡", layout="wide")

st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(160deg, #111217, #191b24); color: #f5f5f5; }
    .stMetric { background: #1f2230; border-radius: 12px; padding: 8px; }
    div.stButton > button { background:#e3a74f; color:#111; border:none; border-radius:10px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🏡 BizHaven v0.1")
st.caption("The local small business haven — private, offline-capable, and subscription-free.")

menu = st.sidebar.radio(
    "Navigate",
    [
        "Dashboard",
        "Invoicing & Payments",
        "Expense Tracking",
        "Client CRM",
        "Contracts & Documents",
        "Local AI Assistant",
        "Triad369 Integration",
    ],
)

if menu == "Dashboard":
    s = dashboard_summary()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Earnings", f"${s['earnings']:,.2f}")
    c2.metric("Upcoming Invoices", s["upcoming_invoices"])
    c3.metric("Expenses", f"${s['expenses']:,.2f}")
    c4.metric("Outstanding", f"${s['outstanding']:,.2f}")

    st.subheader("Quick Actions")
    st.info("Create invoice • Log expense • Add client • Draft contract")

elif menu == "Invoicing & Payments":
    st.subheader("Create Invoice")
    clients = fetch_all("SELECT id, name FROM clients ORDER BY name")
    client_map = {f"{c['name']} (#{c['id']})": c["id"] for c in clients}
    with st.form("invoice_form"):
        choice = st.selectbox("Client", ["-- No Clients --"] + list(client_map.keys()))
        invoice_number = st.text_input("Invoice Number", value=f"INV-{date.today().strftime('%Y%m%d')}")
        issue_date = st.date_input("Issue Date", value=date.today())
        due_date = st.date_input("Due Date", value=date.today())
        subtotal = st.number_input("Subtotal", min_value=0.0)
        tax = st.number_input("Tax", min_value=0.0)
        notes = st.text_area("Notes", value="Thanks for your business!")
        submitted = st.form_submit_button("Save Invoice")
    if submitted and choice != "-- No Clients --":
        execute(
            """INSERT INTO invoices (client_id,invoice_number,issue_date,due_date,status,subtotal,tax,total,notes)
            VALUES (?,?,?,?,'sent',?,?,?,?)""",
            (
                client_map[choice],
                invoice_number,
                str(issue_date),
                str(due_date),
                subtotal,
                tax,
                subtotal + tax,
                notes,
            ),
        )
        st.success("Invoice created.")

    st.subheader("Invoices")
    invoices = fetch_all(
        "SELECT i.*, c.name AS client_name, COALESCE((SELECT SUM(amount) FROM payments p WHERE p.invoice_id=i.id),0) AS paid FROM invoices i LEFT JOIN clients c ON c.id=i.client_id ORDER BY i.created_at DESC"
    )
    st.dataframe(invoices, use_container_width=True)

    if invoices:
        st.subheader("Record Payment")
        id_map = {f"{inv['invoice_number']} ({inv['client_name']})": inv["id"] for inv in invoices}
        with st.form("payment_form"):
            inv_choice = st.selectbox("Invoice", list(id_map.keys()))
            amount = st.number_input("Amount", min_value=0.0, key="pay_amt")
            method = st.selectbox("Method", ["cash", "bank", "card", "check"])
            paid_on = st.date_input("Paid On", value=date.today(), key="paid_on")
            submit_payment = st.form_submit_button("Record Payment")
        if submit_payment:
            iid = id_map[inv_choice]
            execute(
                "INSERT INTO payments (invoice_id,amount,method,paid_on) VALUES (?,?,?,?)",
                (iid, amount, method, str(paid_on)),
            )
            execute(
                "UPDATE invoices SET status=CASE WHEN (SELECT COALESCE(SUM(amount),0) FROM payments WHERE invoice_id=?)>=total THEN 'paid' ELSE 'partial' END WHERE id=?",
                (iid, iid),
            )
            st.success("Payment recorded.")

        csv_path = Path("data/invoices_export.csv")
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=invoices[0].keys())
            writer.writeheader()
            writer.writerows(invoices)
        st.download_button("Export CSV", csv_path.read_text(), file_name="invoices_export.csv")

elif menu == "Expense Tracking":
    st.subheader("Log Expense")
    with st.form("expense_form"):
        category = st.selectbox("Category", ["Software", "Travel", "Equipment", "Meals", "Marketing", "Other"])
        vendor = st.text_input("Vendor")
        amount = st.number_input("Amount", min_value=0.0)
        expense_date = st.date_input("Date", value=date.today())
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Save Expense")
    if submitted:
        execute(
            "INSERT INTO expenses (category,vendor,amount,expense_date,notes) VALUES (?,?,?,?,?)",
            (category, vendor, amount, str(expense_date), notes),
        )
        st.success("Expense added.")

    expenses = fetch_all("SELECT * FROM expenses ORDER BY expense_date DESC")
    st.dataframe(expenses, use_container_width=True)

    month = st.text_input("Tax Estimate Month (YYYY-MM)", value=date.today().strftime("%Y-%m"))
    t = estimate_tax(month)
    st.info(f"Income: ${t['income']:,.2f} | Costs: ${t['costs']:,.2f} | Taxable: ${t['taxable']:,.2f} | Est. Tax: ${t['estimate']:,.2f}")

elif menu == "Client CRM":
    st.subheader("Add Client")
    with st.form("client_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Save Client")
    if submitted and name:
        execute("INSERT INTO clients (name,email,phone,notes) VALUES (?,?,?,?)", (name, email, phone, notes))
        st.success("Client saved.")

    clients = fetch_all(
        "SELECT c.*, (SELECT COUNT(*) FROM invoices i WHERE i.client_id=c.id) AS invoice_count, (SELECT COUNT(*) FROM jobs j WHERE j.client_id=c.id) AS jobs_count FROM clients c ORDER BY c.created_at DESC"
    )
    st.dataframe(clients, use_container_width=True)

elif menu == "Contracts & Documents":
    st.subheader("Contract Templates")
    templates = list(Path("app/data/templates").glob("*.md"))
    if templates:
        selected = st.selectbox("Template", [t.name for t in templates])
        st.code((Path("app/data/templates") / selected).read_text(encoding="utf-8"), language="markdown")
    st.caption("E-sign placeholder: capture typed name + date and mark signed status.")

    uploaded = st.file_uploader("Store document locally")
    if uploaded:
        out = Path("data/documents") / uploaded.name
        out.write_bytes(uploaded.read())
        st.success(f"Stored at {out}")

elif menu == "Local AI Assistant":
    st.subheader("Offline Assistant")
    prompt = st.text_area("Ask for quote, invoice, or tax guidance")
    if st.button("Ask") and prompt:
        st.success(local_assistant_reply(prompt))

elif menu == "Triad369 Integration":
    st.subheader("Triad369 / Agentora / Memoria")
    st.write("Status: local development bridge enabled.")
    st.code(
        """{
  "agentora_login": "placeholder-token-flow",
  "memoria_pull": "SELECT memory FROM memories WHERE client_id=:client_id"
}""",
        language="json",
    )
    memories = fetch_all(
        "SELECT m.*, c.name as client_name FROM memories m LEFT JOIN clients c ON c.id=m.client_id ORDER BY m.created_at DESC"
    )
    st.dataframe(memories, use_container_width=True)
