# MediApp Automated Test Coverage & Verification Report

**Audit Date**: November 12, 2026  
**Testing Frameworks**: Pytest 9.1.1, Pytest-Cov 7.1.0, Playwright 1.58.0 (Chromium Headless Shell v1254)  
**Execution Runtime**: Python 3.14.4 / Python 3.11 on Windows 11  
**Total Tests**: 65 Pytest Tests + 12 Browser Automation Stages + 15 Live Cross-Portal Verification Stages  
**Test Pass Rate**: **100% (65/65 passed in 51.65s)**  

---

## 1. Executive Summary

This report provides a formal evaluation of the automated test coverage for the **MediApp** platform. Testing spans three distinct tiers of verification:
1. **Tier 1: Isolated Unit & Domain Service Tests** (Mathematical pricing precision, finite state machine transitions, clinical DDI normalizers, and atomic inventory decrement/restore operations).
2. **Tier 2: HTTP Integration & RBAC/Security Tests** (Flask test client exercising route blueprints, session management, IDOR boundaries, SQL injection resilience, and multi-vendor cart conflict handling).
3. **Tier 3: Full End-to-End Real Browser Automation** (Playwright Chromium launching the web app in a real browser engine, typing into search boxes, triggering debounced input events, clicking dynamic DOM elements, inspecting modals, and validating cross-portal synchronization).

---

## 2. Test Suite Inventory

| Test Module | Test Functions | Scope & Verification Highlights | Status |
|---|---|---|---|
| `tests/test_pricing.py` | 5 | Decimal money quantizing, item subtotal calculation, standard delivery fee, free delivery threshold (>= ₹500), coupon discounts. | **PASSED** |
| `tests/test_state_machine.py` | 3 | Valid order state transitions, rejection of illegal jumps (e.g. `PLACED` → `DELIVERED`), unauthorized role transitions. | **PASSED** |
| `tests/test_inventory.py` | 3 | Real-time stock checks, atomic decrement and restore, overselling prevention under zero/insufficient inventory. | **PASSED** |
| `tests/test_ddi.py` | 5 | Substance nomenclature normalization, salt radical stripping, contraindicated pairs (Sildenafil + Nitrates), safe combinations, generic alternative bioequivalents. | **PASSED** |
| `tests/test_auth_rbac.py` | 16 | Demo login, credential login across all 4 roles, invalid password rejection, customer registration validation, duplicate email 409, deactivated user rejection, Google OAuth flow, cross-pharmacy cart conflict (DEF-15), static asset 404 behavior (DEF-03). | **PASSED** |
| `tests/test_api_orders.py` | 7 | Order creation from cart, IDOR protection on order inspection, IDOR on customer order cancellation, customer state transition lockdown, pharmacy store isolation, payment rejection on cancelled orders, delivery claim concurrency race handling (DEF-08). | **PASSED** |
| `tests/test_api_payments.py` | 2 | Payment initiation, Razorpay signature validation, demo payment state progression, duplicate payment callback prevention. | **PASSED** |
| `tests/test_api_prescriptions.py` | 3 | File upload extension/MIME validation, PDF/image OCR parsing, pharmacist verification workflow. | **PASSED** |
| `tests/test_api_ai.py` | 2 | Emergency red-flag triage alert (112/911 banner), mild OTC consultation response generation. | **PASSED** |
| `tests/test_e2e_scenarios.py` | 5 | Scenario A (Installation & health check), Scenarios B–D (Complete cross-portal order lifecycle), Scenario E (Admin metrics computation), Scenario F (Order cancellation & inventory restoration), Scenario G (Prescription upload & approval). | **PASSED** |
| `tests/test_edge_cases_and_security.py` | 13 | Boundary values & empty inputs, SQL/XSS injection resilience, unauthenticated API lockout, prescription HIPAA privacy (DEF-05), admin lockout protection (DEF-11), state machine illegal transition matrix, pricing edge cases, DDI screening, prescription verification order auto-sync and rejection stock restoration (DEF-16, DEF-17), rejected rx reuse rejection (DEF-18), pharmacy inventory CRUD & deletion (DEF-19), courier capacity limit enforcement (DEF-21), zero-byte prescription rejection (DEF-22), admin nonexistent pharmacy 404 (DEF-23). | **PASSED** |
| `tests/test_browser_suite.py` | 1 (12 stages) | Real Playwright Chromium end-to-end execution of all 12 operational stages across the actual DOM and UI. | **PASSED** |
| **Total Automated Pytest Suite** | **65** | **Complete regression suite** | **65/65 PASSED** |

