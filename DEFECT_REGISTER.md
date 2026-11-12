# MediApp Comprehensive Defect Register & Resolution Log

**Version**: 1.0.0  
**Audit Date**: November 12, 2026  
**Status**: All Discovered Defects Resolved and Verified  

---

## 1. Defect Summary Table

| Defect ID | Severity | Component | Summary | Status |
|---|---|---|---|---|
| **DEF-01** | High | Auth / State Sync | Session fixation & stale UI state across portal role switching | **RESOLVED** |
| **DEF-02** | High | Customer / Search | Missing search input debounce causing high latency and search bar focus teardown | **RESOLVED** |
| **DEF-03** | Medium | Routing / Static | Missing static files returning HTTP 200 with index.html masking missing asset 404s | **RESOLVED** |
| **DEF-04** | Medium | Customer / UI | "All Categories" pill filter missing click event listener, preventing filter reset | **RESOLVED** |
| **DEF-05** | High | Prescription / RBAC | Delivery riders able to access customer prescriptions (HIPAA / Privacy risk) | **RESOLVED** |
| **DEF-06** | Medium | Customer / Modal | Order details modal dialog title corrupted by shared stock edit modal markup | **RESOLVED** |
| **DEF-07** | Medium | Delivery / GPS | Geolocation failure breaking transit status transitions when location denied | **RESOLVED** |
| **DEF-08** | High | Delivery / Concurrency | Race condition when multiple drivers simultaneously claim the same available order | **RESOLVED** |
| **DEF-09** | High | CSS / Layout | Sticky top navbar intercepting pointer clicks on scrolled elements (`scroll-padding`) | **RESOLVED** |
| **DEF-10** | High | CSS / Layout | Medicine card action buttons overflowing horizontally by 90px, overlapping neighbors | **RESOLVED** |
| **DEF-11** | Critical | Admin / Governance | Admin self-lockout risk via `toggle_user_status` allowing deactivation of all admins | **RESOLVED** |
| **DEF-12** | Critical | Order Service | Unchecked state machine transitions allowing skipping fulfillment phases | **RESOLVED** |
| **DEF-13** | Critical | Inventory Service | Concurrent checkout overselling inventory due to non-atomic stock verification | **RESOLVED** |
| **DEF-14** | High | DDI Service | Missing explicit `Sildenafil + Nitroglycerin` contraindication rule in ruleset | **RESOLVED** |
| **DEF-15** | High | Cart / Multi-Vendor | Cross-pharmacy items permitted in a single order without multi-vendor split logic | **RESOLVED** |
| **DEF-16** | Critical | Prescription / Order | Prescription verification failed to auto-transition orders from `AWAITING_PRESCRIPTION` | **RESOLVED** |
| **DEF-17** | High | Prescription / Inventory | Prescription rejection failed to cancel orders and restore reserved inventory stock | **RESOLVED** |
| **DEF-18** | High | Order / Security | Rejected prescriptions could be reused to place subsequent orders | **RESOLVED** |
| **DEF-19** | Medium | Pharmacy / Inventory | Missing `DELETE /api/pharmacy/inventory/<id>` and FK crash on invalid medicine ID | **RESOLVED** |
| **DEF-20** | Medium | Pharmacy / UI | Missing UI workflows for stocking new catalogue medicines and removing inventory | **RESOLVED** |
| **DEF-21** | Medium | Delivery / Batching | Uncapped delivery order claiming causing order orphaning in UI | **RESOLVED** |
| **DEF-22** | Low | Prescription / Upload | Zero-byte empty files accepted and processed as valid prescriptions | **RESOLVED** |
| **DEF-23** | Low | Admin / Governance | Admin update pharmacy status returning HTTP 200 on nonexistent pharmacy ID | **RESOLVED** |

---

## 2. Detailed Defect Reports & Code Resolutions

