-- ==============================================================================
-- MediApp Database Schema
-- SQLite3 with Foreign Keys Enforced
-- ==============================================================================

PRAGMA foreign_keys = ON;

-- 1. Users & Authentication
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    full_name TEXT NOT NULL,
    phone TEXT,
    role TEXT NOT NULL CHECK(role IN ('customer', 'pharmacy', 'delivery', 'admin')),
    is_active INTEGER NOT NULL DEFAULT 1,
    google_id TEXT UNIQUE,
    profile_image TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. Customer Saved Delivery Addresses
CREATE TABLE IF NOT EXISTS customer_addresses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    address_line1 TEXT NOT NULL,
    address_line2 TEXT,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    pincode TEXT NOT NULL,
    landmark TEXT,
    is_default INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 3. Pharmacies / Shops
CREATE TABLE IF NOT EXISTS pharmacies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    license_number TEXT UNIQUE NOT NULL,
    phone TEXT NOT NULL,
    email TEXT NOT NULL,
    address TEXT NOT NULL,
    city TEXT NOT NULL,
    pincode TEXT NOT NULL,
    latitude REAL DEFAULT 12.9716,
    longitude REAL DEFAULT 77.5946,
    status TEXT NOT NULL DEFAULT 'approved' CHECK(status IN ('pending', 'approved', 'suspended', 'rejected')),
    rating REAL DEFAULT 4.8,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 4. Pharmacy Staff Membership
CREATE TABLE IF NOT EXISTS pharmacy_staff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pharmacy_id INTEGER NOT NULL REFERENCES pharmacies(id) ON DELETE CASCADE,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_title TEXT DEFAULT 'Pharmacist',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 5. Delivery Personnel Profiles
CREATE TABLE IF NOT EXISTS delivery_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    vehicle_type TEXT DEFAULT 'Motorcycle',
    vehicle_number TEXT,
    driving_license TEXT,
    is_available INTEGER NOT NULL DEFAULT 1,
    current_latitude REAL DEFAULT 12.9716,
    current_longitude REAL DEFAULT 77.5946,
    status TEXT NOT NULL DEFAULT 'approved' CHECK(status IN ('pending', 'approved', 'suspended')),
    rating REAL DEFAULT 4.9,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 6. Medicines Catalogue
CREATE TABLE IF NOT EXISTS medicines (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    generic_name TEXT NOT NULL,
    strength TEXT NOT NULL,
    dosage_form TEXT NOT NULL,
    category TEXT NOT NULL,
    manufacturer TEXT NOT NULL,
    mrp REAL NOT NULL CHECK(mrp >= 0),
    prescription_required INTEGER NOT NULL DEFAULT 0,
    pack_size TEXT,
    uses TEXT,
    side_effects TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 7. Pharmacy-Specific Live Inventory
CREATE TABLE IF NOT EXISTS pharmacy_inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pharmacy_id INTEGER NOT NULL REFERENCES pharmacies(id) ON DELETE CASCADE,
    medicine_id INTEGER NOT NULL REFERENCES medicines(id) ON DELETE CASCADE,
    stock_quantity INTEGER NOT NULL DEFAULT 0 CHECK(stock_quantity >= 0),
    unit_price REAL NOT NULL CHECK(unit_price >= 0),
    is_available INTEGER NOT NULL DEFAULT 1,
    batch_number TEXT,
    expiry_date TEXT,
    low_stock_threshold INTEGER NOT NULL DEFAULT 10,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(pharmacy_id, medicine_id)
);

-- 8. Prescriptions & OCR Verification Records
CREATE TABLE IF NOT EXISTS prescriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type TEXT NOT NULL,
    doctor_name TEXT,
    patient_name TEXT,
    prescription_date TEXT,
    extracted_text TEXT,
    extracted_medicines TEXT, -- JSON array of candidate medications
    ocr_confidence REAL DEFAULT 0.0,
    ocr_provider TEXT DEFAULT 'heuristic',
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'under_review', 'verified', 'rejected')),
    reviewed_by INTEGER REFERENCES users(id),
    rejection_reason TEXT,
    verified_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 9. Customer Carts
CREATE TABLE IF NOT EXISTS carts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    pharmacy_id INTEGER REFERENCES pharmacies(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 10. Cart Items
CREATE TABLE IF NOT EXISTS cart_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cart_id INTEGER NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
    medicine_id INTEGER NOT NULL REFERENCES medicines(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cart_id, medicine_id)
);

