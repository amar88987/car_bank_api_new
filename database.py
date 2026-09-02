import os
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
from config import DATABASE_URL


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured. Put your Supabase PostgreSQL URL in .env")
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def initialize_database():
    """Create required tables and demo data without deleting existing data."""
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured")
    schema_path = Path(__file__).resolve().parent.parent / "database" / "schema.sql"
    sql = schema_path.read_text(encoding="utf-8")
    # psycopg can execute the whole schema in one call for PostgreSQL.
    with get_connection() as conn:
        conn.execute(sql)
        conn.commit()

def get_customers():
    with get_connection() as conn:
        return conn.execute("""
            SELECT id, name, phone, email, national_id
            FROM customers ORDER BY id
        """).fetchall()

def get_customer(customer_id):
    with get_connection() as conn:
        return conn.execute("""
            SELECT id, name, phone, email, national_id
            FROM customers WHERE id = %s
        """, (customer_id,)).fetchone()

def get_accounts():
    with get_connection() as conn:
        return conn.execute("""
            SELECT a.id, a.customer_id, c.name AS customer_name,
                   a.account_number, a.balance::float AS balance,
                   a.account_type
            FROM accounts a
            JOIN customers c ON c.id = a.customer_id
            ORDER BY a.id
        """).fetchall()

def get_loans():
    with get_connection() as conn:
        return conn.execute("""
            SELECT l.id, l.customer_id, c.name AS customer_name,
                   l.car_id, l.car_name, l.amount::float AS amount,
                   l.months, l.monthly_payment::float AS monthly_payment,
                   l.status, l.created_at::text AS created_at
            FROM loans l
            JOIN customers c ON c.id = l.customer_id
            ORDER BY l.id DESC
        """).fetchall()

def get_loan(loan_id):
    with get_connection() as conn:
        return conn.execute("""
            SELECT l.id, l.customer_id, c.name AS customer_name,
                   l.car_id, l.car_name, l.amount::float AS amount,
                   l.months, l.monthly_payment::float AS monthly_payment,
                   l.status, l.created_at::text AS created_at
            FROM loans l
            JOIN customers c ON c.id = l.customer_id
            WHERE l.id = %s
        """, (loan_id,)).fetchone()

def create_loan(customer_id, car_id, car_name, amount, months, status):
    monthly_payment = round(amount / months, 2)
    with get_connection() as conn:
        row = conn.execute("""
            INSERT INTO loans
            (customer_id, car_id, car_name, amount, months,
             monthly_payment, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
        """, (customer_id, car_id, car_name, amount, months,
              monthly_payment, status)).fetchone()
    return row["id"], monthly_payment