---

## 3. Real Browser E2E Suite Breakdown (Playwright Chromium)

The browser test suite (`tests/test_browser_suite.py`) operates a real Chromium instance against the running Flask application on `http://127.0.0.1:5000/`.

- **Stage 1: Home Page Loading & Theme Toggle**  
  Verifies page render, document title, navigation links, and theme toggle switching between light and dark modes.
- **Stage 2: Customer Registration & Auth Flow**  
  Registers a fresh unique customer account, verifies password validation, tests invalid credential error toast, verifies session persistence on reload, and completes logout.
- **Stage 3: Demo Quick Switcher**  
  Tests the 1-click demo persona switcher bar, cycling through Customer, Pharmacy, Delivery, and Admin roles.
- **Stage 4: Catalogue Search, Debounce & Generic Alternatives**  
  Tests typing in the medicine search bar with a 250ms debounce, verifies that focus is retained, searches for "Paracetamol", filters by category pills, resets filter with "All Categories" (DEF-04), and opens the generic alternative comparison modal.
- **Stage 5: Cart Management & Drawer**  
  Adds medicines to cart, opens sliding cart drawer, increments quantity, and verifies live subtotal recalculation.
- **Stage 6: Clinical AI Assistant**  
  Submits clinical symptoms to the AI consultation dialog, verifying emergency triage detection and red-flag alerts.
- **Stage 7: Prescription Upload & OCR**  
  Uploads a prescription file through the customer interface, verifying file acceptance and extraction feedback.
- **Stage 8: Customer Checkout & Payment**  
  Completes checkout form with shipping address, executes demo payment, receives authoritative order ID (`ORD-YYYYMMDD-XXXX`), and inspects invoice details.
- **Stage 9: Pharmacy Order Fulfillment & Inventory Management**  
  Switches to Pharmacy Portal, verifies real-time queue receipt, accepts order, transitions to `PREPARING` and `READY_FOR_PICKUP`, performs stock inventory search, and edits medicine batch and quantity.
- **Stage 10: Delivery Dispatch & Doorstep Handover**  
  Switches to Delivery Portal, browses available orders pool, claims the order, picks up from pharmacy (`PICKED_UP`), moves en route (`IN_TRANSIT`), and confirms customer delivery (`DELIVERED`).
- **Stage 11: Admin Governance & System Diagnostics**  
  Switches to Admin Portal, verifies updated platform GMV revenue, inspects user governance directory, audits pharmacy partners, and verifies system health check status.
- **Stage 12: Cross-Portal Synchronization Confirmation**  
  Returns to Customer Portal and verifies that the active order's tracking timeline displays `DELIVERED`.

---

## 4. Statement-Level Code Coverage Analysis