### DEF-01: Session Fixation & Stale UI State Across Role Switching
- **Severity**: High
- **Component**: `app/static/js/state.js`, `app/routes/auth_routes.py`
- **Symptom**: When switching roles using the Demo Switcher, the browser retained stale customer cart state or pharmacy queue data from the previous user.
- **Root Cause**: The client-side `state.js` reactive store did not emit a cache-purge event upon role transition, and the session cookie was updated without invalidating cached customer localStorage keys.
- **Resolution**:
  - Implemented `clearPortalState()` in `state.js` that resets active orders, carts, and cached responses upon `AUTH_STATE_CHANGED`.
  - Added session renewal in `/api/auth/switch-role` in `app/routes/auth_routes.py`.
- **Verification**: `tests/test_auth_rbac.py::test_switch_role_authorized_vs_unauthorized` passed.

---

### DEF-02: Missing Search Input Debounce & Focus Teardown
- **Severity**: High
- **Component**: `app/static/js/customer.js`
- **Symptom**: Typing in the medicine search bar re-rendered the catalogue container on every keystroke, causing the input element to lose DOM focus and dropping subsequent characters.
- **Root Cause**: Search event handler executed immediately without a debounce timer and directly mutated the parent DOM tree rather than targeted list repainting.
- **Resolution**:
  - Wrapped search input listener in a 250ms debounce utility function.
  - Isolated catalogue card grid rendering from the search input header to preserve input focus.
- **Verification**: Tested in Browser Stage 4 (typing "Paracetamol" in real Chromium without dropped keystrokes).

---

### DEF-03: Static Asset 404 Masking with `index.html`
- **Severity**: Medium
- **Component**: `app/routes/static_routes.py`
- **Symptom**: Requests to nonexistent static assets (e.g. `/static/js/nonexistent.js`) returned HTTP 200 with the HTML body of `index.html`, causing confusing `SyntaxError: Unexpected token '<'` in the browser console.
- **Root Cause**: The catch-all SPA route `@app.route('/<path:path>')` intercepted all unresolved requests without checking if the prefix was `/static/`.
- **Resolution**:
  - Added an explicit check in `static_routes.py`: if `path.startswith('static/')`, abort with `404 Not Found`.
- **Verification**: `tests/test_auth_rbac.py::test_static_asset_404_no_html_masking` passed.

---

### DEF-04: "All Categories" Pill Filter Missing Event Listener
- **Severity**: Medium
- **Component**: `app/static/js/customer.js`
- **Symptom**: Clicking on the "All Categories" pill (`.pill-filter[data-cat=""]`) failed to reset active category filters, leaving the catalogue permanently filtered by the previously clicked category.
- **Root Cause**: The click listener loop attached only to pills where `data-cat` was truthy (`if (pill.dataset.cat)`), ignoring the empty string attribute representing "all".
- **Resolution**:
  - Updated selector to bind to all `.pill-filter` elements.
  - Handled `data-cat === ""` by setting `state.selectedCategory = null` and triggering catalogue re-render.
- **Verification**: Browser Stage 4 verified filtering by "Antibiotic" followed by clicking "All Categories" restores the full 1,250 medicine list.

---

### DEF-05: Delivery Rider Access to Patient Medical Prescriptions
- **Severity**: High (Privacy / Compliance)
- **Component**: `app/routes/prescription_routes.py`, `app/routes/auth_routes.py`
- **Symptom**: Delivery riders could query `/api/prescriptions/<id>` and `/api/prescriptions/<id>/file` and inspect private clinical notes and prescriptions.
- **Root Cause**: The role check on prescription endpoints permitted any authenticated user who was part of an active order, without excluding the delivery role.
- **Resolution**:
  - Enforced strict authorization in `prescription_routes.py`: Only `customer` (owner of the prescription), `pharmacy` (assigned to dispense the order), and `admin` may access prescription metadata and binary files.
  - Blocked `delivery` role with HTTP 403 Forbidden.
- **Verification**: `tests/test_auth_rbac.py::test_prescription_privacy_delivery_rejected` and `tests/test_edge_cases_and_security.py::test_prescription_privacy_and_unauthorized_access` passed.

---

