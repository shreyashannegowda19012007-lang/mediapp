"""
MediApp - Streamlit Cloud Showcase & Management Hub.
Provides an interactive cloud interface for querying the medicine catalogue,
inspecting cross-portal orders, auditing pharmacies and delivery fleets,
and viewing portal credentials and system metrics.
"""
import streamlit as st
import os
import json

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="MediApp - Licensed Healthcare Network",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 1. Initialize SQLite Database, Migrations and Idempotent Seed Data
@st.cache_resource
def init_backend():
    from app.migrations import apply_migrations
    from app.seed import seed_database
    apply_migrations()
    seed_database()
    return True

init_backend()

from app.database import query_db

# Custom Theme & Visual Overhaul Injection
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@600;700;800&family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, sans-serif;
}

h1, h2, h3, h4 {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
}

/* Gradient Header */
.main-title-gradient {
    background: linear-gradient(135deg, #0284c7 0%, #4f46e5 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.3rem !important;
    font-weight: 800 !important;
    margin-bottom: 0.2rem !important;
}

/* Container Cards */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 12px !important;
    transition: all 0.25s ease !important;
    background: rgba(255, 255, 255, 0.02) !important;
}

[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: #0284c7 !important;
    transform: translateY(-3px) !important;
    box-shadow: 0 10px 25px -5px rgba(2, 132, 199, 0.15) !important;
}

/* Styled Metric Cards */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(2, 132, 199, 0.06) 0%, rgba(79, 70, 229, 0.06) 100%);
    border: 1px solid rgba(2, 132, 199, 0.25);
    border-radius: 14px;
    padding: 16px 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.03);
}

