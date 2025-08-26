
# Natural Language Query Translator (NLQT)

**Live App:** https://lnkd.in/dnqEzcib

NLQT lets anyone query a PostgreSQL database in plain English. It:
- Normalizes the user’s question into database-friendly phrasing.
- Builds a strict, schema-aware prompt for **Google Gemini**.
- Generates **read‑only** PostgreSQL SQL.
- Validates it for safety.
- Executes it and returns structured results via a sleek Flask UI (table/cards).

---

## Table of Contents
- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Demo & Screens](#demo--screens)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Normalization Engine](#normalization-engine)
- [LLM Prompt Guardrails](#llm-prompt-guardrails)
- [SQL Safety & DB Hardening](#sql-safety--db-hardening)
- [Frontend UX](#frontend-ux)
- [Observability & Limits](#observability--limits)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

---

## Features
- **Natural language → SQL** using **Google Gemini** with deterministic generation (temperature 0).
- **Input normalization** (synonyms, comparators, “lakh/crore” money parsing, qualitative terms → thresholds, logical operator unification).
- **SQL validator** blocks DDL/DML, semicolons, and non-SELECT/WITH statements.
- **PostgreSQL** querying with **statement timeout** and safe defaults.
- **Interactive UI** with chat-like flow, results in **Table** and **Card** views, and a **Schema** modal.
- **Schema auto-discovery** at startup (public schema tables/columns).

---

## Architecture Overview

**Flow:**

1. `normalizer.py` → canonicalizes user text (synonyms, thresholds, comparators, implicit references).
2. `prompt_builder.py` → crafts a *strict* prompt with schema and guardrails.
3. `gemini_client.py` → calls Google Gemini and returns SQL (temperature 0).
4. `sql_validator.py` → blocks unsafe/invalid statements.
5. `db.py` → executes read-only SQL on PostgreSQL with a per-connection statement timeout.
6. `app.py` → Flask API and pages (`/`, `/query`, `/health`, `/nlp-query`).

---

## Demo & Screens
- **Live:** https://lnkd.in/dnqEzcib  
- UI includes a friendly assistant (“Nelly”), chat history, and session-persistent results.  
- Switch between **Table** and **Cards**. Reviews open in modal or inline chips.

> Tip: Add screenshots/GIFs of `index.html` and `nlp-query.html` once deployed screenshots are ready.

---

## Quick Start

### Requirements
- Python 3.10+
- PostgreSQL 13+
- A Google Gemini API key

### Install
```bash
git clone https://github.com/CollegeCompass2025-26/Natural-Language-Query-Translator-NLQT-.git
cd Natural-Language-Query-Translator-NLQT-
python -m venv .venv && source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
```

If you don’t have `requirements.txt`, use this minimal set:
```txt
flask
python-dotenv
psycopg2-binary
sqlparse
google-generativeai
psutil
gunicorn  # optional, for production
```

### Run
Create `.env` (see below), then:
```bash
python app.py
# or for prod-style run
gunicorn -w 2 -b 0.0.0.0:${PORT:-5000} app:app
```

Open: http://localhost:5000

---

## Configuration

Create a `.env` file at the project root:

```env
# Google Gemini
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-pro

# PostgreSQL
DB_URL=postgresql://user:password@host:5432/dbname
STATEMENT_TIMEOUT=10000  # ms

# Server
PORT=5000
```

> **Note**  
> - `DB_URL` and `STATEMENT_TIMEOUT` are read by `db.py` and applied per connection.  
> - `PORT` is read by `app.py` when running directly (`__main__`).

---

## API Reference

### `GET /`
- Renders **Home** (`templates/index.html`).

### `GET /query`
- Renders **Query Dashboard** (`templates/nlp-query.html`).

### `GET /health`
- Returns `{ "ok": true, "schema_tables": ["table1", "table2", ...] }`

### `POST /nlp-query`
**Body:**
```json
{ "query": "top affordable colleges in maharashtra with good placement" }
```
**Success (200):**
```json
{
  "error": false,
  "type": "success",
  "message": "Your result has been generated.",
  "rows": [ { "college": "...", "...": "...", "alumni_reviews": [ { "id": 1, "name": "...", "review": "...", "rating": 4.2 } ] } ],
  "sql": "SELECT ... LIMIT 500"
}
```

## Examples

**User:** “Top affordable colleges in Maharashtra with good placement”

**Normalized (illustrative):**
```
top rating state = maharashtra affordable placement > 6 AND ug_fee < 300000
```

**Generated SQL (illustrative — follows prompt rules):**
```sql
SELECT
  cp.*,
  COALESCE(
    JSON_AGG(
      JSON_BUILD_OBJECT('id', ar.id, 'name', ar.name, 'review', ar.review, 'rating', ar.rating)
    ) FILTER (WHERE ar.id IS NOT NULL),
    '[]'
  ) AS alumni_reviews
FROM college_profiles cp
LEFT JOIN alumni_reviews ar
  ON LOWER(cp.college) = LOWER(ar.college)
WHERE
  LOWER(cp.state) = LOWER('maharashtra')
  AND cp.placement > 6
  AND cp.ug_fee < 300000
  AND cp.rating > 8
GROUP BY
  cp.college, cp.state, cp.stream, cp.ug_fee, cp.pg_fee, cp.rating,
  cp.academic, cp.accommodation, cp.faculty, cp.infrastructure, cp.placement, cp.social_life
LIMIT 500
```

---

## Troubleshooting

- **“DB_URL is not set. Put it in your .env.”**  
  Add a valid `DB_URL` to `.env`.
- **`missing_column`/`missing_table`**  
  The generated SQL referenced a column/table outside your public schema. Check naming, update synonyms, or adjust the schema.
- **`unsafe_sql`**  
  Validator blocked a non-read-only or multi-statement query.
- **`timeout`**  
  Increase `STATEMENT_TIMEOUT` or add tighter filters / indexes.
- **No rows**  
  Widen filters or confirm data presence.

---

## Project Structure

```
app.py
db.py
gemini_client.py
normalizer.py
prompt_builder.py
sql_validator.py
templates/
  ├── index.html
  └── nlp-query.html
static/
  └── images/ (icons used by the UI)
```

---

## Contributing
- Open an issue with a clear repro.
- Keep PRs focused; include tests where practical.
- For prompt/normalizer changes, document the rationale in PR description.

---

## License
Add a `LICENSE` file (recommendation: **MIT** for permissive use).
