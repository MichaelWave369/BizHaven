from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path

import streamlit as st

from app.core.database import init_db
from app.services.assistant import ask_bizhaven, generate_contract, generate_follow_up_email, generate_quote
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

init_db()
st.set_page_config(page_title="BizHaven", page_icon="🏡", layout="wide")

if "theme" not in st.session_state:
    st.session_state.theme = "Dark"

mode = st.sidebar.toggle("Light mode", value=st.session_state.theme == "Light")
st.session_state.theme = "Light" if mode else "Dark"

if st.session_state.theme == "Dark":
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

st.title("🏡 BizHaven v0.2")
st.caption("Local-first small business toolkit — private, offline-capable, and American-focused.")
st.sidebar.caption("Shortcuts: Alt+1 Dashboard • Alt+2 Invoices • Alt+3 Expenses • Alt+4 CRM/Projects")

menu = st.sidebar.radio(
    "Navigate",
    [
        "Dashboard",
        "Recurring & Advanced Invoicing",
        "Reporting & Insights",
        "Client & Project Management",
        "Contracts & Documents",
        "Ask BizHaven (AI)",
        "Backup & Export",
        "Triad369 Integration",
    ],
)

if menu == "Dashboard":
    created = run_recurring_invoices()
    if created:
        st.success(f"Auto-generated {created} recurring invoice(s).")
    s = dashboard_summary()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Earnings", f"${s['earnings']:,.2f}")
    c2.metric("Upcoming", s["upcoming_invoices"])
    c3.metric("Expenses", f"${s['expenses']:,.2f}")
    c4.metric("Outstanding", f"${s['outstanding']:,.2f}")
    c5.metric("Active Projects", s["active_projects"])

    st.subheader("Pending Reminders")
    reminders = fetch_all(
        "SELECT r.reminder_date, i.invoice_number, c.name AS client_name FROM reminders r JOIN invoices i ON i.id=r.invoice_id JOIN clients c ON c.id=i.client_id WHERE r.sent=0 ORDER BY r.reminder_date"
    )
    st.dataframe(reminders, use_container_width=True)

elif menu == "Recurring & Advanced Invoicing":
    clients = fetch_all("SELECT id, name FROM clients ORDER BY name")
    projects = fetch_all("SELECT id, name FROM projects ORDER BY name")
    client_map = {f"{c['name']} (#{c['id']})": c["id"] for c in clients}
    project_map = {"None": None} | {f"{p['name']} (#{p['id']})": p["id"] for p in projects}

    st.subheader("Create Advanced Invoice")
    with st.form("advanced_invoice"):
        choice = st.selectbox("Client", ["-- No Clients --"] + list(client_map.keys()))
        project_choice = st.selectbox("Project", list(project_map.keys()))
        invoice_number = st.text_input("Invoice Number", value=f"INV-{date.today().strftime('%Y%m%d')}")
        issue_date = st.date_input("Issue Date", value=date.today())
        due_date = st.date_input("Due Date", value=date.today())
        recurring_rule = st.selectbox("Recurring", ["none", "weekly", "monthly", "quarterly"])
        next_run_date = st.date_input("Next recurring run", value=date.today()) if recurring_rule != "none" else None
        reminder_days = st.number_input("Reminder days before due", min_value=0, value=3)
        discount = st.number_input("Discount ($)", min_value=0.0, value=0.0)
        tax_rate = st.number_input("Tax rate (e.g. 0.0825)", min_value=0.0, max_value=0.3, value=0.0825)
        st.markdown("**Line Items**")
        col1, col2, col3, col4 = st.columns(4)
        d1 = col1.text_input("Item 1 description", value="Service work")
        q1 = col2.number_input("Qty 1", min_value=0.0, value=1.0)
        r1 = col3.number_input("Rate 1", min_value=0.0, value=150.0)
        t1 = col4.checkbox("Taxable 1", value=True)
        col1, col2, col3, col4 = st.columns(4)
        d2 = col1.text_input("Item 2 description", value="Materials")
        q2 = col2.number_input("Qty 2", min_value=0.0, value=0.0)
        r2 = col3.number_input("Rate 2", min_value=0.0, value=0.0)
        t2 = col4.checkbox("Taxable 2", value=True)
        custom_po = st.text_input("Custom field: PO Number")
        notes = st.text_area("Notes", value="Thank you for your business.")
        submitted = st.form_submit_button("Save Invoice")

    if submitted and choice != "-- No Clients --":
        items = [
            {"description": d1, "quantity": q1, "rate": r1, "taxable": t1},
            {"description": d2, "quantity": q2, "rate": r2, "taxable": t2},
        ]
        items = [i for i in items if i["description"] and i["quantity"] > 0]
        iid = add_invoice_with_items(
            {
                "client_id": client_map[choice],
                "project_id": project_map[project_choice],
                "invoice_number": invoice_number,
                "issue_date": str(issue_date),
                "due_date": str(due_date),
                "items": items,
                "tax_rate": tax_rate,
                "discount": discount,
                "custom_fields": {"po_number": custom_po},
                "notes": notes,
                "reminder_days": int(reminder_days),
                "recurring_rule": recurring_rule,
                "next_run_date": str(next_run_date) if next_run_date else None,
            }
        )
        st.success(f"Invoice #{iid} created.")

    invoices = fetch_all(
        "SELECT i.*, c.name AS client_name, COALESCE((SELECT SUM(amount) FROM payments p WHERE p.invoice_id=i.id),0) AS paid FROM invoices i LEFT JOIN clients c ON c.id=i.client_id ORDER BY i.created_at DESC"
    )
    st.dataframe(invoices, use_container_width=True)

    if invoices:
        st.subheader("Record Partial/Full Payment")
        id_map = {f"{inv['invoice_number']} ({inv['client_name']})": inv["id"] for inv in invoices}
        with st.form("payment_form"):
            inv_choice = st.selectbox("Invoice", list(id_map.keys()))
            amount = st.number_input("Amount", min_value=0.0, key="pay_amt")
            method = st.selectbox("Method", ["cash", "bank", "card", "check", "zelle", "ach"])
            paid_on = st.date_input("Paid On", value=date.today(), key="paid_on")
            submit_payment = st.form_submit_button("Record Payment")
        if submit_payment:
            iid = id_map[inv_choice]
            execute("INSERT INTO payments (invoice_id,amount,method,paid_on) VALUES (?,?,?,?)", (iid, amount, method, str(paid_on)))
            update_invoice_payment_status(iid)
            st.success("Payment recorded.")

