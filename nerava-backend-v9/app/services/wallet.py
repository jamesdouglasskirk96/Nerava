# app/services/wallet.py
from __future__ import annotations
import os
import sqlite3
from contextlib import contextmanager
from typing import Optional, Dict, Any

# You can override via env; defaults to a local file next to the app.
DB_PATH = os.getenv("NERAVA_DB_PATH", os.path.join(os.path.dirname(__file__), "..", "..", "nerava.db"))
DB_PATH = os.path.abspath(DB_PATH)

# ---------- SQLite helpers ----------

@contextmanager
def _conn():
    try:
        con = sqlite3.connect(DB_PATH)
        con.execute("PRAGMA journal_mode=WAL;")
        con.row_factory = sqlite3.Row
        yield con
        con.commit()
    except Exception:
        # If SQLite fails for any reason, fall back to in-memory store
        yield None
    finally:
        try:
            con.close()
        except Exception:
            pass

def _ensure_schema(con: sqlite3.Connection):
    con.execute("""
        CREATE TABLE IF NOT EXISTS wallet (
            user_id TEXT PRIMARY KEY,
            balance_cents INTEGER NOT NULL DEFAULT 0,
            currency TEXT NOT NULL DEFAULT 'USD'
        )
    """)

# ---------- In-memory fallback ----------

_mem_store: Dict[str, Dict[str, Any]] = {}

def _mem_get(user_id: str) -> Dict[str, Any]:
    if user_id not in _mem_store:
        _mem_store[user_id] = {"user_id": user_id, "balance_cents": 0, "currency": "USD"}
    return _mem_store[user_id]

def _mem_set(user_id: str, balance_cents: int, currency: str = "USD") -> Dict[str, Any]:
    _mem_store[user_id] = {"user_id": user_id, "balance_cents": int(balance_cents), "currency": currency}
    return _mem_store[user_id]

# ---------- Public API ----------

def get_wallet(user_id: str, currency: str = "USD") -> Dict[str, Any]:
    """
    Return { user_id, balance_cents, currency }
    Creates a wallet with zero balance if it doesn't exist.
    """
    with _conn() as con:
        if con is None:
            # Fallback
            return _mem_get(user_id)

        _ensure_schema(con)
        row = con.execute("SELECT user_id, balance_cents, currency FROM wallet WHERE user_id = ?", (user_id,)).fetchone()
        if row is None:
            con.execute("INSERT INTO wallet (user_id, balance_cents, currency) VALUES (?, ?, ?)", (user_id, 0, currency))
            return {"user_id": user_id, "balance_cents": 0, "currency": currency}
        return {"user_id": row["user_id"], "balance_cents": int(row["balance_cents"]), "currency": row["currency"]}

def credit_wallet(user_id: str, amount_cents: int, currency: str = "USD") -> Dict[str, Any]:
    """
    Increment balance by amount_cents (must be >= 0). Returns updated wallet.
    """
    if amount_cents < 0:
        raise ValueError("amount_cents must be >= 0")

    with _conn() as con:
        if con is None:
            w = _mem_get(user_id)
            w["balance_cents"] = int(w["balance_cents"]) + int(amount_cents)
            return _mem_set(user_id, w["balance_cents"], w.get("currency", currency))

        _ensure_schema(con)
        row = con.execute("SELECT balance_cents, currency FROM wallet WHERE user_id = ?", (user_id,)).fetchone()
        if row is None:
            con.execute("INSERT INTO wallet (user_id, balance_cents, currency) VALUES (?, ?, ?)",
                        (user_id, int(amount_cents), currency))
            return {"user_id": user_id, "balance_cents": int(amount_cents), "currency": currency}
        new_balance = int(row["balance_cents"]) + int(amount_cents)
        con.execute("UPDATE wallet SET balance_cents = ? WHERE user_id = ?", (new_balance, user_id))
        return {"user_id": user_id, "balance_cents": new_balance, "currency": row["currency"]}

def debit_wallet(user_id: str, amount_cents: int) -> Dict[str, Any]:
    """
    Decrement balance by amount_cents (must be >= 0; not allowing negative balances).
    Returns updated wallet.
    """
    if amount_cents < 0:
        raise ValueError("amount_cents must be >= 0")

    with _conn() as con:
        if con is None:
            w = _mem_get(user_id)
            new_balance = max(0, int(w["balance_cents"]) - int(amount_cents))
            return _mem_set(user_id, new_balance, w.get("currency", "USD"))

        _ensure_schema(con)
        row = con.execute("SELECT balance_cents, currency FROM wallet WHERE user_id = ?", (user_id,)).fetchone()
        if row is None:
            # Nothing to debit; create empty wallet
            con.execute("INSERT INTO wallet (user_id, balance_cents, currency) VALUES (?, ?, ?)",
                        (user_id, 0, "USD"))
            return {"user_id": user_id, "balance_cents": 0, "currency": "USD"}
        new_balance = int(row["balance_cents"]) - int(amount_cents)
        if new_balance < 0:
            new_balance = 0  # or raise if you prefer strict behavior
        con.execute("UPDATE wallet SET balance_cents = ? WHERE user_id = ?", (new_balance, user_id))
        return {"user_id": user_id, "balance_cents": new_balance, "currency": row["currency"]}
