from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parent.parent / "fruit_store.db"

SEED_PRODUCTS = [
    ("maca", "Maca", 42),
    ("banana", "Banana", 31),
    ("laranja", "Laranja", 27),
    ("uva", "Uva", 18),
    ("abacaxi", "Abacaxi", 9),
]


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity >= 0)
            )
            """
        )
        connection.executemany(
            """
            INSERT OR IGNORE INTO products (slug, name, quantity)
            VALUES (?, ?, ?)
            """,
            SEED_PRODUCTS,
        )


def list_products() -> list[dict[str, int | str]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT slug, name, quantity
            FROM products
            ORDER BY name
            """
        ).fetchall()

    return [dict(row) for row in rows]
