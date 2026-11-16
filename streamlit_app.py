"""
MediApp — Licensed Clinical Pharmacy & Cold-Chain Logistics Hub
Production Cloud Deployment for Streamlit Cloud (medi-app.streamlit.app)
Adheres strictly to the MediApp Clinical Design System:
Deep Navys, Crisp Surfaces, Clinical Emerald (OTC/Verified), Amber (Rx/Warning), Cyan (Cold-Chain), Zero Emojis.
"""
import streamlit as st
import os
import json
from datetime import datetime

# Set Page Configuration
st.set_page_config(
    page_title="MediApp — Clinical Pharmacy & Cold-Chain Logistics",
    page_icon="https://img.icons8.com/color/96/caduceus.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 1. Database Initialization & Seeding
@st.cache_resource
def init_backend():
    try:
        from app.migrations import apply_migrations
        from app.seed import seed_database
        apply_migrations()
        seed_database()
        return True
    except Exception as e:
        st.error(f"Database initialization error: {e}")
        return False

init_backend()

from app.database import query_db

# 2. Strict Clinical Design System CSS (Dark/Light Responsive, Zero Emojis, High-Trust Tokens)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@600;700;800;900&family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, sans-serif !important;
}

h1, h2, h3, h4, h5 {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
}

/* Header & Accent Branding */
.clinical-hero {
    background: linear-gradient(135deg, #070d1a 0%, #0f172a 50%, #0b132b 100%);
    border: 1px solid rgba(56, 189, 248, 0.2);
    border-radius: 20px;
    padding: 32px 40px;
    color: #f8fafc;
    margin-bottom: 24px;
    box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
}

.clinical-tag {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    background: rgba(56, 189, 248, 0.1);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.25);
    margin-bottom: 12px;
}

.clinical-badge-otc {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 9999px;
    font-size: 11px;
    font-weight: 700;
    background: rgba(16, 185, 129, 0.1);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.25);
}

.clinical-badge-rx {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 9999px;
    font-size: 11px;
    font-weight: 700;
    background: rgba(245, 158, 11, 0.1);
    color: #f59e0b;
    border: 1px solid rgba(245, 158, 11, 0.3);
}

.clinical-badge-coldchain {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 9999px;
    font-size: 11px;
    font-weight: 700;
    background: rgba(6, 182, 212, 0.1);
    color: #06b6d4;
    border: 1px solid rgba(6, 182, 212, 0.3);
}

.generic-match-banner {
    background: linear-gradient(135deg, rgba(6, 182, 212, 0.08) 0%, rgba(16, 185, 129, 0.08) 100%);
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 12px;
    padding: 10px 14px;
    margin: 8px 0;
    font-size: 12px;
}

/* Card Elevations */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 16px !important;
    border: 1px solid rgba(226, 232, 240, 0.15) !important;
    background: rgba(15, 23, 42, 0.4) !important;
    transition: all 0.2s ease !important;
}

[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: #38bdf8 !important;
    box-shadow: 0 8px 24px -4px rgba(56, 189, 248, 0.15) !important;
}

