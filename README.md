# MediApp — Unified Medicine Delivery Platform

A complete, production-grade, ground-up rebuild of **MediApp**: a multi-portal medicine discovery and delivery platform connecting Patients, Pharmacies, Delivery Partners, and System Administrators through a single authoritative backend.

---

## 🌟 Key Capabilities & Architectural Highlights

1. **One Shared Order Engine**:
   - Single authoritative order record (`ORD-YYYYMMDD-XXXX`) shared seamlessly across Customer, Pharmacy, Delivery, and Admin portals.
   - Mathematical decimal-safe currency calculations (`Decimal('0.01')` with `ROUND_HALF_UP`) preventing floating-point rounding errors across all portals.
   - Strict server-side finite state machine enforcing legal order transitions (`PLACED` → `CONFIRMED` → `PACKAGING` → `READY_FOR_PICKUP` → `ASSIGNED` → `OUT_FOR_DELIVERY` → `DELIVERED` or `CANCELLED`).
   - Atomic inventory reservation during order placement and automatic stock restoration upon cancellation.

2. **Real Medicine Catalogue (1,250 Medicines)**:
   - High-fidelity catalogue ingested from `app/data/A_Z_medicines.csv` covering OTC, Scheduled H/H1, and Chronic care therapeutics.
   - Debounced search (250ms) with persistent input focus retention (typing does not lose focus or cause DOM teardown).
   - Bioequivalent generic medicine recommendations with real-time price comparison and cost-savings calculation.

3. **Clinical Drug-Drug Interaction (DDI) Screening**:
   - Automated active ingredient normalizer and pairwise clinical interaction engine screening against 15+ major drug interaction rules (e.g., Sildenafil + Nitrates contraindicated, ACE inhibitors + Potassium-sparing diuretics hyperkalemia risk).

4. **Multi-Tier Prescription OCR & Verification**:
   - Secure PDF and image prescription upload with MIME validation, size caps, and hash tracking.
   - Multi-tier text extraction (digital PDF text via `pypdf`, image OCR via `pytesseract`, pattern-based clinical entity extraction for Doctor name, Patient name, and Rx lines).
   - Pharmacist review and verification workflow preventing unauthorized dispensing of prescription-only medicines.

5. **AI Ailment Assistant (Gemini REST Integration)**:
   - Automated emergency red-flag triage detection (chest pain, stroke, severe breathing distress) immediately redirecting to emergency hotlines (`112` / `911`).
   - Dual-mode architecture: Real cloud generation via Google Gemini API (`gemini-1.5-flash`), with transparently labelled local clinical triage fallback for zero-dependency offline environments.

6. **Payment System (Razorpay Real & Demo Modes)**:
   - Separate demo and real execution modes.
   - Real mode implements official Razorpay order creation and cryptographic HMAC-SHA256 signature verification.
   - Demo mode provides high-fidelity simulation with transaction tracking, replay rejection, and idempotent state synchronization.

7. **Four Unified Portals in a Responsive Single Page Application (SPA)**:
   - **Customer Portal**: Debounced search, pharmacy inventory selector, interactive cart, generic substitution, prescription upload, and live order tracking.
   - **Pharmacy Portal**: Real-time KPI dashboard, order fulfillment queue, inventory CRUD with batch and expiry tracking, and prescription verification.
   - **Delivery Portal**: Available delivery pool, assignment claiming, step-by-step transit milestones, and doorstep handover confirmation.
   - **Admin Portal**: Executive platform KPI analytics, pharmacy onboarding approvals, user governance, and live system health diagnostics.

---

## 🏗️ System Architecture & Technology Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | Python 3.12+ / Flask with Application Factory & 11 modular Blueprints |
| **Database** | SQLite 3 with WAL Mode, Strict Foreign Key Enforcement (`PRAGMA foreign_keys = ON`), and 16 indexes |
| **Frontend** | Vanilla JavaScript (ES6+ modular modules), Vanilla CSS (Custom Design System, Dark Mode, Responsive Breakpoints), HTML5 |
| **Authentication** | Session-based Auth with PBKDF2-SHA256 password hashing, Google OAuth 2.0 flow, and 1-click Demo Switcher |
| **Payments** | Razorpay Python SDK + HMAC-SHA256 Signature Verification + Local Demo Provider |
| **AI / OCR** | Google Gemini REST API, `pypdf`, `pytesseract`, PIL / Pillow |
| **Testing** | `pytest`, `pytest-cov` (32 tests covering Scenarios A through G) |

