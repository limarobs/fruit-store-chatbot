from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parent.parent / "fruit_store.db"

# (slug, name, quantity, price_cents) - preco em centavos para evitar float.
SEED_PRODUCTS = [
    ("maca", "Maca", 42, 450),
    ("banana", "Banana", 31, 320),
    ("laranja", "Laranja", 27, 280),
    ("uva", "Uva", 18, 890),
    ("abacaxi", "Abacaxi", 9, 600),
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
                quantity INTEGER NOT NULL CHECK (quantity >= 0),
                price_cents INTEGER NOT NULL DEFAULT 0 CHECK (price_cents >= 0)
            )
            """
        )

        # Migracao para bancos criados antes da coluna de preco existir.
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(products)")}
        if "price_cents" not in columns:
            connection.execute(
                "ALTER TABLE products ADD COLUMN price_cents INTEGER NOT NULL DEFAULT 0"
            )

        connection.executemany(
            """
            INSERT OR IGNORE INTO products (slug, name, quantity, price_cents)
            VALUES (?, ?, ?, ?)
            """,
            SEED_PRODUCTS,
        )

        # Garante que linhas ja existentes recebam o preco do seed.
        connection.executemany(
            "UPDATE products SET price_cents = ? WHERE slug = ?",
            [(price_cents, slug) for slug, _, _, price_cents in SEED_PRODUCTS],
        )


def list_products() -> list[dict[str, int | str]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT slug, name, quantity, price_cents
            FROM products
            ORDER BY name
            """
        ).fetchall()

    return [dict(row) for row in rows]


def find_product_by_slug(slug: str) -> dict[str, int | str] | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT slug, name, quantity, price_cents
            FROM products
            WHERE slug = ?
            """,
            (slug,),
        ).fetchone()

    if row is None:
        return None

    return dict(row)
