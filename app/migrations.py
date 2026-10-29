"""
Schema Migration Tracker for MediApp.
Tracks schema versions and applies incremental database modifications safely.
"""
from app.database import get_connection, init_db

CURRENT_SCHEMA_VERSION = 1

MIGRATIONS = {
    1: "Initial schema creation with core tables, foreign keys, and indexes"
}

def apply_migrations(db_path: str = None):
    """Checks schema_migrations and applies any outstanding migrations."""
    init_db(db_path)
    conn = get_connection(db_path)
    cur = conn.cursor()
    
    cur.execute("SELECT version FROM schema_migrations")
    applied_versions = {row[0] for row in cur.fetchall()}
    
    for version, desc in sorted(MIGRATIONS.items()):
        if version not in applied_versions:
            # Migration logic can be executed here
            cur.execute(
                "INSERT INTO schema_migrations (version, description) VALUES (?, ?)",
                (version, desc)
            )
            print(f"Applied migration {version}: {desc}")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    apply_migrations()
