import os
import sqlite3
from pathlib import Path

import psycopg2


BASE_DIR = Path(__file__).resolve().parent.parent
SQLITE_PATH = BASE_DIR / "database.db"
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()


def main():
    if not DATABASE_URL:
        raise SystemExit("Set DATABASE_URL before running this migration.")
    if not SQLITE_PATH.exists():
        raise SystemExit(f"SQLite database not found: {SQLITE_PATH}")

    import sys

    sys.path.insert(0, str(BASE_DIR))
    from models.db_setup import init_db

    init_db()

    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    pg_conn = psycopg2.connect(DATABASE_URL)

    rows = sqlite_conn.execute(
        """
        SELECT product_code, client_name, category, metal_type, metal_weight, diamond_weight,
               diamond_pcs, diamond_rate, making_charges, labor_rate, setting_charge_per_pc,
               gold_loss, rhodium, extra_charges, margin, final_price, created_at
        FROM products
        ORDER BY id
        """
    ).fetchall()

    with pg_conn:
        with pg_conn.cursor() as cursor:
            for row in rows:
                cursor.execute(
                    """
                    INSERT INTO products (
                        product_code, client_name, category, metal_type, metal_weight, diamond_weight,
                        diamond_pcs, diamond_rate, making_charges, labor_rate, setting_charge_per_pc,
                        gold_loss, rhodium, extra_charges, margin, final_price, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (product_code) DO NOTHING
                    """,
                    tuple(row),
                )

    sqlite_conn.close()
    pg_conn.close()
    print(f"Migrated {len(rows)} products into PostgreSQL.")


if __name__ == "__main__":
    main()