elif menu == "Reporting & Insights":
    st.subheader("Profit & Loss")
    period = st.segmented_control("Period", ["monthly", "quarterly"], default="monthly")
    rows = profit_loss(period)
    st.dataframe(rows, use_container_width=True)
    if rows:
        chart_data = {"period": [r["period"] for r in rows], "profit": [r["profit"] for r in rows]}
        st.bar_chart(chart_data, x="period", y="profit")

    st.subheader("Expense Categories")
    cats = expense_category_breakdown()
    st.dataframe(cats, use_container_width=True)
    if cats:
        pie_df = {"category": [c["category"] for c in cats], "total": [c["total"] for c in cats]}
        st.bar_chart(pie_df, x="category", y="total")

    st.subheader("Tax-ready Export")
    year = st.text_input("Year", value=str(date.today().year))
    if st.button("Export Tax Summary CSV"):
        path = export_tax_summary(Path("data/exports") / f"tax_summary_{year}.csv", year)
        st.success(f"Saved: {path}")
        st.download_button("Download tax summary", path.read_text(encoding="utf-8"), file_name=path.name)

elif menu == "Client & Project Management":
    left, right = st.columns(2)
    with left:
        st.subheader("Add Client")
        with st.form("client_form"):
            name = st.text_input("Name")
            email = st.text_input("Email")
            phone = st.text_input("Phone")
            notes = st.text_area("Notes")
            submitted = st.form_submit_button("Save Client")
        if submitted and name:
            cid = execute("INSERT INTO clients (name,email,phone,notes) VALUES (?,?,?,?)", (name, email, phone, notes))
            token = ensure_client_portal_token(cid)
            memoria_autosave(cid, f"Client note: {notes or 'No notes'}", priority=2)
            st.success(f"Client saved. Portal token: {token}")

    with right:
        st.subheader("Add Project")
        clients = fetch_all("SELECT id, name FROM clients ORDER BY name")
        c_map = {f"{c['name']} (#{c['id']})": c["id"] for c in clients}
        with st.form("project_form"):
            client_choice = st.selectbox("Client", list(c_map.keys()) if c_map else ["No clients"])
            pname = st.text_input("Project Name")
            pdesc = st.text_area("Description")
            pbudget = st.number_input("Budget", min_value=0.0)
            pstatus = st.selectbox("Status", ["active", "on_hold", "completed"])
            psubmit = st.form_submit_button("Save Project")
        if psubmit and c_map and pname:
            execute(
                "INSERT INTO projects (client_id,name,description,status,start_date,budget) VALUES (?,?,?,?,?,?)",
                (c_map[client_choice], pname, pdesc, pstatus, str(date.today()), pbudget),
            )
            memoria_autosave(c_map[client_choice], f"Project updated: {pname}", priority=3)
            st.success("Project created.")

    st.subheader("Clients + Projects")
    clients = fetch_all("SELECT * FROM clients ORDER BY created_at DESC")
    projects = fetch_all("SELECT p.*, c.name AS client_name FROM projects p LEFT JOIN clients c ON c.id=p.client_id ORDER BY p.created_at DESC")
    st.dataframe(clients, use_container_width=True)
    st.dataframe(projects, use_container_width=True)

    st.subheader("Client Portal Preview")
    if clients:
        cmap = {c["name"]: c for c in clients}
        cselect = st.selectbox("Select Client", list(cmap.keys()))
        token = ensure_client_portal_token(cmap[cselect]["id"])
        invoices = fetch_all("SELECT invoice_number,due_date,status,total FROM invoices WHERE client_id=? ORDER BY due_date DESC", (cmap[cselect]["id"],))
        st.code(f"/portal/{token}")
        st.dataframe(invoices, use_container_width=True)

