import sqlite3
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "rahat.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users table
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

    # Goals table
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
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    # Transactions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        amount REAL NOT NULL,
        type TEXT NOT NULL, -- 'income' or 'expense'
        category TEXT NOT NULL,
        description TEXT,
        date TEXT NOT NULL,
        source TEXT DEFAULT 'manual', -- 'manual', 'voice', 'ocr', 'seed'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    # Obligations table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS obligations (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        title TEXT NOT NULL,
        amount REAL NOT NULL,
        frequency TEXT DEFAULT 'monthly',
        due_day INTEGER DEFAULT 10,
        next_due_date TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    # Financial Plans table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS financial_plans (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        goal_id TEXT,
        target_amount REAL NOT NULL,
        daily_target REAL NOT NULL,
        strategy TEXT NOT NULL,
        timeframe_days INTEGER NOT NULL,
        status TEXT DEFAULT 'active', -- 'active', 'succeeded', 'failed', 'revised'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    conn.commit()
    conn.close()

def seed_demo_data(user_id: str = "demo_user"):
    """
    Deterministic demo dataset showcasing:
    - Variable daily income (₹650, ₹900, ₹430, ₹1050, ₹1300, etc.)
    - Realistic expenses (Fuel ₹220, Maintenance ₹350, Food ₹140)
    - Active EMI Goal: ₹4,500
    - Historical plan from Sept 12 (Save ₹900/day)
    - Outcome: Failed because weekday earnings were lower (actual pace ~₹500/day)
    - Learned pattern: Weekend earnings higher, weekday earnings lower
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Clear existing data for demo user
    cursor.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM goals WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM obligations WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM financial_plans WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))

    # Insert Demo User (Ramesh Kumar - Delivery Partner)
    cursor.execute("""
    INSERT INTO users (id, name, email, password_hash, role, pay_frequency, primary_obligation)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, "Ramesh Kumar", "ramesh.demo@rahat.app", "demo_secure_hash", "Delivery Partner (Zomato/Swiggy)", "Daily", "Bike EMI (₹4,500)"))

    # Fixed Obligation
    cursor.execute("""
    INSERT INTO obligations (id, user_id, title, amount, frequency, due_day, next_due_date)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("obl_1", user_id, "Hero Splendor Bike EMI", 4500.0, "monthly", 10, "2026-10-10"))

    # Active Goal: Upcoming Bike EMI
    cursor.execute("""
    INSERT INTO goals (id, user_id, title, target_amount, current_amount, due_date, category, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, ("goal_current_emi", user_id, "Upcoming Bike EMI Target", 4500.0, 1800.0, "2026-10-05", "emi", "active"))

    # Past Goal (September EMI)
    cursor.execute("""
    INSERT INTO goals (id, user_id, title, target_amount, current_amount, due_date, category, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, ("goal_sept_emi", user_id, "September Bike EMI", 4500.0, 3900.0, "2026-09-16", "emi", "missed"))

    # Past Plan (Sept 12)
    cursor.execute("""
    INSERT INTO financial_plans (id, user_id, goal_id, target_amount, daily_target, strategy, timeframe_days, status, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ("plan_sept_12", user_id, "goal_sept_emi", 4500.0, 900.0, "Flat ₹900/day saving across 5 weekdays", 5, "failed", "2026-09-12 09:00:00"))

    # Seed Transactions representing variable gig earnings & fuel expenses
    today = datetime.now()
    transactions = [
        # Recent 7 days
        ("tx_1", 1300.0, "income", "Delivery Earnings", "Sunday peak hours delivery (14 orders)", (today - timedelta(days=1)).strftime("%Y-%m-%d")),
        ("tx_2", 240.0, "expense", "Fuel", "HP Petrol Pump", (today - timedelta(days=1)).strftime("%Y-%m-%d")),
        ("tx_3", 1050.0, "income", "Delivery Earnings", "Saturday weekend surge deliveries", (today - timedelta(days=2)).strftime("%Y-%m-%d")),
        ("tx_4", 180.0, "expense", "Fuel", "IndianOil Petrol", (today - timedelta(days=2)).strftime("%Y-%m-%d")),
        ("tx_5", 650.0, "income", "Delivery Earnings", "Friday dinner shifts", (today - timedelta(days=3)).strftime("%Y-%m-%d")),
        ("tx_6", 430.0, "income", "Delivery Earnings", "Thursday rain slow shift (6 orders)", (today - timedelta(days=4)).strftime("%Y-%m-%d")),
        ("tx_7", 120.0, "expense", "Food", "Tiffin during afternoon rest", (today - timedelta(days=4)).strftime("%Y-%m-%d")),
        ("tx_8", 900.0, "income", "Delivery Earnings", "Wednesday lunch & dinner shifts", (today - timedelta(days=5)).strftime("%Y-%m-%d")),
        ("tx_9", 350.0, "expense", "Maintenance", "Clutch cable & brake shoe service", (today - timedelta(days=5)).strftime("%Y-%m-%d")),
        ("tx_10", 720.0, "income", "Delivery Earnings", "Tuesday weekday shift", (today - timedelta(days=6)).strftime("%Y-%m-%d")),
        ("tx_11", 680.0, "income", "Delivery Earnings", "Monday regular shift", (today - timedelta(days=7)).strftime("%Y-%m-%d")),
        ("tx_12", 220.0, "expense", "Fuel", "Bharat Petroleum refueling", (today - timedelta(days=7)).strftime("%Y-%m-%d")),
    ]

    for tx in transactions:
        cursor.execute("""
        INSERT INTO transactions (id, user_id, amount, type, category, description, date, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (tx[0], user_id, tx[1], tx[2], tx[3], tx[4], tx[5], "seed"))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    seed_demo_data()
    print("Database initialized and demo data seeded successfully.")