---

## 🚀 Quickstart & Setup Guide (Windows)

### Prerequisites
- Python 3.12 to 3.14 installed and available on PATH
- Windows 10/11 with PowerShell

### 1. Clone & Enter Project Directory
```powershell
cd d:\MediApp
```

### 2. Set Up Virtual Environment
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```
Default configuration runs in `APP_MODE=demo` and `APP_ENV=development` with zero external dependencies needed.

### 5. Initialize Database & Seed Catalogue
```powershell
python -c "from app.database import init_db; from app.seed import seed_database; init_db('mediapp.db'); seed_database('mediapp.db')"
```
This migrates the 17 tables, ingests all 1,250 medicines from `app/data/A_Z_medicines.csv`, stocks 2,500 inventory items across 3 pharmacies, and provisions demo accounts.

### 6. Run the Application
```powershell
python run.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000/
```

---

## 👥 Demo Accounts (1-Click Switcher or Credentials)

You can switch between any of the 4 roles using the **Quick Demo Switcher** bar at the top of the interface, or log in manually with the following credentials:

| Role | Name / Organization | Email | Password |
|---|---|---|---|
| **Customer** | Aditi Sharma | `customer@mediapp.local` | `Demo@Customer123` |
| **Pharmacy 1** | Apollo Pharmacy Koramangala | `apollo.koramangala@mediapp.local` | `Demo@Pharmacy123` |
| **Pharmacy 2** | MedPlus Pharmacy BTM Layout | `medplus.btm@mediapp.local` | `Demo@Pharmacy123` |
| **Delivery Rider 1** | Rajesh Kumar (Scooter) | `rajesh.delivery@mediapp.local` | `Demo@Delivery123` |
| **Delivery Rider 2** | Suresh Nair (Motorcycle) | `suresh.delivery@mediapp.local` | `Demo@Delivery123` |
| **Administrator** | System Administrator | `admin@mediapp.local` | `Demo@Admin123` |

---

## 🧪 Automated Testing Suite

MediApp includes an extensive automated test suite covering unit calculations, database integrity, state transitions, API endpoints, and end-to-end acceptance scenarios (Scenarios A through G):

```powershell
# Run all tests
.\.venv\Scripts\python.exe -m pytest -v

# Run with coverage report
.\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing tests/
```

### Test Coverage Highlights:
- `tests/test_pricing.py`: Decimal quantizing, tax calculations, free delivery thresholds, discount math.
- `tests/test_state_machine.py`: Legal order state transitions and role permission enforcement.
- `tests/test_inventory.py`: Concurrent stock checks, atomic reservation, overselling prevention, stock restoration.
- `tests/test_ddi.py`: Substance name normalization, contraindicated drug interactions, generic bioequivalent matching.
- `tests/test_auth_rbac.py`: Session management, role-based access control, IDOR protection.
- `tests/test_api_orders.py`: Cart to order conversion, order item snapshots, customer data isolation.
- `tests/test_api_payments.py`: Razorpay signature validation, demo payment progression, replay rejection.
- `tests/test_api_prescriptions.py`: Upload validation, OCR entity extraction, pharmacist verification flow.
- `tests/test_api_ai.py`: Emergency red-flag triage warnings, clinical OTC suggestions.
- `tests/test_e2e_scenarios.py`:
  - **Scenario A**: Clean installation & health check diagnostics.
  - **Scenarios B–D**: Complete cross-portal order lifecycle across Customer, Pharmacy, and Delivery partners on ONE authoritative order ID.
  - **Scenario E**: Admin oversight & real database analytics computation.
  - **Scenario F**: Order cancellation and atomic inventory restoration.
  - **Scenario G**: Prescription upload, digital parsing, and pharmacist approval.

---

## ⚙️ External Provider Configuration (Real Mode)

To switch the application from `demo` to `real` mode, set `APP_MODE=real` in `.env` and provide credentials for external providers:

### 1. Google OAuth 2.0
- **Google Cloud Console**: Create OAuth 2.0 Web Client Credentials.
- **Authorized Redirect URI**: `http://127.0.0.1:5000/api/auth/google/callback`
- **Configuration in `.env`**:
  ```env
  GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
  GOOGLE_CLIENT_SECRET=your-client-secret
  ```

