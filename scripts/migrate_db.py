import sqlite3
import random

def migrate():
    conn = sqlite3.connect('mediapp.db')
    c = conn.cursor()

    def add_col(table, col, col_type):
        c.execute(f'PRAGMA table_info({table})')
        cols = [r[1] for r in c.fetchall()]
        if col not in cols:
            print(f'Adding {col} to {table}...')
            c.execute(f'ALTER TABLE {table} ADD COLUMN {col} {col_type}')
            print(f'Added {col} to {table}.')
        else:
            print(f'{col} already exists in {table}.')

    add_col('orders', 'delivery_otp', 'TEXT')
    add_col('prescriptions', 'approved_medicines', 'TEXT')
    add_col('prescriptions', 'pharmacist_notes', 'TEXT')
    add_col('medicines', 'requires_cold_chain', 'INTEGER DEFAULT 0')

    # Populate requires_cold_chain
    c.execute("""
        UPDATE medicines
        SET requires_cold_chain = 1
        WHERE category LIKE '%Insulin%'
           OR category LIKE '%Vaccine%'
           OR name LIKE '%Insulin%'
           OR uses LIKE '%diabetes%' AND dosage_form = 'Injection'
    """)

    # Seed delivery_otp for existing orders if null
    c.execute("SELECT id FROM orders WHERE delivery_otp IS NULL")
    rows = c.fetchall()
    for (oid,) in rows:
        otp = f"{random.randint(100000, 999999)}"
        c.execute("UPDATE orders SET delivery_otp = ? WHERE id = ?", (otp, oid))

    conn.commit()
    print(f"Migration completed. Updated {len(rows)} orders with OTP.")
    conn.close()

if __name__ == '__main__':
    migrate()