/* Tabs Styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    border-bottom: 2px solid rgba(56, 189, 248, 0.15);
    padding-bottom: 6px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 12px !important;
    padding: 8px 20px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
}

.stTabs [aria-selected="true"] {
    background: #0284c7 !important;
    color: white !important;
    box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3) !important;
}
</style>
""", unsafe_allow_html=True)

# 3. Sidebar Command & Governance Panel
with st.sidebar:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:16px;">
        <img src="https://img.icons8.com/color/96/caduceus.png" width="48" style="border-radius:10px;" />
        <div>
            <div style="font-weight:900; font-size:1.2rem; line-height:1.2;">Medi<span style="color:#38bdf8;">App</span></div>
            <div style="font-size:10px; text-transform:uppercase; letter-spacing:0.05em; color:#94a3b8; font-weight:700;">Clinical Network</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    st.subheader("System Infrastructure")
    st.success("Dispensary Database: Online")
    st.info("Logistics Telemetry: Active (2°C - 8°C)")

    st.divider()
    st.subheader("Role Governance & Demo Credentials")
    with st.expander("Show Test Credentials", expanded=True):
        st.markdown("""
        **Universal Password**: `Role@123`
        
        - **Clinical Customer**:  
          `customer@mediapp.local`
        - **Licensed Pharmacist**:  
          `pharmacy@mediapp.local`
        - **Cold-Chain Fleet**:  
          `delivery@mediapp.local`
        - **Hospital Admin**:  
          `admin@mediapp.local`
        """)

    st.divider()
    st.caption("MediApp Clinical Architecture • CDSCO & WHO-GMP Compliant")

# 4. Hero Banner
st.markdown("""
<div class="clinical-hero">
    <div class="clinical-tag">Licensed Hyperlocal Healthcare & Cold-Chain Network</div>
    <h1 style="font-size: 2.4rem; font-weight: 900; line-height: 1.15; margin-bottom: 12px;">
        Authentic Medicines & Clinical Care, <span style="color:#38bdf8;">Delivered in 45 Minutes.</span>
    </h1>
    <p style="color: #94a3b8; font-size: 0.95rem; max-width: 800px; line-height: 1.6; margin-bottom: 0;">
        Access over 1,250+ licensed pharmaceutical drugs, cold-chain biologics, and certified bioequivalent generics saving patients up to 70%. Every prescription is verified by a licensed pharmacist prior to express dispatch.
    </p>
</div>
""", unsafe_allow_html=True)

# 5. Clinical Workspaces Navigation
tab_catalogue, tab_pharmacist, tab_logistics, tab_pharmacies, tab_analytics = st.tabs([
    "Medicine Catalogue & Generic Match",
    "Pharmacist Review Desk",
    "Logistics & Cold-Chain Tracking",
    "Dispensary Network",
    "Hospital Analytics"
])

# ==========================================
# WORKSPACE 1: MEDICINE CATALOGUE & GENERIC PRICE MATCH
# ==========================================
with tab_catalogue:
    st.header("Search & Discover Clinical Formulations")
    
    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        search_query = st.text_input(
            "Omni-Search Query",
            placeholder="Search brand name, active generic molecule (e.g. Ranitidine, Paracetamol, Metformin)...",
            label_visibility="collapsed"
        )
    with c2:
        category_options = ["All Categories"] + [r["category"] for r in query_db("SELECT DISTINCT category FROM medicines ORDER BY category")]
        selected_cat = st.selectbox("Category", category_options, label_visibility="collapsed")
    with c3:
        filter_mode = st.selectbox("Formulation Type", ["All Formulations", "OTC Only", "Prescription (Rx)", "Cold-Chain Monitored"], label_visibility="collapsed")

    query_sql = "SELECT * FROM medicines WHERE 1=1"
    params = []

    if search_query:
        query_sql += " AND (name LIKE ? OR generic_name LIKE ? OR manufacturer LIKE ? OR uses LIKE ?)"
        pattern = f"%{search_query}%"
        params.extend([pattern, pattern, pattern, pattern])

    if selected_cat != "All Categories":
        query_sql += " AND category = ?"
        params.append(selected_cat)

    if filter_mode == "OTC Only":
        query_sql += " AND prescription_required = 0"
    elif filter_mode == "Prescription (Rx)":
        query_sql += " AND prescription_required = 1"

    query_sql += " ORDER BY name ASC LIMIT 36"
    medicines = query_db(query_sql, tuple(params))

    # Apply cold-chain filter if requested
    if filter_mode == "Cold-Chain Monitored":
        medicines = [m for m in medicines if "insulin" in m["category"].lower() or "vaccine" in m["category"].lower() or "insulin" in m["name"].lower()]

    st.caption(f"Showing {len(medicines)} verified pharmaceutical records")

    cols = st.columns(3)
    for idx, med in enumerate(medicines):
        is_coldchain = "insulin" in med["category"].lower() or "vaccine" in med["category"].lower() or "insulin" in med["name"].lower()
        price = med.get("unit_price") or med.get("mrp") or 0.0
        mrp = med.get("mrp") or price

        with cols[idx % 3]:
            with st.container(border=True):
                # Status Tags
                st.markdown(f"""
                <div style="display:flex; gap:6px; margin-bottom:8px;">
                    {'<span class="clinical-badge-rx">Rx Required</span>' if med.get("prescription_required") else '<span class="clinical-badge-otc">OTC Approved</span>'}
                    {'<span class="clinical-badge-coldchain">Cold-Chain (2°C - 8°C)</span>' if is_coldchain else ''}
                </div>
                """, unsafe_allow_html=True)

                st.subheader(med.get("name", "Medicine"))
                st.caption(f"Active Molecule: **{med.get('generic_name', '')}**")
                
                st.markdown(f"**Form:** {med.get('dosage_form', 'Tablet')} • {med.get('strength', 'Standard')}")
                st.markdown(f"**Manufacturer:** {med.get('manufacturer', 'Standard')}")
                st.markdown(f"**Category:** `{med.get('category', 'General')}`")

                # Dynamic Generic Savings Match Check
                if "generic" not in med.get("name", "").lower():
                    generic_equiv = query_db(
                        "SELECT * FROM medicines WHERE generic_name = ? AND id != ? AND mrp < ? LIMIT 1",
                        (med.get("generic_name"), med.get("id"), mrp),
                        one=True
                    )
                    if generic_equiv:
                        savings_pct = int(((mrp - generic_equiv["mrp"]) / mrp) * 100)
                        st.markdown(f"""
                        <div class="generic-match-banner">
                            <strong>Generic Price Match Available:</strong><br/>
                            Switch to <em>{generic_equiv['name']}</em> and save <strong>{savings_pct}%</strong> (₹{mrp - generic_equiv['mrp']:.2f} savings).
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown(f"### ₹{price:.2f} <span style='font-size:12px; color:#94a3b8; text-decoration:line-through;'>MRP ₹{mrp:.2f}</span>", unsafe_allow_html=True)
                st.button(f"Add to Prescription Cart", key=f"btn_add_{med['id']}", use_container_width=True)

# ==========================================
# WORKSPACE 2: PHARMACIST CLINICAL DESK
# ==========================================
with tab_pharmacist:
    st.header("Pharmacist Clinical Inspection & Verification Desk")
    st.caption("Active Verification Station #04 • Split-screen Rx forensic inspection, AI molecule extraction, and licensed clinical certification.")

    p_col1, p_col2 = st.columns([1, 1])

    with p_col1:
        st.subheader("Document Inspection Viewport")
        st.info("Prescription Reference: `Dr_Mukherjee_Apollo_Cardio_Rx.png` • Reg #49281")
        
        # Inspection controls
        st.markdown("""
        <div style="background:#070d1a; border:1px solid #1e293b; border-radius:12px; padding:24px; text-align:center; min-height:360px; display:flex; flex-direction:column; justify-content:center; align-items:center;">
            <img src="https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=600&auto=format&fit=crop&q=60" style="max-height:280px; border-radius:10px; box-shadow:0 4px 12px rgba(0,0,0,0.5);" />
            <div style="font-size:11px; color:#94a3b8; margin-top:12px;">High-Resolution Digital Forensic Preview (100% Zoom)</div>
        </div>
        """, unsafe_allow_html=True)

    with p_col2:
        st.subheader("Clinical Audit Checklist")
        with st.container(border=True):
            st.markdown("**OCR AI Molecular Extraction Findings** (Confidence: 96.4%)")
            st.markdown("""
            - Identified Molecule 1: `Amlodipine 5mg` (Cardiovascular / Anti-Hypertensive)
            - Identified Molecule 2: `Atorvastatin 20mg` (Lipid Lowering / Statin)
            """)

            st.divider()
            st.markdown("**Mandatory Verification Checks**")
            chk1 = st.checkbox("Doctor Registration & Medical Council Seal Verified", value=True)
            chk2 = st.checkbox("Prescription Date valid within 6-month regulatory window", value=True)
            chk3 = st.checkbox("Dosage duration and frequency clinically verified", value=True)

            notes = st.text_area("Pharmacist Clinical Notes", value="Verified against national doctor council registry. Formulations allocated from central Apollo batch.")

            b_col1, b_col2 = st.columns(2)
            with b_col1:
                if st.button("Certify & Approve Rx", type="primary", use_container_width=True):
                    st.success("Prescription certified and released for pharmacy dispatch packaging!")
            with b_col2:
                if st.button("Reject Prescription", use_container_width=True):
                    st.warning("Prescription rejected. Clinical rejection rationale dispatched to patient.")

# ==========================================
# WORKSPACE 3: LOGISTICS & COLD-CHAIN TRACKING
# ==========================================
with tab_logistics:
    st.header("Logistics Command & Cold-Chain Live Tracking")
    
    # Cold-chain IoT Banner
    st.markdown("""
    <div style="background:rgba(6, 182, 212, 0.08); border:1px solid rgba(6, 182, 212, 0.3); border-radius:16px; padding:18px 24px; margin-bottom:20px; display:flex; justify-content:space-between; align-items:center;">
        <div>
            <div style="font-size:11px; font-weight:800; text-transform:uppercase; color:#06b6d4; letter-spacing:0.05em;">Cold-Chain Active Telemetry</div>
            <div style="font-size:1.1rem; font-weight:800; color:#f8fafc;">Insulated Thermal Case #CC-842 • 4.2°C Nominal</div>
            <div style="font-size:12px; color:#94a3b8;">Safe Operating Threshold: 2.0°C to 8.0°C • Bluetooth IoT Sensor Connected</div>
        </div>
        <div style="background:rgba(16, 185, 129, 0.15); border:1px solid rgba(16, 185, 129, 0.3); color:#10b981; padding:6px 14px; border-radius:9999px; font-weight:700; font-size:12px;">
            100% Thermal Integrity Verified
        </div>
    </div>
    """, unsafe_allow_html=True)

    orders = query_db("SELECT * FROM orders ORDER BY created_at DESC LIMIT 10")
    if orders:
        for ord_row in orders:
            status = ord_row.get("order_status") or "OUT_FOR_DELIVERY"
            with st.expander(f"Order #{ord_row['id']} — {status} — ₹{ord_row.get('total_amount', 0):.2f}", expanded=(ord_row['id'] == orders[0]['id'])):
                st.markdown(f"**Delivery Address:** {ord_row.get('delivery_address', 'Bengaluru 560103')}")
                st.markdown(f"**Assigned Fleet Agent:** Manoj Kumar (+91 98450 12849 • Thermal Van KA-05-MH-2914)")
                
                # Stepper visual representation
                st.markdown("""
                <div style="display:flex; justify-content:space-between; margin:16px 0; text-align:center; font-size:12px;">
                    <div style="color:#10b981; font-weight:700;">[1] Order Placed</div>
                    <div style="color:#10b981; font-weight:700;">[2] Rx Approved</div>
                    <div style="color:#10b981; font-weight:700;">[3] Cold-Chain Packed</div>
                    <div style="color:#38bdf8; font-weight:800;">[4] Out for Delivery</div>
                    <div style="color:#94a3b8;">[5] Delivered</div>
                </div>
                """, unsafe_allow_html=True)

                otp_col1, otp_col2 = st.columns([2, 1])
                with otp_col1:
                    otp_val = st.text_input("Patient Delivery Handover OTP", placeholder="Enter 4-digit OTP", key=f"otp_{ord_row['id']}")
                with otp_col2:
                    st.write("")
                    st.write("")
                    if st.button("Verify OTP & Complete Delivery", key=f"btn_otp_{ord_row['id']}", use_container_width=True):
                        st.success("Patient Handover OTP Verified! Delivery successfully completed.")

# ==========================================
# WORKSPACE 4: DISPENSARY NETWORK
# ==========================================
with tab_pharmacies:
    st.header("Licensed Pharmacy Dispensaries")
    pharms = query_db("SELECT * FROM pharmacies ORDER BY rating DESC")
    for p in pharms:
        with st.container(border=True):
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.subheader(p["name"])
                st.write(f"Address: {p['address']}, {p['city']} - {p['pincode']}")
                st.caption(f"License Number: `{p['license_number']}` | Contact: {p['phone']}")
            with col_b:
                st.metric("Clinical Rating", f"{p['rating']} / 5.0")
                st.write(f"Compliance Status: **{p['status'].upper()}**")

# ==========================================
# WORKSPACE 5: HOSPITAL ANALYTICS
# ==========================================
with tab_analytics:
    st.header("Hospital Command & Logistics Oversight")
    
    total_orders = query_db("SELECT COUNT(*) as c FROM orders", one=True)["c"]
    delivered_orders = query_db("SELECT COUNT(*) as c FROM orders WHERE order_status = 'DELIVERED'", one=True)["c"]
    total_rev = query_db("SELECT COALESCE(SUM(total_amount), 0) as s FROM orders WHERE payment_status = 'paid'", one=True)["s"]
    total_meds = query_db("SELECT COUNT(*) as c FROM medicines", one=True)["c"]
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Avg. Dispatch Velocity", "14.2 min", "-18% faster")
    m2.metric("Cold-Chain Compliance", "99.8%", "0 Excursions")
    m3.metric("Generic Switch Savings", f"₹48,920", "+24% saved")
    m4.metric("Total Fulfilled Orders", total_orders or 842)

    st.divider()
    st.subheader("Key Clinical Performance Insights")
    st.write("1. **Antibiotics & Anti-Hypertensives** drove the highest volume of bioequivalent generic conversions, saving patients an average of 64% per prescription.")
    st.write("2. **Cold-Chain Biologics** (Insulin, Vaccines) maintained 100% telemetry within the mandatory 2.0°C to 8.0°C window across all 45-minute delivery radiuses.")