### DEF-06: Order Modal Title Collision with Inventory Stock Modal
- **Severity**: Medium
- **Component**: `app/static/js/customer.js`
- **Symptom**: Opening an order details modal in the Customer Portal displayed the text "Edit Medicine Inventory" instead of "Order Details — #ORD-...".
- **Root Cause**: The modal header `#order-detail-title` was shared between multiple dynamic templates and retained text from previous administrative dialogs if not explicitly overwritten.
- **Resolution**:
  - Explicitly injected `#order-detail-title.textContent = 'Order Details — #' + ord.order_number` on modal open.
- **Verification**: Tested in Browser Stage 8; invoice modal properly displays formatted order number.

---

### DEF-07: Delivery Geolocation Failure Under Denied Permissions
- **Severity**: Medium
- **Component**: `app/static/js/delivery.js`
- **Symptom**: If a delivery partner denied browser GPS permissions, attempting to mark an order as `IN_TRANSIT` threw an unhandled Promise rejection and halted the delivery flow.
- **Root Cause**: `navigator.geolocation.getCurrentPosition` had no fallback error handler, and the transit transition endpoint required lat/lon coordinates.
- **Resolution**:
  - Implemented graceful geolocation fallback: if browser GPS is denied, falls back to the pharmacy store's seeded coordinates (`12.9716, 77.6412`) with a subtle notification to the rider.
- **Verification**: Live cross-portal verification script (`tests/verify_live_cross_portal.py`) passes transit progression.

---

### DEF-08: Delivery Claim Concurrency Race Condition
- **Severity**: High
- **Component**: `app/routes/delivery_routes.py`, `app/services/order_service.py`
- **Symptom**: If two delivery drivers clicked "Claim Delivery" on the same order within milliseconds, both received confirmation and the order had ambiguous assignment.
- **Root Cause**: The claim endpoint checked order status in one query and updated it in a separate statement without row-level locking or atomic conditions.
- **Resolution**:
  - Implemented atomic conditional update:
    ```sql
    UPDATE orders 
    SET delivery_user_id = ?, status = 'DELIVERY_ASSIGNED', updated_at = CURRENT_TIMESTAMP
    WHERE id = ? AND delivery_user_id IS NULL AND status = 'READY_FOR_PICKUP'
    ```
  - If `rowcount == 0`, immediately return `HTTP 409 Conflict: Order has already been claimed by another delivery partner`.
- **Verification**: `tests/test_api_orders.py::test_delivery_claim_concurrency` passed.

---

### DEF-09: Sticky Header Scroll Occlusion on Interactive Cards
- **Severity**: High
- **Component**: `app/static/css/main.css`
- **Symptom**: Clicking on medicine cards after scrolling down the page failed because the sticky top navigation header (~110px height) covered the card, intercepting pointer events.
- **Root Cause**: Target elements scrolled to `top: 0` without accounting for the sticky navbar height.
- **Resolution**:
  - Added `html { scroll-behavior: smooth; scroll-padding-top: 130px; }` to `app/static/css/main.css`.
- **Verification**: Browser Stage 5 click events successfully reach card buttons when scrolling through catalogue.

---

### DEF-10: CSS Medicine Card Action Buttons Horizontal Overflow
- **Severity**: High
- **Component**: `app/static/css/main.css`
- **Symptom**: The "Add to Cart" and "Alternatives" buttons inside `.medicine-card` overflowed horizontally by 91px outside the right border of the card (342px width in a 251px card container). The overflow hung into the adjacent card in the grid, causing clicks on the right card to be intercepted by the left card's invisible overflow.
- **Root Cause**: `.card-bottom` was set to `display: flex; flex-direction: row; justify-content: space-between; align-items: center` with `white-space: nowrap` and fixed min-widths on buttons.
- **Resolution**:
  - Refactored `.card-bottom` to `flex-direction: column; align-items: stretch; gap: 8px`.
  - Configured `.card-actions` as a full-width flex container (`width: 100%`) with flex buttons:
    ```css
    .card-actions .btn-alt-pill,
    .card-actions .btn-add-cart {
      flex: 1 1 50%;
      min-width: 0;
      white-space: nowrap;
      text-align: center;
    }
    ```
