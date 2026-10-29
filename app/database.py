"""
Database management module for MediApp.
Enforces foreign keys, row factories, transaction safety, and connection lifecycle.
"""
import sqlite3
import os
from contextlib import contextmanager
from flask import g, current_app

def get_connection(db_path: str = None) -> sqlite3.Connection:
    """Creates a raw sqlite3 connection with strict foreign keys and Row factory."""
    if db_path is None:
        if current_app:
            db_path = current_app.config["DATABASE_PATH"]
        else:
            from app.config import Config
            db_path = Config.DATABASE_PATH
            
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")  # Write-Ahead Logging for concurrency
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.row_factory = sqlite3.Row
    return conn


def get_db() -> sqlite3.Connection:
    """Returns request-scoped database connection, or a direct connection if outside app context."""
    from flask import has_app_context
    if has_app_context():
        if "db" not in g:
            g.db = get_connection()
        return g.db
    return get_connection()


def close_db(e=None):
    """Closes request-scoped database connection."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


@contextmanager
def transaction(conn: sqlite3.Connection = None):
    """Context manager for atomic database operations with automatic rollback."""
    managed_conn = conn or get_db()
    try:
        yield managed_conn
        managed_conn.commit()
    except Exception:
        managed_conn.rollback()
        raise


def init_db(db_path: str = None):
    """Executes schema.sql against target database."""
    conn = get_connection(db_path)
    schema_file = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_file, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()


def query_db(query: str, args=(), one: bool = False, conn: sqlite3.Connection = None):
    """Executes query and returns list of dicts or single dict."""
    c = conn or get_db()
    cur = c.execute(query, args)
    rv = [dict(row) for row in cur.fetchall()]
    cur.close()
    return (rv[0] if rv else None) if one else rv


def execute_db(query: str, args=(), conn: sqlite3.Connection = None) -> int:
    """Executes modification statement and returns lastrowid."""
    c = conn or get_db()
    cur = c.execute(query, args)
    c.commit()
    last_id = cur.lastrowid
    cur.close()
    return last_id