-- 11. Orders (The Single Authoritative Shared Entity)
CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY, -- String order ID, e.g. ORD-20261025-A1B2
    customer_id INTEGER NOT NULL REFERENCES users(id),
    pharmacy_id INTEGER NOT NULL REFERENCES pharmacies(id),
    delivery_person_id INTEGER REFERENCES users(id),
    prescription_id INTEGER REFERENCES prescriptions(id),
    delivery_address_json TEXT NOT NULL,
    subtotal REAL NOT NULL CHECK(subtotal >= 0),
    tax REAL NOT NULL CHECK(tax >= 0),
    delivery_fee REAL NOT NULL CHECK(delivery_fee >= 0),
    discount REAL NOT NULL DEFAULT 0.0 CHECK(discount >= 0),
    total_amount REAL NOT NULL CHECK(total_amount >= 0),
    currency TEXT NOT NULL DEFAULT 'INR',
    payment_status TEXT NOT NULL DEFAULT 'pending' CHECK(payment_status IN ('pending', 'paid', 'failed', 'refunded')),
    order_status TEXT NOT NULL DEFAULT 'PLACED' CHECK(order_status IN (
        'PLACED',
        'AWAITING_PRESCRIPTION',
        'PRESCRIPTION_VERIFIED',
        'ACCEPTED',
        'PREPARING',
        'READY_FOR_PICKUP',
        'DELIVERY_ASSIGNED',
        'PICKED_UP',
        'IN_TRANSIT',
        'DELIVERED',
        'CANCELLED',
        'DELIVERY_FAILED'
    )),
    cancellation_reason TEXT,
    delivery_notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 12. Order Items (Snapshot preserving historical prices & details)
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    medicine_id INTEGER NOT NULL REFERENCES medicines(id),
    medicine_name_snapshot TEXT NOT NULL,
    generic_name_snapshot TEXT NOT NULL,
    strength_snapshot TEXT NOT NULL,
    dosage_form_snapshot TEXT NOT NULL,
    unit_price REAL NOT NULL CHECK(unit_price >= 0),
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    total_price REAL NOT NULL CHECK(total_price >= 0)
);

-- 13. Order Status Audit History
CREATE TABLE IF NOT EXISTS order_status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    from_status TEXT,
    to_status TEXT NOT NULL,
    changed_by_user_id INTEGER REFERENCES users(id),
    role TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 14. Payments Records
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    provider TEXT NOT NULL CHECK(provider IN ('demo', 'razorpay')),
    amount REAL NOT NULL CHECK(amount >= 0),
    currency TEXT NOT NULL DEFAULT 'INR',
    status TEXT NOT NULL DEFAULT 'initiated' CHECK(status IN ('initiated', 'success', 'failed', 'refunded')),
    transaction_reference TEXT UNIQUE NOT NULL,
    provider_order_id TEXT,
    signature TEXT,
    raw_response_json TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 15. Delivery Assignments
CREATE TABLE IF NOT EXISTS delivery_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT UNIQUE NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    delivery_person_id INTEGER NOT NULL REFERENCES users(id),
    status TEXT NOT NULL DEFAULT 'assigned' CHECK(status IN ('assigned', 'picked_up', 'in_transit', 'delivered', 'failed', 'cancelled')),
    pickup_time TIMESTAMP,
    delivery_time TIMESTAMP,
    proof_of_delivery TEXT,
    failure_reason TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 16. Audit Log
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT,
    details_json TEXT,
    ip_address TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 17. Migrations Version Tracker
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for Fast Lookups and High-Performance Joins
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_google ON users(google_id);

CREATE INDEX IF NOT EXISTS idx_medicines_name ON medicines(name);
CREATE INDEX IF NOT EXISTS idx_medicines_generic ON medicines(generic_name);
CREATE INDEX IF NOT EXISTS idx_medicines_cat ON medicines(category);

CREATE INDEX IF NOT EXISTS idx_inventory_pharmacy ON pharmacy_inventory(pharmacy_id);
CREATE INDEX IF NOT EXISTS idx_inventory_med ON pharmacy_inventory(medicine_id);
CREATE INDEX IF NOT EXISTS idx_inventory_available ON pharmacy_inventory(is_available);

CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_pharmacy ON orders(pharmacy_id);
CREATE INDEX IF NOT EXISTS idx_orders_delivery ON orders(delivery_person_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(order_status);
CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at);

CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_history_order ON order_status_history(order_id);

CREATE INDEX IF NOT EXISTS idx_payments_order ON payments(order_id);
CREATE INDEX IF NOT EXISTS idx_payments_txn ON payments(transaction_reference);

CREATE INDEX IF NOT EXISTS idx_prescriptions_customer ON prescriptions(customer_id);
CREATE INDEX IF NOT EXISTS idx_prescriptions_status ON prescriptions(status);

CREATE INDEX IF NOT EXISTS idx_delivery_assignments_person ON delivery_assignments(delivery_person_id);
CREATE INDEX IF NOT EXISTS idx_delivery_assignments_status ON delivery_assignments(status);

CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at);
