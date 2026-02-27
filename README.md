# BizHaven v0.2 — The Local Small Business Haven

> A polished, local-first business cockpit for freelancers, solo techs, and small crews who want pro workflows without monthly SaaS fees.

![BizHaven Hero Placeholder](docs/screenshots/hero-placeholder.png)

## Replaces QuickBooks & FreshBooks (Core Freelancer Workflows)
BizHaven is American-focused, private by default, and offline-capable.

- Advanced invoicing (multi-line, discounts, tax, custom fields)
- Recurring billing with local auto-reminder scheduling
- Expense tracking + tax-ready exports
- Client CRM + project management + portal preview
- Contract/doc templates and local document vault
- Local AI assistant for quotes, contracts, follow-ups, and Q&A
- Triad369 bridge points for Agentora and Memoria

## Stack
- **UI:** Streamlit (mobile-friendly, dark/light mode)
- **API:** FastAPI (embedded/local)
- **Storage:** SQLite + local files
- **License:** MIT

## v0.2 Upgrade Highlights
1. **Recurring & Advanced Invoicing**
   - Recurring schedules (weekly/monthly/quarterly)
   - Multi-item invoice lines, discount, tax rate, custom fields
   - Partial/full payment tracking + reminders table

2. **Reporting & Insights**
   - Monthly/quarterly profit & loss reports
   - Expense category breakdown charts
   - Tax-ready annual CSV export

3. **Smarter AI Assistant**
   - “Ask BizHaven” conversational helper
   - Generate quote drafts, contract drafts, and follow-up emails

4. **Client & Project Management**
   - Projects linked to clients, invoices, and expenses
   - Local client portal preview token and route

5. **Polish & Usability**
   - Dark/light mode toggle
   - keyboard shortcut hints in sidebar
   - Backup/export tools for local resilience

6. **Triad369 Integration**
   - Agentora task queue model for automated client communication
   - Memoria autosave hooks for important events

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
  api/               # FastAPI endpoints + request models
  core/              # config + SQLite schema/migrations
  data/
    sample/          # sample CSV data
    templates/       # contract/invoice templates
  services/          # repository, analytics, assistant logic
  ui/                # Streamlit app screens
scripts/
  load_sample_data.py
data/
  documents/
  receipts/
  exports/
triad369.launchpad.json
```

## Screenshots
![Dashboard Placeholder](docs/screenshots/dashboard-placeholder.png)
![Advanced Invoicing Placeholder](docs/screenshots/invoicing-placeholder.png)
![Reporting Placeholder](docs/screenshots/reporting-placeholder.png)

## Local-first Privacy Model
- Works entirely with local SQLite DB (`data/bizhaven.db`)
- Receipts/contracts/docs stored locally on disk
- No mandatory cloud accounts

## Triad369 Launchpad
`triad369.launchpad.json` is included for easy registration in Triad369-Launchpad.

## Roadmap
- Native PDF invoice rendering
- Optional local LLM providers (Ollama/llama.cpp)
- End-to-end encrypted backup bundles
