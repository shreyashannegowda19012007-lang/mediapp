"""
Schema Migration Tracker for MediApp.
Tracks schema versions and applies incremental database modifications safely.
"""
import sqlite3
from app.database import get_connection, init_db

CURRENT_SCHEMA_VERSION = 2

MIGRATIONS = {
    1: "Initial schema creation with core tables, foreign keys, and indexes",
    2: "Add requires_cold_chain to medicines, delivery_otp to orders, approved_medicines and pharmacist_notes to prescriptions"
}

def _column_exists(cur: sqlite3.Cursor, table_name: str, column_name: str) -> bool:
    """Checks whether a column exists in the specified table."""
    cur.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cur.fetchall()]
    return column_name in columns

def _apply_migration_v2(cur: sqlite3.Cursor):
    """Executes schema changes and backfills for schema version 2."""
    # Alter medicines: add requires_cold_chain INTEGER NOT NULL DEFAULT 0
    if not _column_exists(cur, "medicines", "requires_cold_chain"):
        cur.execute("ALTER TABLE medicines ADD COLUMN requires_cold_chain INTEGER NOT NULL DEFAULT 0")

    # Alter orders: add delivery_otp TEXT DEFAULT NULL
    if not _column_exists(cur, "orders", "delivery_otp"):
        cur.execute("ALTER TABLE orders ADD COLUMN delivery_otp TEXT DEFAULT NULL")

    # Alter prescriptions: add approved_medicines TEXT DEFAULT NULL
    if not _column_exists(cur, "prescriptions", "approved_medicines"):
        cur.execute("ALTER TABLE prescriptions ADD COLUMN approved_medicines TEXT DEFAULT NULL")

    # Alter prescriptions: add pharmacist_notes TEXT DEFAULT NULL
    if not _column_exists(cur, "prescriptions", "pharmacist_notes"):
        cur.execute("ALTER TABLE prescriptions ADD COLUMN pharmacist_notes TEXT DEFAULT NULL")

    # Backfill cold-chain medicines (insulins, vaccines, biologicals)
    cur.execute("""
        UPDATE medicines
        SET requires_cold_chain = 1
        WHERE LOWER(category) LIKE '%insulin%'
           OR LOWER(category) LIKE '%vaccine%'
           OR LOWER(category) LIKE '%biological%'
           OR LOWER(name) LIKE '%insulin%'
           OR LOWER(name) LIKE '%vaccine%'
    """)

def run_migrations(db_path: str = None):
    """Checks schema_migrations and applies any outstanding migrations up to CURRENT_SCHEMA_VERSION."""
    init_db(db_path)
    conn = get_connection(db_path)
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            description TEXT NOT NULL,
            applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("SELECT version FROM schema_migrations")
    applied_versions = {row[0] for row in cur.fetchall()}
    
    for version, desc in sorted(MIGRATIONS.items()):
        if version > CURRENT_SCHEMA_VERSION:
            continue
        if version not in applied_versions:
            if version == 2:
                _apply_migration_v2(cur)
            
            cur.execute(
                "INSERT INTO schema_migrations (version, description) VALUES (?, ?)",
                (version, desc)
            )
            print(f"Applied migration {version}: {desc}")
            
    conn.commit()
    conn.close()

# Alias apply_migrations to run_migrations for API compatibility
apply_migrations = run_migrations

if __name__ == "__main__":
    run_migrations()