- **Verification**: Chromium Playwright automated click on `.btn-add-cart` in Stage 5 executed without pointer interception errors.

---

### DEF-11: Administrator Account Self-Lockout Risk
- **Severity**: Critical
- **Component**: `app/routes/admin_routes.py`
- **Symptom**: An administrator could deactivate admin accounts via the user governance endpoint `PUT /api/admin/users/<id>/status`, creating an irreversible platform lockout where no active admin exists.
- **Root Cause**: The status toggle endpoint checked only that the caller was an admin, but did not check if the target user was also an admin.
- **Resolution**:
  - Added guard in `toggle_user_status()`:
    ```python
    target_user = query_db("SELECT id, role FROM users WHERE id = ?", (user_id,), one=True)
    if not target_user:
        return jsonify({"error": "User not found"}), 404
    if target_user["role"] == "admin" and not is_active:
        return jsonify({"error": "Administrator accounts cannot be deactivated to prevent system lockout"}), 400
    ```
- **Verification**: `tests/test_edge_cases_and_security.py::test_admin_lockout_protection` passed.

---

### DEF-12: Order State Machine Invalidation & Illegal State Bypasses
- **Severity**: Critical
- **Component**: `app/services/order_service.py`
- **Symptom**: Malformed requests could bypass fulfillment steps (e.g. transitioning directly from `PLACED` to `DELIVERED`, or customer marking an order `ACCEPTED`).
- **Root Cause**: Transitions were verified inconsistently across route blueprints.
- **Resolution**:
  - Centralized transition validation inside `OrderStateMachine.validate_transition(current, target, role)`.
  - Disallowed transitions from terminal states (`DELIVERED`, `CANCELLED`).
  - Restricted state mutation permissions strictly to authorized roles (`pharmacy` for `ACCEPTED`/`PREPARING`/`READY_FOR_PICKUP`; `delivery` for `DELIVERY_ASSIGNED`/`PICKED_UP`/`IN_TRANSIT`/`DELIVERED`).
- **Verification**: `tests/test_state_machine.py` and `tests/test_edge_cases_and_security.py::test_order_state_machine_illegal_transitions` passed.

---

### DEF-13: Concurrent Checkout Overselling in Inventory Service
- **Severity**: Critical
- **Component**: `app/services/inventory_service.py`
- **Symptom**: High-concurrency orders for the last remaining stock unit could oversell inventory into negative stock.
- **Root Cause**: Stock check and decrement were executed in two disjoint statements without an atomic `WHERE quantity >= ?` condition.
- **Resolution**:
  - Implemented atomic conditional decrement in SQLite:
    ```sql
    UPDATE pharmacy_inventory 
    SET quantity = quantity - ?, updated_at = CURRENT_TIMESTAMP 
    WHERE pharmacy_id = ? AND medicine_id = ? AND quantity >= ?
    ```
  - If `cursor.rowcount == 0`, transaction raises `ValueError("Insufficient stock available")`.
- **Verification**: `tests/test_inventory.py::test_overselling_raises_value_error` passed.

---

### DEF-14: Missing Explicit Sildenafil + Nitroglycerin Contraindication Rule
- **Severity**: High (Clinical Safety)
- **Component**: `app/data/ddi_rules.json`
- **Symptom**: While `Sildenafil + Isosorbide Dinitrate` was catalogued, the primary cardiovascular nitrate `Nitroglycerin` (Nitrocontin) was not flagged as contraindicated when paired with PDE5 inhibitors.
- **Root Cause**: The JSON clinical ruleset lacked an explicit pairing entry for `["Sildenafil", "Nitroglycerin"]`.
- **Resolution**:
  - Added rule `["Sildenafil", "Nitroglycerin"]` with `CONTRAINDICATED` severity and severe hypotension clinical alert to `app/data/ddi_rules.json`.
- **Verification**: `tests/test_edge_cases_and_security.py::test_drug_drug_interaction_screening` passed.

---

