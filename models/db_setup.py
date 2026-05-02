import json
import os
import sqlite3
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database.db"
CONFIG_PATH = BASE_DIR / "config.json"
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()


def is_postgres():
    return DATABASE_URL.startswith(("postgres://", "postgresql://"))


class DatabaseConnection:
    def __init__(self, raw_connection, postgres=False):
        self.raw_connection = raw_connection
        self.postgres = postgres

    def execute(self, statement, params=None):
        cursor = self.raw_connection.cursor()
        if self.postgres:
            statement = statement.replace("?", "%s")
        cursor.execute(statement, params or ())
        return cursor

    def commit(self):
        self.raw_connection.commit()

    def rollback(self):
        self.raw_connection.rollback()

    def close(self):
        self.raw_connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        if exc_type:
            self.rollback()
        self.close()


def get_connection():
    if is_postgres():
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return DatabaseConnection(conn, postgres=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return DatabaseConnection(conn)


def load_default_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
        return json.load(config_file)


def load_settings():
    if not is_postgres():
        return load_default_config()

    init_db()
    config = load_default_config()
    with get_connection() as conn:
        rows = conn.execute("SELECT key, value FROM app_settings").fetchall()
    for row in rows:
        key = row["key"]
        value = row["value"]
        if key == "currency_symbol":
            config[key] = value
        else:
            try:
                config[key] = float(value)
            except (TypeError, ValueError):
                config[key] = value
    return config


def save_settings(config):
    if not is_postgres():
        with open(CONFIG_PATH, "w", encoding="utf-8") as config_file:
            json.dump(config, config_file, indent=2, ensure_ascii=False)
        return

    init_db()
    with get_connection() as conn:
        for key, value in config.items():
            conn.execute(
                """
                INSERT INTO app_settings (key, value)
                VALUES (?, ?)
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
                """,
                (key, str(value)),
            )
        conn.commit()


def init_db():
    with get_connection() as conn:
        if is_postgres():
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id SERIAL PRIMARY KEY,
                    product_code TEXT UNIQUE NOT NULL,
                    client_name TEXT NOT NULL DEFAULT '',
                    category TEXT NOT NULL,
                    metal_type TEXT NOT NULL,
                    metal_weight DOUBLE PRECISION NOT NULL,
                    diamond_weight DOUBLE PRECISION NOT NULL,
                    diamond_pcs INTEGER NOT NULL DEFAULT 0,
                    diamond_rate DOUBLE PRECISION NOT NULL,
                    making_charges DOUBLE PRECISION NOT NULL,
                    labor_rate DOUBLE PRECISION NOT NULL DEFAULT 0,
                    setting_charge_per_pc DOUBLE PRECISION NOT NULL DEFAULT 0,
                    gold_loss DOUBLE PRECISION NOT NULL DEFAULT 0,
                    rhodium DOUBLE PRECISION NOT NULL DEFAULT 0,
                    extra_charges DOUBLE PRECISION NOT NULL DEFAULT 0,
                    margin DOUBLE PRECISION NOT NULL,
                    final_price DOUBLE PRECISION NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            existing_columns = {
                row["column_name"]
                for row in conn.execute(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'products'
                    """
                ).fetchall()
            }
            migrations = {
                "client_name": "ALTER TABLE products ADD COLUMN client_name TEXT NOT NULL DEFAULT ''",
                "diamond_pcs": "ALTER TABLE products ADD COLUMN diamond_pcs INTEGER NOT NULL DEFAULT 0",
                "labor_rate": "ALTER TABLE products ADD COLUMN labor_rate DOUBLE PRECISION NOT NULL DEFAULT 0",
                "setting_charge_per_pc": "ALTER TABLE products ADD COLUMN setting_charge_per_pc DOUBLE PRECISION NOT NULL DEFAULT 0",
                "gold_loss": "ALTER TABLE products ADD COLUMN gold_loss DOUBLE PRECISION NOT NULL DEFAULT 0",
                "rhodium": "ALTER TABLE products ADD COLUMN rhodium DOUBLE PRECISION NOT NULL DEFAULT 0",
                "extra_charges": "ALTER TABLE products ADD COLUMN extra_charges DOUBLE PRECISION NOT NULL DEFAULT 0",
            }
        else:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_code TEXT UNIQUE NOT NULL,
                    client_name TEXT NOT NULL DEFAULT '',
                    category TEXT NOT NULL,
                    metal_type TEXT NOT NULL,
                    metal_weight REAL NOT NULL,
                    diamond_weight REAL NOT NULL,
                    diamond_pcs INTEGER NOT NULL DEFAULT 0,
                    diamond_rate REAL NOT NULL,
                    making_charges REAL NOT NULL,
                    labor_rate REAL NOT NULL DEFAULT 0,
                    setting_charge_per_pc REAL NOT NULL DEFAULT 0,
                    gold_loss REAL NOT NULL DEFAULT 0,
                    rhodium REAL NOT NULL DEFAULT 0,
                    extra_charges REAL NOT NULL DEFAULT 0,
                    margin REAL NOT NULL,
                    final_price REAL NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            existing_columns = {
                row["name"] for row in conn.execute("PRAGMA table_info(products)").fetchall()
            }
            migrations = {
                "client_name": "ALTER TABLE products ADD COLUMN client_name TEXT NOT NULL DEFAULT ''",
                "diamond_pcs": "ALTER TABLE products ADD COLUMN diamond_pcs INTEGER NOT NULL DEFAULT 0",
                "labor_rate": "ALTER TABLE products ADD COLUMN labor_rate REAL NOT NULL DEFAULT 0",
                "setting_charge_per_pc": "ALTER TABLE products ADD COLUMN setting_charge_per_pc REAL NOT NULL DEFAULT 0",
                "gold_loss": "ALTER TABLE products ADD COLUMN gold_loss REAL NOT NULL DEFAULT 0",
                "rhodium": "ALTER TABLE products ADD COLUMN rhodium REAL NOT NULL DEFAULT 0",
                "extra_charges": "ALTER TABLE products ADD COLUMN extra_charges REAL NOT NULL DEFAULT 0",
            }
        for column_name, statement in migrations.items():
            if column_name not in existing_columns:
                conn.execute(statement)

        if is_postgres():
            for key, value in load_default_config().items():
                conn.execute(
                    """
                    INSERT INTO app_settings (key, value)
                    VALUES (?, ?)
                    ON CONFLICT (key) DO NOTHING
                    """,
                    (key, str(value)),
                )
        conn.commit()


def generate_product_code(category):
    prefixes = {
        "Ring": "RNG",
        "Necklace": "NEC",
        "Bracelet": "BRC",
    }
    prefix = prefixes.get(category)
    if not prefix:
        raise ValueError("Unsupported category")

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT product_code
            FROM products
            WHERE category = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (category,),
        ).fetchone()

    if not row:
        next_number = 1
    else:
        try:
            next_number = int(row["product_code"].split("-")[-1]) + 1
        except (ValueError, IndexError):
            next_number = 1

    return f"{prefix}-{next_number:04d}"
