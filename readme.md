# Jewelry Pricing Tool

A lightweight Flask-based jewelry pricing system for internal team use.

## Features

* Add, edit, delete, and duplicate jewelry products
* Formula-based pricing engine
* Auto-generated product codes
* Shared rates and settings
* Dashboard with search, filter, and sorting
* Excel export
* PostgreSQL support for team use, with SQLite fallback for local testing

## Tech Stack

* Backend: Python and Flask
* Database: PostgreSQL on Render
* Local fallback: SQLite
* Frontend: HTML, CSS, JavaScript
* Excel Export: pandas and openpyxl

## Render Setup

Set these environment variables in your Render web service:

```text
DATABASE_URL=your Render PostgreSQL internal database URL
SECRET_KEY=any long random secret text
```

Use this Render start command:

```bash
gunicorn app:app
```

The app creates these PostgreSQL tables automatically on startup:

* `products`
* `app_settings`

Keep the real database password only in Render environment variables. Do not commit it into GitHub.

## Local Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Run locally:

```bash
python app.py
```

Open:

```text
http://localhost:8080
```

Without `DATABASE_URL`, the app uses local `database.db` and `config.json`.

## Migrate Existing Local Data

To copy products from local `database.db` into PostgreSQL:

PowerShell:

```powershell
$env:DATABASE_URL="your Render PostgreSQL URL"
python scripts/migrate_sqlite_to_postgres.py
```

Command Prompt:

```bat
set DATABASE_URL=your Render PostgreSQL URL
python scripts\migrate_sqlite_to_postgres.py
```

The migration skips duplicate `product_code` values.

## Configuration

Use the Settings page to update shared PostgreSQL settings:

* Gold rate
* Diamond rate
* Default margin
* Currency symbol
* Platinum rate
* Labor rate
* Setting charge
* Gold loss
* Rhodium

When PostgreSQL is enabled, these settings are saved in the shared `app_settings` table.

## Important Note

This version does not include login accounts yet. Before sharing the Render URL widely, add authentication or restrict access to trusted team members.