```
Name                                Stmts   Miss  Cover   Missing
-----------------------------------------------------------------
app\__init__.py                        68     17    75%   29, 66-68, 72-74, 78-80, 85, 89, 93-99, 104
app\config.py                          66      9    86%   73, 76-81, 112-113
app\database.py                        58      9    84%   16-17, 35, 79-84
app\migrations.py                      17     17     0%   5-35
app\routes\admin_routes.py             96     21    78%   91-92, 113, 117-121, 127-132, 141, 148-149, 155-162, 168-170
app\routes\ai_routes.py                18      6    67%   21-26
app\routes\auth_routes.py             177     31    82%   57-58, 94-95, 117-118, 122-123, 138, 159-160, 179-180, 221, 236-241, 246-263, 296
app\routes\cart_routes.py             135     40    70%   22-28, 80, 82-83, 118, 134, 145, 155, 159, 168-192, 197-204
app\routes\delivery_routes.py         188     80    57%   16, 20, 22, 28-35, 42-72, 85-86, 104-124, 133-134, 144, 159, 169, 195-196, 218-221, 229-230, 252-255, 263-264, 289-292, 298-329, 335-346
app\routes\health_routes.py            25      4    84%   18-19, 38-39
app\routes\medicine_routes.py          74     31    58%   37-38, 41-42, 45-46, 51-70, 101-121, 125-131, 135-140, 145-155, 160-161
app\routes\order_routes.py            100     32    68%   28, 33, 37, 41, 67-68, 76-118, 132, 136, 138, 152, 168, 171-172, 195-198
app\routes\payment_routes.py           72     32    56%   20, 27, 29, 36-37, 45, 51, 53, 60-61, 66-98
app\routes\pharmacy_routes.py         178     83    53%   17, 19, 22, 24, 32-75, 96-119, 127-128, 132, 145-148, 154-179, 187-188, 204, 242-243, 254, 271-274, 280-312, 320-321
app\routes\prescription_routes.py     140     39    72%   26, 30, 58-59, 120-143, 162, 165, 168, 173-174, 185, 188, 196, 209, 240-242, 259-272
app\seed.py                            87      4    95%   46, 78, 179, 259
app\services\ai_service.py             50     18    64%   88, 103-136, 157
app\services\auth_service.py          217     71    67%   24, 49, 53, 110, 113, 115, 122, 124, 126, 135, 163, 173, 177, 186-203, 208-282, 286-287, 332, 335-336
app\services\ddi_service.py            71      2    97%   50, 132
app\services\inventory_service.py      54      5    91%   14, 60, 62, 135, 137
app\services\ocr_service.py           107     25    77%   22-26, 37-38, 44-46, 60, 89-90, 105-108, 127, 135-137, 151-152, 158-159
app\services\order_service.py         119     16    87%   105, 143, 155, 164, 173, 175, 196, 207, 293, 311, 314, 329-333, 379, 417-418
app\services\payment_service.py       107     38    64%   20, 28, 50, 59-64, 68-71, 75-87, 98-116, 124-131, 140, 147, 183, 188, 195-207, 217
app\services\pricing_service.py        33      2    94%   60, 69
-----------------------------------------------------------------
TOTAL                                2257    632    72%
```

### Coverage Highlights:
- **Core Domain Services**:
  - `ddi_service.py`: **97%**
  - `pricing_service.py`: **94%**
  - `inventory_service.py`: **91%**
  - `order_service.py`: **87%**
  - `ocr_service.py`: **77%**
- **Security & Database**:
  - `seed.py`: **95%**
  - `config.py`: **86%**
  - `database.py`: **84%**
  - `auth_routes.py`: **82%**

---

## 5. Unverified Aspects & Limitations

While automated and browser verification achieved 100% pass rates across local and demo fixtures, the following real external provider paths were not subjected to live production billing:
1. **Live Razorpay Gateway Execution**: Tested in `APP_MODE=demo` and with simulated webhook HMAC signatures. Live production credit card charges through Razorpay's live production banking gateway were deliberately not executed to avoid financial transactions.
2. **Live Google Gemini API Tokens**: Tested with local clinical AI triage rules and simulated API responses. Live upstream Gemini API key quota consumption was not tested against production billing accounts.
3. **Physical SMS OTP Gateways**: SMS OTP delivery was validated using mock token stores rather than physical cellular telecom SMS gateways.
4. **Physical Mobile Device Viewports**: Browser testing was executed in Chromium desktop viewport (1280x800). Real mobile hardware touch gestures were not tested on physical iOS/Android devices.