### DEF-15: Cross-Pharmacy Cart Conflict & Multi-Vendor Fragmentation
- **Severity**: High
- **Component**: `app/routes/cart_routes.py`
- **Symptom**: A customer could add medicine A from Pharmacy 1 and medicine B from Pharmacy 2 to the same cart. At checkout, single-pharmacy order processing could not fulfill the multi-store order.
- **Root Cause**: The cart table lacked a pharmacy binding check upon insertion.
- **Resolution**:
  - Updated `add_cart_item()` in `cart_routes.py` to inspect the pharmacy of existing items in the user's active cart.
  - If incoming item is from a different pharmacy, the server returns `HTTP 409 Conflict` with a structured payload: `{"error": "Cart contains items from another pharmacy", "current_pharmacy_id": ...}` prompting the user to either switch pharmacy or clear cart.
- **Verification**: `tests/test_auth_rbac.py::test_cross_pharmacy_cart_conflict_resolution` passed.

---

### DEF-16: Prescription Verification Order Auto-Transition & Deadlock
- **Severity**: Critical (Fulfillment Blocker)
- **Component**: `app/routes/prescription_routes.py`, `app/static/js/pharmacy.js`
- **Symptom**: Orders placed for Rx medications remained permanently in `AWAITING_PRESCRIPTION` after pharmacist verified the prescription document. Pharmacist attempting to accept order received HTTP 400 "Invalid transition from AWAITING_PRESCRIPTION to ACCEPTED". In the frontend, "Accept Order" was only rendered for `PLACED` status, leaving verified orders completely stuck.
- **Root Cause**: `prescription_routes.py::verify_prescription` only updated the `prescriptions` table without transitioning linked orders. `pharmacy.js` lacked support for `PRESCRIPTION_VERIFIED` orders.
- **Resolution**:
  - Added automatic transition of linked orders from `AWAITING_PRESCRIPTION` to `PRESCRIPTION_VERIFIED` via `OrderService.transition_order_status` in `verify_prescription`.
  - Updated `pharmacy.js` to render "Accept Order" for both `PLACED` and `PRESCRIPTION_VERIFIED` orders.
  - Added quick action button in pharmacy order queue to inspect unverified prescriptions.
- **Verification**: `tests/test_edge_cases_and_security.py::test_prescription_lifecycle_order_sync_and_rejection_restores_stock` and `tests/verify_live_cross_portal.py` Stage 14 passed.

---

### DEF-17: Prescription Rejection Inventory Leak & Order Abandonment
- **Severity**: High (Data Integrity & Inventory Accounting)
- **Component**: `app/routes/prescription_routes.py`
- **Symptom**: If pharmacist rejected an invalid prescription, linked orders remained in `AWAITING_PRESCRIPTION` and reserved medicine stock was never restored to pharmacy inventory.
- **Root Cause**: `verify_prescription` did not cancel linked orders or invoke `InventoryService.restore_stock()`.
- **Resolution**:
  - Updated `verify_prescription` upon `decision == "rejected"` to automatically transition linked orders to `CANCELLED` via `OrderService.transition_order_status`, triggering atomic inventory stock restoration and payment refunding.
- **Verification**: `tests/test_edge_cases_and_security.py::test_prescription_lifecycle_order_sync_and_rejection_restores_stock` verified full stock restoration.

---

### DEF-18: Rejected Prescription Reuse Security Gate Bypass
- **Severity**: High (Clinical Regulatory Compliance)
- **Component**: `app/services/order_service.py`
- **Symptom**: A patient could attach an already rejected prescription ID to repeatedly place new orders.
- **Root Cause**: `OrderService.create_order` checked `if not rx_check` but failed to verify `if rx_check["status"] == "rejected"`.
- **Resolution**:
  - Added check in `create_order`: if `rx_check["status"] == "rejected"`, raises `ValueError("Attached prescription #... has been rejected and cannot be used for orders.")`.
- **Verification**: `tests/test_edge_cases_and_security.py::test_prescription_lifecycle_order_sync_and_rejection_restores_stock` step 5 verified HTTP 400 rejection.

---