elif menu == "Contracts & Documents":
    st.subheader("Templates")
    templates = list(Path("app/data/templates").glob("*.md"))
    selected = st.selectbox("Template", [t.name for t in templates]) if templates else None
    if selected:
        st.code((Path("app/data/templates") / selected).read_text(encoding="utf-8"), language="markdown")

    st.subheader("AI Draft Generator")
    c_name = st.text_input("Client")
    p_name = st.text_input("Project")
    fee = st.number_input("Fee", min_value=0.0, value=1500.0)
    if st.button("Generate Contract Draft") and c_name and p_name:
        st.text_area("Draft", value=generate_contract(c_name, p_name, fee), height=240)

    uploaded = st.file_uploader("Store document locally")
    if uploaded:
        out = Path("data/documents") / uploaded.name
        out.write_bytes(uploaded.read())
        st.success(f"Stored at {out}")

elif menu == "Ask BizHaven (AI)":
    st.subheader("Ask BizHaven")
    prompt = st.text_area("Ask business, tax, quote, contract, or follow-up questions")
    if st.button("Ask") and prompt:
        st.success(ask_bizhaven(prompt))

    st.subheader("Quick Generators")
    c1, c2 = st.columns(2)
    with c1:
        q_client = st.text_input("Quote Client")
        q_scope = st.text_area("Quote Scope", value="Website + monthly maintenance")
        q_budget = st.number_input("Quote Budget", min_value=0.0, value=2000.0)
        if st.button("Generate Quote") and q_client:
            st.code(generate_quote(q_client, q_scope, q_budget))
    with c2:
        e_client = st.text_input("Email Client")
        e_inv = st.text_input("Invoice #", value="INV-1001")
        e_due = st.number_input("Amount Due", min_value=0.0, value=500.0)
        if st.button("Generate Follow-up") and e_client:
            st.code(generate_follow_up_email(e_client, e_inv, e_due))

elif menu == "Backup & Export":
    st.subheader("Data Backups")
    if st.button("Create backup snapshot"):
        path = backup_database(Path("data/exports/backup_snapshot.json"))
        st.success(f"Backup created: {path}")
    st.subheader("Export Invoices CSV")
    invoices = fetch_all("SELECT * FROM invoices ORDER BY created_at DESC")
    if invoices:
        csv_path = Path("data/exports/invoices_export.csv")
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=invoices[0].keys())
            writer.writeheader()
            writer.writerows(invoices)
        st.download_button("Download invoices export", csv_path.read_text(encoding="utf-8"), file_name=csv_path.name)

elif menu == "Triad369 Integration":
    st.subheader("Agentora + Memoria")
    st.write("Local bridge queue for agent-powered client communication and memory autosave.")

    tasks = fetch_all("SELECT a.*, c.name AS client_name FROM agent_tasks a LEFT JOIN clients c ON c.id=a.client_id ORDER BY a.created_at DESC")
    st.dataframe(tasks, use_container_width=True)

    clients = fetch_all("SELECT id, name FROM clients ORDER BY name")
    cmap = {f"{c['name']} (#{c['id']})": c["id"] for c in clients}
    with st.form("agent_task_form"):
        client_sel = st.selectbox("Client", list(cmap.keys()) if cmap else ["No clients"])
        ttype = st.selectbox("Agent task", ["follow_up", "check_in", "payment_reminder", "proposal_nudge"])
        payload = st.text_area("Payload", value=json.dumps({"channel": "email", "tone": "friendly"}, indent=2))
        q = st.form_submit_button("Queue task")
    if q and cmap:
        execute("INSERT INTO agent_tasks (client_id,task_type,payload,status) VALUES (?,?,?,?)", (cmap[client_sel], ttype, payload, "queued"))
        memoria_autosave(cmap[client_sel], f"Queued Agentora task: {ttype}", priority=2)
        st.success("Task queued.")

    memories = fetch_all("SELECT m.*, c.name as client_name FROM memories m LEFT JOIN clients c ON c.id=m.client_id ORDER BY m.priority DESC, m.created_at DESC")
    st.dataframe(memories, use_container_width=True)

    st.code(
        """{
  "agentora_login": "local-placeholder-token-flow",
  "agent_task_queue": "agent_tasks table",
  "memoria_autosave": "enabled on client/project/task events"
}""",
        language="json",
    )

st.caption("Tip: Keep BizHaven local on your own machine for maximum privacy.")