/* Styled Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    border-bottom: 2px solid rgba(2, 132, 199, 0.15);
    padding-bottom: 4px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 20px !important;
    padding: 8px 18px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
    color: white !important;
    box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3) !important;
}
</style>
""", unsafe_allow_html=True)

# 2. Sidebar Navigation & System Information
with st.sidebar:
    st.image("https://img.icons8.com/color/96/caduceus.png", width=64)
    st.title("MediApp Hub")
    st.caption("Licensed Hyperlocal Healthcare & Pharmacy Network")
    st.divider()

    st.subheader("System Status")
    st.success("🟢 Database & API Online")
    st.info("⚡ Environment: Production / Showcase")

    st.divider()
    st.subheader("🔐 4-Portal Credentials")
    with st.expander("Show Demo Login Accounts", expanded=True):
        st.markdown("""
        **Standard Password**: `Role@123`
        
        - 🛒 **Customer**:  
          `customer@mediapp.local` / `Customer@123`
        - 💊 **Pharmacy**:  
          `pharmacy@mediapp.local` / `Pharmacy@123`
        - 🚴 **Delivery**:  
          `delivery@mediapp.local` / `Delivery@123`
        - 🛡️ **Admin**:  
          `admin@mediapp.local` / `Admin@123`
        """)

# 3. Main Header
st.title("💊 MediApp Healthcare Network")
st.markdown("Automated clinical dispensary, pharmacy fulfillment, delivery logistics, and administrative oversight.")

tab_catalogue, tab_orders, tab_pharmacies, tab_delivery, tab_metrics = st.tabs([
    "🛒 Medicine Catalogue",
    "📋 Live Orders & Tracking",
    "🏪 Partner Pharmacies",
    "🚴 Delivery Fleets",
    "📊 System Analytics"
])

# ==========================================
# TAB 1: MEDICINE CATALOGUE
# ==========================================
with tab_catalogue:
    st.header("Search & Browse Medicines")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input("🔍 Search medicine name, generic composition, or manufacturer", placeholder="e.g. Paracetamol, Dolo, Metformin, Augmentin")
    with col2:
        rx_filter = st.selectbox("Prescription Filter", ["All Items", "OTC Only (No Rx)", "Prescription Required (Rx)"])
        
    query_sql = "SELECT * FROM medicines WHERE 1=1"
    params = []
    
    if search_query:
        query_sql += " AND (name LIKE ? OR generic_name LIKE ? OR manufacturer LIKE ?)"
        term = f"%{search_query.strip()}%"
        params.extend([term, term, term])
        
    if rx_filter == "OTC Only (No Rx)":
        query_sql += " AND prescription_required = 0"
    elif rx_filter == "Prescription Required (Rx)":
        query_sql += " AND prescription_required = 1"
        
    query_sql += " ORDER BY name ASC LIMIT 30"
    medicines = query_db(query_sql, tuple(params))
    
    st.caption(f"Showing {len(medicines)} results")
    
    cols = st.columns(3)
    for idx, med in enumerate(medicines):
        with cols[idx % 3]:
            with st.container(border=True):
                st.subheader(med.get("name", "Unknown Medicine"))
                st.caption(f"Generic: **{med.get('generic_name', '')}** | {med.get('dosage_form', 'Unit')} ({med.get('strength', '')})")
                st.markdown(f"**Manufacturer:** {med.get('manufacturer', 'Standard')}")
                st.markdown(f"**Category:** `{med.get('category', 'General')}`")
                
                if med.get("prescription_required"):
                    st.error("📄 Prescription (Rx) Required")
                else:
                    st.success("🟢 OTC - No Prescription Needed")
                    
                st.markdown(f"### ₹{med.get('mrp', 0.0):.2f}")

# ==========================================
# TAB 2: LIVE ORDERS & TRACKING
# ==========================================
with tab_orders:
    st.header("Orders & Fulfillment Pipeline")
    status_filter = st.selectbox("Filter by Order Status", [
        "All Statuses", "PLACED", "ACCEPTED", "PREPARING", "READY_FOR_PICKUP", "IN_TRANSIT", "DELIVERED", "CANCELLED"
    ])
    
    order_sql = "SELECT * FROM orders WHERE 1=1"
    params = []
    if status_filter != "All Statuses":
        order_sql += " AND order_status = ?"
        params.append(status_filter)
    order_sql += " ORDER BY created_at DESC LIMIT 25"
    
    orders = query_db(order_sql, tuple(params))
    
    if not orders:
        st.info("No orders found matching this filter.")
    else:
        for ord_row in orders:
            with st.expander(f"📦 Order {ord_row['id']} — Status: {ord_row['order_status']} — Total: ₹{ord_row['total_amount']:.2f}"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(f"**Status:** `{ord_row['order_status']}`")
                    st.markdown(f"**Payment Status:** `{ord_row['payment_status']}`")
                with c2:
                    st.markdown(f"**Pharmacy ID:** {ord_row['pharmacy_id']}")
                    st.markdown(f"**Customer ID:** {ord_row['customer_id']}")
                with c3:
                    st.markdown(f"**Subtotal:** ₹{ord_row['subtotal']:.2f}")
                    st.markdown(f"**Total:** ₹{ord_row['total_amount']:.2f}")

# ==========================================
# TAB 3: PARTNER PHARMACIES
# ==========================================
with tab_pharmacies:
    st.header("Licensed Pharmacy Network")
    pharms = query_db("SELECT * FROM pharmacies ORDER BY rating DESC")
    for p in pharms:
        with st.container(border=True):
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.subheader(p["name"])
                st.write(f"📍 {p['address']}, {p['city']} - {p['pincode']}")
                st.caption(f"License Number: `{p['license_number']}` | Contact: {p['phone']}")
            with col_b:
                st.metric("Rating", f"⭐ {p['rating']}")
                status_color = "🟢" if p["status"] == "approved" else "🟡"
                st.write(f"{status_color} Status: **{p['status'].upper()}**")

# ==========================================
# TAB 4: DELIVERY FLEETS
# ==========================================
with tab_delivery:
    st.header("Active Delivery Fleet Couriers")
    couriers = query_db("""
        SELECT u.full_name, u.phone, dp.* 
        FROM delivery_profiles dp
        JOIN users u ON dp.user_id = u.id
    """)
    for c in couriers:
        with st.container(border=True):
            col_x, col_y = st.columns([3, 1])
            with col_x:
                st.subheader(c["full_name"])
                st.write(f"Vehicle: **{c['vehicle_type']}** (`{c['vehicle_number']}`)")
                st.caption(f"Driving License: `{c['driving_license']}` | Phone: {c['phone']}")
            with col_y:
                st.metric("Driver Rating", f"⭐ {c['rating']}")
                avail = "🟢 Available" if c["is_available"] else "🔴 On Delivery"
                st.write(f"Status: **{avail}**")

# ==========================================
# TAB 5: SYSTEM ANALYTICS
# ==========================================
with tab_metrics:
    st.header("Administrative Operational Metrics")
    
    total_orders = query_db("SELECT COUNT(*) as c FROM orders", one=True)["c"]
    delivered_orders = query_db("SELECT COUNT(*) as c FROM orders WHERE order_status = 'DELIVERED'", one=True)["c"]
    total_rev = query_db("SELECT COALESCE(SUM(total_amount), 0) as s FROM orders WHERE payment_status = 'paid'", one=True)["s"]
    total_meds = query_db("SELECT COUNT(*) as c FROM medicines", one=True)["c"]
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Orders Placed", total_orders)
    m2.metric("Orders Delivered", delivered_orders)
    m3.metric("Total Revenue", f"₹{total_rev:,.2f}")
    m4.metric("Catalogue Medicines", total_meds)
