# Jugendlohn Tracker - Architecture

## Overview

A lightweight web app for parents to track their children's expenses (Jugendlohn = Swiss/German youth allowance). Built with Flask, stores data in CSV, runs in Docker.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Browser (Client)                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │  index    │  │ history  │  │ summary  │  setup   │
│  │  (entry)  │  │ (list)   │  │ (stats)  │  (wizard)│
│  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
│       │ HTML forms / vanilla JS                      │
└───────┼──────────────┼──────────────┼───────────────┘
        │    HTTP       │              │
┌───────┼──────────────┼──────────────┼───────────────┐
│       ▼              ▼              ▼               │
│  ┌─────────────────────────────────────────────┐    │
│  │              Flask (app.py)                  │    │
│  │                                              │    │
│  │  ┌────────────┐  ┌────────────┐             │    │
│  │  │   Routes    │  │   i18n     │             │    │
│  │  │  (views)    │  │ (DE / EN)  │             │    │
│  │  └──────┬─────┘  └────────────┘             │    │
│  │         │                                    │    │
│  │  ┌──────┴─────────────────────────┐         │    │
│  │  │       Data Layer               │         │    │
│  │  │  ┌──────────┐  ┌───────────┐  │         │    │
│  │  │  │ CSV Ops   │  │ Config    │  │         │    │
│  │  │  │ (expenses)│  │ (JSON)    │  │         │    │
│  │  │  └─────┬────┘  └─────┬─────┘  │         │    │
│  │  └────────┼──────────────┼────────┘         │    │
│  └───────────┼──────────────┼──────────────────┘    │
│              ▼              ▼                        │
│  ┌───────────────────────────────────┐              │
│  │    jugendlohn_data (named volume)  │              │
│  │   expenses.csv    config.json     │              │
│  └───────────────────────────────────┘              │
│                  Docker Container                    │
└─────────────────────────────────────────────────────┘
```

## Tech Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Backend | Flask (Python 3.12) | Minimal, full HTML/CSS control, trivial to containerize |
| Frontend | HTML + CSS + vanilla JS | No build step, mobile-first responsive, works on any browser |
| Storage | CSV + JSON | No database needed for household-scale (~500 entries/year) |
| Container | Docker + docker-compose | Named volume for data persistence; configurable port via `PORT` |
| i18n | DE/EN toggle | Translation dict in Python, injected into templates |

## Design Principles

1. **Single-file backend**: All Python logic in `app.py`. The app is small enough that modules add complexity without benefit.
2. **No database**: CSV + JSON avoids ORM, migrations, and database containers.
3. **Server-rendered HTML**: Jinja2 templates with standard form POST. No SPA or JS framework.
4. **Mobile-first responsive**: CSS targets mobile by default, enhances for desktop via media queries.
5. **Configuration over code**: Names, currency, budget, categories, language all in `config.json`, configured via setup wizard.

## Data Flow

### Adding an Expense
```
User taps buttons → JS sets hidden inputs → Form POST /api/expense
  → Flask validates fields
  → Acquires threading.Lock
  → Appends row to expenses.csv
  → Releases lock
  → Redirects to / with flash "Saved!"
```

### Viewing Summary
```
User visits /summary?month=2026-03
  → Flask reads all rows from expenses.csv
  → Filters by month
  → Aggregates with collections.defaultdict
  → Computes budget remaining if configured
  → Renders summary.html
```

### First-Run Flow
```
User visits any route
  → @app.before_request checks config.json
  → If missing: redirect to /setup
  → User fills wizard → POST /setup
  → Saves config.json → Redirects to /
```

## File Structure

```
jugendlohn_tracker/
├── app.py                  # Flask app: routes, CSV ops, config, i18n
├── requirements.txt        # Flask, pytest
├── Dockerfile
├── docker-compose.yml
├── data/                   # Persisted via Docker named volume (jugendlohn_data)
│   ├── config.json         # User configuration (created by setup wizard)
│   └── expenses.csv        # Expense data
├── templates/
│   ├── base.html           # Layout with nav bar, flash messages
│   ├── setup.html          # First-run configuration wizard
│   ├── index.html          # Expense entry form
│   ├── history.html        # Filterable expense list
│   └── summary.html        # Monthly summary with budget bars
├── static/
│   ├── style.css           # Mobile-first responsive styles
│   ├── app.js              # Button groups, validation, UI interactions
│   └── manifest.json       # PWA manifest for "Add to Home Screen"
├── tests/
│   ├── conftest.py         # Shared fixtures
│   ├── test_config.py      # Config load/save unit tests
│   ├── test_csv_ops.py     # CSV operations unit tests
│   ├── test_summary.py     # Summary aggregation unit tests
│   └── test_routes.py      # Integration tests for all routes
└── docs/
    └── ARCHITECTURE.md     # This file
```

## CSV Schema

| Column | Type | Description |
|--------|------|-------------|
| id | string | `uuid4().hex[:8]` - unique identifier |
| timestamp | ISO 8601 | Exact moment of entry |
| date | YYYY-MM-DD | Expense date (auto-filled, user-editable) |
| name | string | Child's name |
| category | string | Category key (e.g., "food", "clothing") |
| amount | float | Amount with 2 decimal places |
| note | string | Optional free text |

## Thread Safety

A `threading.Lock` guards all CSV read/write operations. Sufficient for single-household use with minimal concurrency.

## i18n

Translations live in `TRANSLATIONS` dict in `app.py`. A Jinja2 context processor injects `t()` into all templates. Templates use `{{ t('key') }}` for all user-visible strings. Language toggle saves preference to `config.json`.

## Security

- No authentication (designed for home network use)
- CSV formula injection prevention (strips leading `=`, `+`, `-`, `@`)
- Jinja2 auto-escaping prevents XSS
- File paths never constructed from user input

## Running

### Local
```bash
pip install -r requirements.txt
python app.py
# Visit http://localhost:5000
```

### Docker
```bash
# Default port (5000)
docker-compose up --build

# Custom port via environment variable
PORT=8080 docker-compose up --build
# or define PORT in a .env file next to docker-compose.yml
```

Data is stored in the Docker-managed named volume `jugendlohn_data`. To inspect it:
```bash
docker volume inspect jugendlohn_data
```

### Tests
```bash
pytest tests/ -v
```