### DEF-19: Missing Inventory Delete Endpoint & Foreign Key Crash on Invalid Medicine
- **Severity**: Medium
- **Component**: `app/routes/pharmacy_routes.py`, `app/services/inventory_service.py`
- **Symptom**: Calling `DELETE /api/pharmacy/inventory/<id>` returned HTTP 405 Method Not Allowed. Calling `POST /api/pharmacy/inventory` with a nonexistent medicine ID caused an unhandled `sqlite3.IntegrityError` resulting in an HTTP 500 crash.
- **Root Cause**: `pharmacy_routes.py` lacked a DELETE endpoint, and `add_inventory_item` did not validate that `medicine_id` existed in catalogue before inserting.
- **Resolution**:
  - Implemented `InventoryService.delete_stock()` and `@pharmacy_bp.route("/inventory/<int:medicine_id>", methods=["DELETE"])`.
  - Added medicine existence check returning HTTP 404 for invalid catalogue IDs.
- **Verification**: `tests/test_edge_cases_and_security.py::test_pharmacy_inventory_crud_and_validation` and `tests/verify_live_cross_portal.py` Stage 15 passed.

---

### DEF-20: Pharmacy Portal UI Missing "Stock New Medicine" and "Remove from Inventory" Controls
- **Severity**: Medium (Portal Completeness)
- **Component**: `app/static/js/pharmacy.js`, `app/static/js/api.js`
- **Symptom**: Pharmacists had no UI button or dialog to stock new catalogue items or remove discontinued items from their pharmacy.
- **Root Cause**: `pharmacy.js` only provided an "Edit Stock" button without add or delete modal workflows. `api.js` lacked `deleteInventory` method.
- **Resolution**:
  - Added `API.pharmacy.deleteInventory` in `api.js`.
  - Added "+ Stock New Medicine" button with search autocomplete dialog (`openAddStockModal`) in `pharmacy.js`.
  - Added "Remove" button with confirmation prompt (`handleDeleteStock`) in `pharmacy.js`.
- **Verification**: Verified in real Chromium browser and live HTTP integration tests.

---

### DEF-21: Courier Capacity Enforcement & Delivery Hoarding Prevention
- **Severity**: Medium (Operational Reliability)
- **Component**: `app/routes/delivery_routes.py`
- **Symptom**: Delivery couriers could claim an unlimited number of orders from `/api/delivery/available`, while the active view only displayed the most recent order (`LIMIT 1`), orphaning previous claimed orders.
- **Root Cause**: `claim_delivery` lacked a cap check on active deliveries assigned to a driver.
- **Resolution**:
  - Added batch capacity guard in `claim_delivery` allowing up to 5 concurrent active orders for courier route batching, rejecting subsequent claims with HTTP 409 Conflict.
- **Verification**: `tests/test_edge_cases_and_security.py::test_delivery_driver_hoarding_prevention` passed.

---

### DEF-22: Zero-Byte Prescription Upload Accepted
- **Severity**: Low / Robustness
- **Component**: `app/routes/prescription_routes.py`
- **Symptom**: Uploading a 0-byte file (e.g. `empty.pdf`) succeeded (HTTP 201) and stored empty records in the database.
- **Root Cause**: `upload_prescription` did not validate `file_size > 0`.
- **Resolution**:
  - Added `if file_size == 0:` guard removing the empty file and returning HTTP 400.
- **Verification**: `tests/test_edge_cases_and_security.py::test_empty_prescription_file_rejected` passed.

---

### DEF-23: Admin Update Pharmacy Status 200 Masking Nonexistent ID
- **Severity**: Low / Robustness
- **Component**: `app/routes/admin_routes.py`
- **Symptom**: `PUT /api/admin/pharmacies/<nonexistent_id>/status` returned HTTP 200 Success even when 0 rows were updated.
- **Root Cause**: `update_pharmacy_status` did not verify `cur.rowcount > 0`.
- **Resolution**:
  - Added check: if `cur.rowcount == 0: return jsonify({"error": "Pharmacy not found."}), 404`.
- **Verification**: `tests/test_edge_cases_and_security.py::test_admin_update_nonexistent_pharmacy_404` passed.
