import sqlite3
from app.core import config


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _add_column_if_missing(cursor: sqlite3.Cursor, table: str, column: str, definition: str):
    """Safe migration: adds a column to an existing table only if it doesn't already exist."""
    cursor.execute(f"PRAGMA table_info({table})")
    existing = [row[1] for row in cursor.fetchall()]
    if column not in existing:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db():
    conn = get_db_connection()
    conn.execute("PRAGMA journal_mode=WAL")
    cursor = conn.cursor()

    # ── Users table ──────────────────────────────────────────────────────────
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'Delivery',
        pay_frequency TEXT DEFAULT 'Daily',
        primary_obligation TEXT DEFAULT 'Bike EMI',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ── Goals table ───────────────────────────────────────────────────────────
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS goals (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        title TEXT NOT NULL,
        target_amount REAL NOT NULL,
        current_amount REAL DEFAULT 0,
        due_date TEXT NOT NULL,
        category TEXT DEFAULT 'emi',
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    # ── Transactions table ────────────────────────────────────────────────────
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        amount REAL NOT NULL,
        type TEXT NOT NULL,         -- 'income' or 'expense'
        category TEXT NOT NULL,
        description TEXT DEFAULT '',
        note TEXT DEFAULT '',       -- optional user annotation
        merchant TEXT DEFAULT '',   -- expense merchant name
        date TEXT NOT NULL,
        source TEXT DEFAULT 'manual', -- 'manual', 'voice', 'ocr', 'seed'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)
    # Safe migrations for databases created before Step 2
    _add_column_if_missing(cursor, "transactions", "note", "TEXT DEFAULT ''")
    _add_column_if_missing(cursor, "transactions", "merchant", "TEXT DEFAULT ''")

    # ── Obligations table ─────────────────────────────────────────────────────
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS obligations (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        title TEXT NOT NULL,
        amount REAL NOT NULL,
        frequency TEXT DEFAULT 'monthly',
        due_day INTEGER DEFAULT 10,
        next_due_date TEXT,
        status TEXT DEFAULT 'active',   -- 'active', 'paid', 'overdue'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)
    # Safe migration for existing obligations table
    _add_column_if_missing(cursor, "obligations", "status", "TEXT DEFAULT 'active'")

    # Safe migration for goals table updated_at
    _add_column_if_missing(cursor, "goals", "updated_at", "TIMESTAMP")

    # ── Financial Plans table ─────────────────────────────────────────────────
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS financial_plans (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        goal_id TEXT,
        target_amount REAL NOT NULL,
        daily_target REAL NOT NULL,
        strategy TEXT NOT NULL,
        timeframe_days INTEGER NOT NULL,
        status TEXT DEFAULT 'active',   -- 'active', 'succeeded', 'failed', 'revised'
        assumptions TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    _add_column_if_missing(cursor, "financial_plans", "assumptions", "TEXT DEFAULT ''")
    _add_column_if_missing(cursor, "financial_plans", "updated_at", "TIMESTAMP")

    conn.commit()
    conn.close()
