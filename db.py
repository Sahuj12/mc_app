"""
SQLite data access layer.

A plain sqlite3 layer (rather than an ORM) is used deliberately: it keeps
the dependency footprint small and every query is explicit and auditable,
which matters for a security-sensitive app like this one.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from flask import g, current_app

from config import Config

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS datasets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    row_count       INTEGER NOT NULL,
    encrypted_blob  BLOB NOT NULL,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS simulations (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name                TEXT NOT NULL,
    dataset_id          INTEGER REFERENCES datasets(id) ON DELETE SET NULL,
    encrypted_params    BLOB NOT NULL,
    encrypted_summary   BLOB NOT NULL,
    encrypted_sample_paths BLOB NOT NULL,
    created_at          TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_datasets_user ON datasets(user_id);
CREATE INDEX IF NOT EXISTS idx_simulations_user ON simulations(user_id);
"""


def get_db() -> sqlite3.Connection:
    """Return a request-scoped SQLite connection (created lazily, reused per-request)."""
    if "db" not in g:
        g.db = sqlite3.connect(Config.DATABASE_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app) -> None:
    """Create tables if they don't exist. Safe to call on every startup."""
    import os
    os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    app.teardown_appcontext(close_db)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
def create_user(email: str, password_hash: str) -> int:
    db = get_db()
    cur = db.execute(
        "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
        (email.lower().strip(), password_hash, now_iso()),
    )
    db.commit()
    return cur.lastrowid


def get_user_by_email(email: str):
    db = get_db()
    return db.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),)).fetchone()


def get_user_by_id(user_id: int):
    db = get_db()
    return db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def update_user_password(user_id: int, new_password_hash: str) -> None:
    db = get_db()
    db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_password_hash, user_id))
    db.commit()


# ---------------------------------------------------------------------------
# Datasets
# ---------------------------------------------------------------------------
def count_datasets_for_user(user_id: int) -> int:
    db = get_db()
    return db.execute("SELECT COUNT(*) AS c FROM datasets WHERE user_id = ?", (user_id,)).fetchone()["c"]


def create_dataset(user_id: int, name: str, row_count: int, encrypted_blob: bytes) -> int:
    db = get_db()
    cur = db.execute(
        "INSERT INTO datasets (user_id, name, row_count, encrypted_blob, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, name, row_count, encrypted_blob, now_iso()),
    )
    db.commit()
    return cur.lastrowid


def list_datasets_for_user(user_id: int):
    db = get_db()
    return db.execute(
        "SELECT id, name, row_count, created_at FROM datasets WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()


def get_dataset(dataset_id: int, user_id: int):
    db = get_db()
    return db.execute(
        "SELECT * FROM datasets WHERE id = ? AND user_id = ?", (dataset_id, user_id)
    ).fetchone()


def delete_dataset(dataset_id: int, user_id: int) -> None:
    db = get_db()
    db.execute("DELETE FROM datasets WHERE id = ? AND user_id = ?", (dataset_id, user_id))
    db.commit()


# ---------------------------------------------------------------------------
# Simulations
# ---------------------------------------------------------------------------
def count_simulations_for_user(user_id: int) -> int:
    db = get_db()
    return db.execute("SELECT COUNT(*) AS c FROM simulations WHERE user_id = ?", (user_id,)).fetchone()["c"]


def create_simulation(user_id, name, dataset_id, encrypted_params, encrypted_summary, encrypted_sample_paths) -> int:
    db = get_db()
    cur = db.execute(
        """INSERT INTO simulations
           (user_id, name, dataset_id, encrypted_params, encrypted_summary, encrypted_sample_paths, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, name, dataset_id, encrypted_params, encrypted_summary, encrypted_sample_paths, now_iso()),
    )
    db.commit()
    return cur.lastrowid


def list_simulations_for_user(user_id: int):
    db = get_db()
    return db.execute(
        "SELECT id, name, created_at FROM simulations WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()


def get_simulation(sim_id: int, user_id: int):
    db = get_db()
    return db.execute(
        "SELECT * FROM simulations WHERE id = ? AND user_id = ?", (sim_id, user_id)
    ).fetchone()


def delete_simulation(sim_id: int, user_id: int) -> None:
    db = get_db()
    db.execute("DELETE FROM simulations WHERE id = ? AND user_id = ?", (sim_id, user_id))
    db.commit()
