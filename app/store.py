"""Carts and orders in SQLite. One table each, keyed by the shopper's cart cookie."""

import sqlite3
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from app.catalog import BY_SLUG, Product
from app.config import settings


def _connect() -> sqlite3.Connection:
    Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    return conn


def init() -> None:
    with _connect() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS cart_items (cart_id TEXT, slug TEXT, qty INTEGER, PRIMARY KEY (cart_id, slug))")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS orders (id TEXT PRIMARY KEY, cart_id TEXT, email TEXT, total_cents INTEGER, created_at TEXT)"
        )


@contextmanager
def _db():
    conn = _connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def add(cart_id: str, slug: str, qty: int = 1) -> None:
    with _db() as conn:
        conn.execute(
            "INSERT INTO cart_items (cart_id, slug, qty) VALUES (?, ?, ?) "
            "ON CONFLICT(cart_id, slug) DO UPDATE SET qty = qty + excluded.qty",
            (cart_id, slug, qty),
        )


def remove(cart_id: str, slug: str) -> None:
    with _db() as conn:
        conn.execute("DELETE FROM cart_items WHERE cart_id = ? AND slug = ?", (cart_id, slug))


def items(cart_id: str) -> list[tuple[Product, int]]:
    with _db() as conn:
        rows = conn.execute("SELECT slug, qty FROM cart_items WHERE cart_id = ?", (cart_id,)).fetchall()
    return [(BY_SLUG[r["slug"]], r["qty"]) for r in rows if r["slug"] in BY_SLUG]


def total_cents(cart_id: str) -> int:
    return sum(p.price_cents * qty for p, qty in items(cart_id))


def place_order(cart_id: str, email: str) -> tuple[str, int]:
    total = total_cents(cart_id)
    order_id = uuid.uuid4().hex[:10]
    with _db() as conn:
        conn.execute(
            "INSERT INTO orders (id, cart_id, email, total_cents, created_at) VALUES (?, ?, ?, ?, ?)",
            (order_id, cart_id, email, total, datetime.now(UTC).isoformat()),
        )
        conn.execute("DELETE FROM cart_items WHERE cart_id = ?", (cart_id,))
    return order_id, total
