# BizHaven v0.1 — The Local Small Business Haven

> A beautiful, local-first toolkit for freelancers, solo techs, and small crews to run the business side without SaaS lock-in.

![BizHaven Hero Placeholder](docs/screenshots/hero-placeholder.png)

## Why BizHaven?
BizHaven is private by default, offline-capable, and designed to replace monthly-fee tools for the basics of running a small service business.

### Replaces QuickBooks & FreshBooks for:
- Invoicing with payment tracking and partial payment support
- Expense logging and simple tax estimates
- Client CRM and notes
- Contract/document templates and local storage
- Lightweight local AI helper for quoting/invoice/tax guidance

## Stack
- **UI:** Streamlit (dark/noir with warm accent design)
- **Backend:** FastAPI (embedded/local)
- **Storage:** SQLite + local filesystem
- **License:** MIT

## Features
1. **Dashboard**: earnings, upcoming invoices, expenses, outstanding totals.
2. **Invoicing & Payments**: invoice creation, partial payments, reminders-ready status, CSV export.
3. **Expense Tracking**: categorized expense logs + monthly US-friendly tax estimate.
4. **Client CRM**: contacts, notes, linked invoice/job history.
5. **Contracts & Documents**: markdown templates + local file storage.
6. **Local AI Assistant**: offline helper responses for quotes/invoicing/tax prompts.
7. **Triad369 Integration**: Agentora/Memoria bridge placeholders + memory context display.

## Quick Start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python scripts/load_sample_data.py
streamlit run app/ui/streamlit_app.py
```

Optional API server:
```bash
uvicorn app.api.server:app --host 127.0.0.1 --port 8090
```

## Project Structure
```text
app/
  api/               # FastAPI models/routes
  core/              # config and SQLite setup
  data/
    sample/          # sample CSV seed data
    templates/       # invoice/contract templates
  services/          # repository + assistant logic
  ui/                # Streamlit app
scripts/
  load_sample_data.py
triad369.launchpad.json
```

## Screenshots
![Dashboard Placeholder](docs/screenshots/dashboard-placeholder.png)
![Invoicing Placeholder](docs/screenshots/invoicing-placeholder.png)

## Local-first Privacy Model
- Works on local SQLite DB (`data/bizhaven.db`)
- Documents and receipts stored locally
- No cloud dependency required for core workflows

## Triad369 Launchpad
This repo includes `triad369.launchpad.json` for straightforward registration in Triad369-Launchpad.

## Roadmap
- PDF invoice rendering
- Real local LLM adapters (Ollama/llama.cpp)
- Optional encrypted backups
