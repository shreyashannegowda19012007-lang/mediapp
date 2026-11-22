"""
Idempotent Database Seeding Script for MediApp.
Populates standard demonstration users, pharmacies, medicine catalogue, inventory,
sample prescriptions, and realistic test orders.
"""
import os
import csv
import json
import sqlite3
from werkzeug.security import generate_password_hash
from app.database import get_connection

def seed_database(db_path: str = None):
    """Seeds the database with idempotent checks to avoid duplication."""
    conn = get_connection(db_path)
    cur = conn.cursor()

    # 1. Seed Demo Users
    users_data = [
        ("customer@mediapp.local", "Customer@123", "Aditi Sharma", "+91 9876543210", "customer"),
        ("demo.customer@mediapp.local", "Customer@123", "Aditi Sharma", "+91 9876543210", "customer"),
        ("pharmacy@mediapp.local", "Pharmacy@123", "Rajesh Varma (Lead Pharmacist)", "+91 9876543211", "pharmacy"),
        ("demo.pharmacy@mediapp.local", "Pharmacy@123", "Rajesh Varma (Lead Pharmacist)", "+91 9876543211", "pharmacy"),
        ("apollo.koramangala@mediapp.local", "Pharmacy@123", "Rajesh Varma (Lead Pharmacist)", "+91 9876543211", "pharmacy"),
        ("pharmacy2@mediapp.local", "Pharmacy@123", "Suresh Patel (Pharmacist)", "+91 9876543212", "pharmacy"),
        ("medplus.btm@mediapp.local", "Pharmacy@123", "Suresh Patel (Pharmacist)", "+91 9876543212", "pharmacy"),
        ("delivery@mediapp.local", "Delivery@123", "Kiran Kumar", "+91 9123456789", "delivery"),
        ("demo.delivery@mediapp.local", "Delivery@123", "Kiran Kumar", "+91 9123456789", "delivery"),
        ("rajesh.delivery@mediapp.local", "Delivery@123", "Rajesh Kumar", "+91 9123456789", "delivery"),
        ("delivery2@mediapp.local", "Delivery@123", "Vikram Singh", "+91 9123456780", "delivery"),
        ("suresh.delivery@mediapp.local", "Delivery@123", "Suresh Nair", "+91 9123456780", "delivery"),
        ("admin@mediapp.local", "Admin@123", "System Administrator", "+91 9999900000", "admin"),
        ("demo.admin@mediapp.local", "Admin@123", "Dr. Neha Rao (Chief Administrator)", "+91 9999900000", "admin")
    ]

    user_ids = {}
    for email, pwd, name, phone, role in users_data:
        cur.execute("SELECT id FROM users WHERE email = ?", (email,))
        row = cur.fetchone()
        hashed = generate_password_hash(pwd)
        if not row:
            cur.execute(
                "INSERT INTO users (email, password_hash, full_name, phone, role, is_active) VALUES (?, ?, ?, ?, ?, 1)",
                (email, hashed, name, phone, role)
            )
            user_ids[email] = cur.lastrowid
        else:
            cur.execute("UPDATE users SET password_hash = ? WHERE email = ?", (hashed, email))
            user_ids[email] = row[0]

    # 2. Seed Customer Addresses
    customer_id = user_ids["demo.customer@mediapp.local"]
    cur.execute("SELECT id FROM customer_addresses WHERE user_id = ?", (customer_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO customer_addresses (user_id, address_line1, address_line2, city, state, pincode, landmark, is_default)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """, (customer_id, "Flat 402, Green Glen Layout", "Outer Ring Road, Bellandur", "Bengaluru", "Karnataka", "560103", "Opposite Central Mall"))

    # 3. Seed Pharmacies
    pharmacies_data = [
        ("Apollo Pharmacy - Indiranagar", "KA-BLR-PH-2024-00129", "+91 80 25251100", "indiranagar@apollo.local",
         "100ft Road, HAL 2nd Stage, Indiranagar", "Bengaluru", "560038", 12.9716, 77.6412, "approved", 4.9),
        ("MedPlus Pharmacy - Koramangala", "KA-BLR-PH-2023-00841", "+91 80 25539988", "koramangala@medplus.local",
         "80ft Road, 4th Block, Koramangala", "Bengaluru", "560034", 12.9352, 77.6245, "approved", 4.8),
        ("Fortis Health Care Chemist", "KA-BLR-PH-2024-00995", "+91 80 66214444", "pharmacy@fortis.local",
         "Bannerghatta Road, Opposite IIMB", "Bengaluru", "560076", 12.8946, 77.5986, "approved", 4.7)
    ]

    pharmacy_ids = []
    for name, lic, phone, email, addr, city, pin, lat, lon, status, rating in pharmacies_data:
        cur.execute("SELECT id FROM pharmacies WHERE license_number = ?", (lic,))
        row = cur.fetchone()
        if not row:
            cur.execute("""
                INSERT INTO pharmacies (name, license_number, phone, email, address, city, pincode, latitude, longitude, status, rating)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, lic, phone, email, addr, city, pin, lat, lon, status, rating))
            pharmacy_ids.append(cur.lastrowid)
        else:
            pharmacy_ids.append(row[0])

    # Associate Pharmacy Staff
    pharm_staff_map = [
        (pharmacy_ids[0], user_ids["demo.pharmacy@mediapp.local"], "Chief Pharmacist"),
        (pharmacy_ids[0], user_ids.get("pharmacy@mediapp.local", user_ids["demo.pharmacy@mediapp.local"]), "Lead Pharmacist"),
        (pharmacy_ids[0], user_ids["apollo.koramangala@mediapp.local"], "Staff Pharmacist"),
        (pharmacy_ids[1], user_ids["pharmacy2@mediapp.local"], "Managing Pharmacist"),
        (pharmacy_ids[1], user_ids["medplus.btm@mediapp.local"], "Supervising Pharmacist")
    ]
    for p_id, u_id, title in pharm_staff_map:
        cur.execute("SELECT id FROM pharmacy_staff WHERE user_id = ?", (u_id,))
        if not cur.fetchone():
            cur.execute("INSERT INTO pharmacy_staff (pharmacy_id, user_id, role_title) VALUES (?, ?, ?)", (p_id, u_id, title))

    # 4. Seed Delivery Profiles
    deliv_profiles_data = [
        (user_ids["demo.delivery@mediapp.local"], "Motorcycle", "KA-03-HA-8821", "DL-0420180091234"),
        (user_ids.get("delivery@mediapp.local", user_ids["demo.delivery@mediapp.local"]), "Motorcycle", "KA-03-HA-8820", "DL-0420180091230"),
        (user_ids["rajesh.delivery@mediapp.local"], "Scooter", "KA-03-HA-8822", "DL-0420180091235"),
        (user_ids["delivery2@mediapp.local"], "Scooter", "KA-05-EJ-4392", "DL-0420200084321"),
        (user_ids["suresh.delivery@mediapp.local"], "Motorcycle", "KA-05-EJ-4393", "DL-0420200084322")
    ]
    for u_id, v_type, v_num, dl in deliv_profiles_data:
        cur.execute("SELECT id FROM delivery_profiles WHERE user_id = ?", (u_id,))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO delivery_profiles (user_id, vehicle_type, vehicle_number, driving_license, is_available, current_latitude, current_longitude, status, rating)
                VALUES (?, ?, ?, ?, 1, 12.9716, 77.5946, 'approved', 4.9)
            """, (u_id, v_type, v_num, dl))

    # 5. Ingest Medicines from A_Z_medicines.csv
    csv_file = os.path.join(os.path.dirname(__file__), "data", "A_Z_medicines.csv")
    if os.path.exists(csv_file):
        with open(csv_file, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            med_rows = []
            for row in reader:
                med_rows.append((
                    int(row["id"]),
                    row["name"].strip(),
                    row["generic"].strip(),
                    row["strength"].strip(),
                    row["form"].strip(),
                    row["cat"].strip(),
                    row["mfr"].strip(),
                    float(row["price"]),
                    int(row["rx"]),
                    row.get("pack", "Standard Pack").strip(),
                    row.get("uses", "").strip(),
                    row.get("side_effects", "").strip()
                ))
            
            cur.executemany("""
                INSERT OR IGNORE INTO medicines (id, name, generic_name, strength, dosage_form, category, manufacturer, mrp, prescription_required, pack_size, uses, side_effects)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, med_rows)

            cur.execute("""
                UPDATE medicines
                SET requires_cold_chain = 1
                WHERE LOWER(category) LIKE '%insulin%'
                   OR LOWER(category) LIKE '%vaccine%'
                   OR LOWER(category) LIKE '%biological%'
                   OR LOWER(name) LIKE '%insulin%'
                   OR LOWER(name) LIKE '%vaccine%'
            """)

    # 6. Seed Pharmacy Inventory for Pharmacy 1 and Pharmacy 2
    # Ensure all catalogue medicines are stocked with realistic quantities and prices
    cur.execute("SELECT id, mrp FROM medicines")
    stocked_meds = cur.fetchall()
    
    inventory_rows = []
    for med in stocked_meds:
        med_id, mrp = med[0], med[1]
        # Pharmacy 1 stock
        inventory_rows.append((
            pharmacy_ids[0], med_id, 45, round(mrp * 0.95, 2), 1, f"BAT-2026-{med_id:04d}", "2028-12-31", 10
        ))
        # Pharmacy 2 stock
        inventory_rows.append((
            pharmacy_ids[1], med_id, 30, round(mrp * 0.92, 2), 1, f"BTM-2026-{med_id:04d}", "2028-10-31", 10
        ))

    cur.executemany("""
        INSERT OR IGNORE INTO pharmacy_inventory (pharmacy_id, medicine_id, stock_quantity, unit_price, is_available, batch_number, expiry_date, low_stock_threshold)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, inventory_rows)

    # 7. Seed Sample Prescriptions for demo customer
    cur.execute("SELECT id FROM prescriptions WHERE customer_id = ?", (customer_id,))
    existing_rx = cur.fetchone()
    if not existing_rx:
        cur.execute("""
            INSERT INTO prescriptions (customer_id, file_path, original_filename, file_size, mime_type, doctor_name, patient_name, prescription_date, extracted_text, extracted_medicines, ocr_confidence, ocr_provider, status, verified_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'verified', CURRENT_TIMESTAMP)
        """, (
            customer_id,
            "uploads/prescriptions/sample_prescription_dr_kapoor.pdf",
            "Dr_Kapoor_Prescription_Cardiology.pdf",
            145200,
            "application/pdf",
            "Dr. Arvind Kapoor, MD Cardiology (Reg. 44821)",
            "Aditi Sharma",
            "2026-10-20",
            "Rx: Tab Telma 40mg 1 OD morning. Tab Atorva 20mg 1 HS night. Tab Ecosprin 75mg 1 OD post-lunch.",
            json.dumps(["Telma 40mg", "Atorva 20mg", "Ecosprin 75mg"]),
            0.96,
            "ocr_verified"
        ))
        sample_rx_id = cur.lastrowid
    else:
        sample_rx_id = existing_rx[0]

    # 8. Seed Initial Cart
    cur.execute("SELECT id FROM carts WHERE user_id = ?", (customer_id,))
    if not cur.fetchone():
        cur.execute("INSERT INTO carts (user_id, pharmacy_id) VALUES (?, ?)", (customer_id, pharmacy_ids[0]))
        cart_id = cur.lastrowid
        # Add Dolo 650mg and Crocin Advance 500mg (both OTC) to cart
        cur.execute("INSERT INTO cart_items (cart_id, medicine_id, quantity) VALUES (?, 2, 2)", (cart_id,))
        cur.execute("INSERT INTO cart_items (cart_id, medicine_id, quantity) VALUES (?, 1, 1)", (cart_id,))

    # 9. Seed Demonstrative Orders Across Different Lifecycle States
    deliv1_id = user_ids["demo.delivery@mediapp.local"]
    sample_address = json.dumps({
        "line1": "Flat 402, Green Glen Layout",
        "line2": "Outer Ring Road, Bellandur",
        "city": "Bengaluru",
        "state": "Karnataka",
        "pincode": "560103",
        "landmark": "Opposite Central Mall",
        "recipient_name": "Aditi Sharma",
        "recipient_phone": "+91 9876543210"
    })

    test_orders = [
        # Order 1: Delivered historical order
        ("ORD-20261021-0001", customer_id, pharmacy_ids[0], deliv1_id, sample_rx_id, sample_address,
         435.0, 21.75, 40.0, 0.0, 496.75, "paid", "DELIVERED", "Left at security desk as requested"),
        # Order 2: In-Transit live order
        ("ORD-20261025-0002", customer_id, pharmacy_ids[0], deliv1_id, None, sample_address,
         140.0, 7.00, 30.0, 0.0, 177.00, "paid", "IN_TRANSIT", "Call upon arrival at gate 2"),
        # Order 3: Ready for pickup order at Pharmacy 1
        ("ORD-20261025-0003", customer_id, pharmacy_ids[0], None, None, sample_address,
         280.0, 14.00, 30.0, 0.0, 324.00, "paid", "READY_FOR_PICKUP", "Standard delivery"),
        # Order 4: Newly placed order needing pharmacy acceptance
        ("ORD-20261025-0004", customer_id, pharmacy_ids[0], None, None, sample_address,
         165.0, 8.25, 30.0, 0.0, 203.25, "paid", "ACCEPTED", "Urgent delivery needed")
    ]

    for ord_id, cust_id, pharm_id, dlv_id, rx_id, addr, sub, tx, fee, disc, tot, pay_st, ord_st, notes in test_orders:
        cur.execute("SELECT id FROM orders WHERE id = ?", (ord_id,))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO orders (id, customer_id, pharmacy_id, delivery_person_id, prescription_id,
                                   delivery_address_json, subtotal, tax, delivery_fee, discount, total_amount,
                                   currency, payment_status, order_status, delivery_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'INR', ?, ?, ?)
            """, (ord_id, cust_id, pharm_id, dlv_id, rx_id, addr, sub, tx, fee, disc, tot, pay_st, ord_st, notes))

            # Add order items
            cur.execute("""
                INSERT INTO order_items (order_id, medicine_id, medicine_name_snapshot, generic_name_snapshot,
                                        strength_snapshot, dosage_form_snapshot, unit_price, quantity, total_price)
                VALUES (?, 2, 'Dolo 650mg', 'Paracetamol', '650mg', 'Tablet', 30.40, 2, 60.80)
            """, (ord_id,))

            # Add payment entry
            cur.execute("""
                INSERT INTO payments (order_id, provider, amount, currency, status, transaction_reference)
                VALUES (?, 'demo', ?, 'INR', 'success', ?)
            """, (ord_id, tot, f"DEMO_TXN_{ord_id}"))

            # Add status history
            cur.execute("""
                INSERT INTO order_status_history (order_id, from_status, to_status, changed_by_user_id, role, notes)
                VALUES (?, 'PLACED', ?, ?, 'system', 'Order initialized via seed')
            """, (ord_id, ord_st, cust_id))

            # If assigned/delivered, add delivery assignment
            if dlv_id:
                cur.execute("""
                    INSERT INTO delivery_assignments (order_id, delivery_person_id, status)
                    VALUES (?, ?, ?)
                """, (ord_id, dlv_id, 'delivered' if ord_st == 'DELIVERED' else 'in_transit'))

    conn.commit()
    conn.close()
    print("Database seeded successfully with users, pharmacies, catalogue, inventory, and test orders.")

if __name__ == "__main__":
    seed_database()