### 2. Razorpay Payment Gateway
- **Razorpay Dashboard**: Obtain API Keys in Test or Live mode.
- **Webhook URL**: `http://127.0.0.1:5000/api/payments/webhook`
- **Configuration in `.env`**:
  ```env
  RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxx
  RAZORPAY_KEY_SECRET=your_razorpay_secret
  RAZORPAY_WEBHOOK_SECRET=your_webhook_secret
  ```

### 3. Google Gemini AI API
- **Google AI Studio**: Obtain an API key for `gemini-1.5-flash`.
- **Configuration in `.env`**:
  ```env
  GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxx
  ```

### 4. Tesseract OCR (Optional for local image OCR)
- Download and install Tesseract-OCR for Windows.
- **Configuration in `.env`**:
  ```env
  TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
  ```

---

## 📁 Repository Directory Structure

```
d:/MediApp/
├── app/
│   ├── data/
│   │   ├── A_Z_medicines.csv       # Ingested 1,250 medicine catalogue
│   │   └── ddi_rules.json          # Clinical Drug-Drug Interaction ruleset
│   ├── routes/                     # 11 Modular Flask Blueprints
│   │   ├── admin_routes.py
│   │   ├── ai_routes.py
│   │   ├── auth_routes.py
│   │   ├── cart_routes.py
│   │   ├── delivery_routes.py
│   │   ├── health_routes.py
│   │   ├── medicine_routes.py
│   │   ├── order_routes.py
│   │   ├── payment_routes.py
│   │   ├── pharmacy_routes.py
│   │   └── prescription_routes.py
│   ├── services/                   # Core Domain Logic Services
│   │   ├── ai_service.py
│   │   ├── auth_service.py
│   │   ├── ddi_service.py
│   │   ├── inventory_service.py
│   │   ├── ocr_service.py
│   │   ├── order_service.py
│   │   ├── payment_service.py
│   │   └── pricing_service.py
│   ├── static/                     # Frontend Client Assets
│   │   ├── css/
│   │   │   └── main.css            # Responsive Dark Mode Medical Design System
│   │   └── js/
│   │       ├── admin.js
│   │       ├── api.js
│   │       ├── app.js              # SPA Orchestrator
│   │       ├── components.js
│   │       ├── customer.js
│   │       ├── delivery.js
│   │       ├── pharmacy.js
│   │       ├── state.js            # Reactive Application State Store
│   │       └── sync.js             # Visibility-aware Background Polling
│   ├── templates/
│   │   └── index.html              # Responsive SPA Shell
│   ├── config.py                   # Configuration & Safe Capability Flags
│   ├── database.py                 # SQLite WAL Connection Provider
│   ├── migrations.py               # Schema Migrations Runner
│   ├── schema.sql                  # 17 Tables, Constraints & 16 Indexes
│   └── seed.py                     # Idempotent Database Seeder
├── tests/                          # 32 Pytest Automated Test Cases
│   ├── conftest.py
│   ├── test_api_ai.py
│   ├── test_api_orders.py
│   ├── test_api_payments.py
│   ├── test_api_prescriptions.py
│   ├── test_auth_rbac.py
│   ├── test_ddi.py
│   ├── test_e2e_scenarios.py
│   ├── test_inventory.py
│   ├── test_pricing.py
│   └── test_state_machine.py
├── uploads/                        # Prescription File Storage (Protected)
├── .env.example
├── generate_data.py                # Synthetic Catalogue & Clinical DDI Generator
├── requirements.txt
└── run.py                          # Server Startup Entrypoint
```

---

## 🔒 Security & Privacy Guarantees

- **No Secrets in Frontend**: Razorpay secret keys, Gemini API keys, and OAuth client secrets are strictly confined to server-side configuration.
- **SQL Injection Prevention**: 100% of database queries use parameterized SQL (`?` placeholders).
- **IDOR Protection**: Customers can only view their own orders/prescriptions; pharmacy staff can only access orders and inventory for their designated store; delivery riders can only view deliveries assigned to them.
- **Protected File Uploads**: Uploaded prescriptions are sanitized with UUID filenames, validated for safe extensions and MIME types, capped at 10 MB, and served exclusively through authenticated, role-checked endpoints.
- **Replay-Protected Payments**: Payment verification tokens and signatures are recorded in a dedicated `payment_transactions` table to prevent transaction reuse or duplicate callbacks.
