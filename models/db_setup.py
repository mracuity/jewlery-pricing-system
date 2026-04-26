import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
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
