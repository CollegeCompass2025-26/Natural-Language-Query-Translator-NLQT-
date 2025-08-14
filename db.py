import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DB_URL")
STATEMENT_TIMEOUT = os.getenv("STATEMENT_TIMEOUT", "10000")  # ms

if not DB_URL:
    raise RuntimeError("DB_URL is not set. Put it in your .env.")


def get_conn():
    conn = psycopg2.connect(DB_URL, connect_timeout=8)
    # Safety: set per-connection statement timeout
    with conn.cursor() as cur:
        cur.execute("SET statement_timeout = %s;", (STATEMENT_TIMEOUT,))
    return conn


def fetch_rows(sql, params=None, limit=None):
    """Execute a SELECT safely and return list[dict]."""
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params or ())
            rows = cur.fetchall() if limit is None else cur.fetchmany(limit)
            return [dict(r) for r in rows]


def fetch_schema_tables_and_columns():
    """Return schema as {table: [columns...]} for public schema only."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT table_name, column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position;
                """
            )
            rows = cur.fetchall()
    schema = {}
    for table, column in rows:
        schema.setdefault(table, []).append(column)
    return schema