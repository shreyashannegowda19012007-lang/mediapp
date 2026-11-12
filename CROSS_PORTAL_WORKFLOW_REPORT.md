# MediApp Cross-Portal Workflow & State Machine Verification Report

**Audit Date**: November 12, 2026  
**Status**: Fully Verified Across All 4 Portals  
**Authoritative Backend**: Flask 3.1.2 Application Factory  
**Database**: SQLite 3 (WAL Mode, `PRAGMA foreign_keys = ON`)  

---

## 1. Architectural Blueprint of Interconnected Portals

MediApp does not operate as four disjoint applications. It is engineered as a unified single-backend platform connecting four user roles:
1. **Customer** (`role: customer`)
2. **Pharmacy Staff** (`role: pharmacy`)
3. **Delivery Partner** (`role: delivery`)
4. **Administrator** (`role: admin`)

### 1.1 Single Source of Truth
- Every order is identified by a single authoritative, human-readable order number: `ORD-YYYYMMDD-XXXX` (e.g. `ORD-20261112-D452`).
- The database schema enforces referential integrity across 17 relational tables, preventing orphaned order items, disjoint payments, or duplicate assignments.
- SQLite operates in Write-Ahead Logging (`WAL`) mode, allowing non-blocking concurrent reads while transactions write to the WAL ring buffer.

### 1.2 Authoritative Order State Machine

```
              ┌─────────────────────────────────────────────────────────────────────────────┐
              │                                                                             │
   (OTC)      ▼                                                                             │
 [  PLACED  ] ──────────────────────────(Customer cancels / Pharmacy rejects)──────► [ CANCELLED ]
      │                                                                               (Terminal)
      │ (Pharmacy accepts)                                                              ▲   ▲
      ▼                                                                                 │   │
 [ ACCEPTED ] ◄─────────────────────────────────────────────┐                           │   │
      │                                                     │ (Pharmacy accepts)        │   │
      │ (Pharmacy prepares items)                           │                           │   │
      ▼                                            [ PRESCRIPTION_VERIFIED ]            │   │
 [ PREPARING ]                                              ▲                           │   │
      │                                                     │ (Pharmacist approves Rx)  │   │
      │ (Pharmacy packages items)                           │                           │   │
      ▼                                            [ AWAITING_PRESCRIPTION ] ───────────┘   │
 [ READY_FOR_PICKUP ]                                       ▲   (Pharmacist rejects Rx)     │
      │                                                     │                               │
      │ (Delivery driver claims order)             (Rx Item)│                               │
      ▼                                                     │                               │
 [ DELIVERY_ASSIGNED ]                                      │                               │
      │                                            [  Order Placement with Rx  ]            │
      │ (Delivery driver arrives at pharmacy)                                               │
      ▼                                                                                     │
 [ PICKED_UP ]                                                                              │
      │                                                                                     │
      │ (Delivery driver departs for delivery)                                              │
      ▼                                                                                     │
 [ IN_TRANSIT ] ──────────────────────(Customer / System Cancellation)──────────────────────┘
      │
      │ (Customer handover & confirmation)
      ▼
 [ DELIVERED ]
  (Terminal)
```

---

## 2. Exhaustive Cross-Portal Workflow Verifications

### 2.1 Workflow 1: Successful Medicine Order Lifecycle

**Objective**: Verify seamless propagation of an order through all four portals from creation to delivery and admin audit.

1. **Step 1: Customer Order Placement**
   - **Portal**: Customer Portal (`customer@mediapp.local`)
   - **Action**: Customer adds 2 units of `Calpol 500mg Tablet` (ID: 3) from Apollo Indiranagar (Pharmacy 1) to cart.
   - **Checkout**: Subtotal: ₹44.00, Tax (5%): ₹2.20, Delivery Fee: ₹30.00. Total: ₹76.20.
   - **Payment**: Demo payment processed and cryptographic verification record created in `payments` table.
   - **State**: Order created with ID `ORD-20261112-D452` in status `PLACED`.

2. **Step 2: Pharmacy Fulfillment & Preparation**
   - **Portal**: Pharmacy Portal (`demo.pharmacy@mediapp.local`)
   - **Action**: Pharmacy staff observes incoming order in real-time orders queue.
   - **Stock Deduction**: Upon clicking "Accept Order", `inventory_service.py` executes an atomic SQLite update:
     `UPDATE pharmacy_inventory SET quantity = quantity - 2 WHERE pharmacy_id = 1 AND medicine_id = 3 AND quantity >= 2`.
   - **Transitions**:
     - Pharmacy transitions order to `ACCEPTED`.
     - Pharmacy transitions order to `PREPARING`.
     - Pharmacy packages items and transitions order to `READY_FOR_PICKUP`.

3. **Step 3: Delivery Pickup & Transit Progression**
   - **Portal**: Delivery Portal (`demo.delivery@mediapp.local`)
   - **Action**: Driver navigates to "Available Deliveries" pool.
   - **Claim**: Driver claims `ORD-20261112-D452`. Order atomically updates to `DELIVERY_ASSIGNED` with `delivery_user_id` bound to driver.
   - **Pickup**: Driver arrives at pharmacy and confirms receipt: status moves to `PICKED_UP`.
   - **Transit**: Driver starts delivery run: status moves to `IN_TRANSIT`. GPS coordinates are broadcasted to order tracking history.

4. **Step 4: Doorstep Handover & Customer Confirmation**
   - **Portal**: Delivery Portal → Customer Portal
   - **Action**: Driver completes delivery at customer address: status transitions to `DELIVERED`.
   - **Verification in Customer Portal**:
     - Customer tracking screen immediately reflects `DELIVERED` status with timestamped timeline.
     - "Download Receipt" and "Reorder" options become active.

5. **Step 5: Executive Financial Audit**
   - **Portal**: Admin Portal (`demo.admin@mediapp.local`)
   - **Action**: Admin inspects Platform Intelligence dashboard.
   - **Verification**: Total delivered orders count increments by 1; gross platform GMV increases by exactly ₹76.20.

---

### 2.2 Workflow 2: Order Rejection & Atomic Stock Restoration

**Objective**: Verify that when an order is cancelled or rejected, inventory is automatically restored and the customer is notified.

1. Customer places order for 1 unit of `Augmentin 625 Duo Tablet`.
2. Initial stock at Pharmacy 1: 50 units → Decremented to 49 units on order placement.
3. Pharmacy staff reviews order and determines prescription mismatch or local stock damage.
4. Pharmacy clicks "Reject Order" with reason: `"Damaged blister pack / stock unavailable"`.
5. Order transitions to `CANCELLED`.
6. SQLite trigger / `restore_inventory()` executes:
   `UPDATE pharmacy_inventory SET quantity = quantity + 1 WHERE pharmacy_id = 1 AND medicine_id = target_id`.
7. Stock restored to 50 units.
8. Customer receives `CANCELLED` status with pharmacist rejection notes.
9. Verification: Customer attempting to submit payment against cancelled order receives `HTTP 400 Bad Request: Cannot pay for a cancelled order`.

---

### 2.3 Workflow 3: Prescription Upload, OCR, Dispensing Control & Rejection Recovery

**Objective**: Ensure restricted medicines (Schedule H/H1) cannot be dispensed without verified prescription, verify state auto-transitions upon pharmacist review, and verify stock restoration upon prescription rejection.

1. **Upload & Ingestion**:
   - Customer uploads digital prescription via Customer Portal.
   - Server validates file payload; empty 0-byte uploads are rejected with `HTTP 400 Bad Request` (DEF-22).
   - `ocr_service.py` evaluates file MIME type and size (capped at 10 MB).
   - Digital entity extraction parses Doctor name, Patient name, and prescribed drugs.
   - Prescription record saved with status `pending`.

2. **Order Placement for Restricted Medicine**:
   - Customer selects a Schedule H/H1 medicine (e.g., `Voveran SR 100mg Tablet`, `prescription_required = 1`).
   - Checkout requires `prescription_id`. Order is placed with initial status `AWAITING_PRESCRIPTION`.
   - Inventory is reserved at the pharmacy store.

3. **Pharmacist Verification (Approval Flow)**:
   - Pharmacist logs in and opens "Prescription Verification" queue (`/api/prescriptions/pending`).
   - Pharmacist reviews the document and approves: `POST /api/prescriptions/<id>/verify` with `{"decision": "verified"}`.
   - Server verifies the document and **automatically transitions** linked orders from `AWAITING_PRESCRIPTION` to `PRESCRIPTION_VERIFIED` (DEF-16).
   - In Pharmacy Portal dashboard queue, the order renders the "Accept Order" action button.
   - Pharmacist accepts the order (`ACCEPTED`), moving it into `PREPARING` → `READY_FOR_PICKUP`.

4. **Pharmacist Rejection & Stock Restoration Flow**:
   - In the event of an invalid or fraudulent prescription, pharmacist rejects: `{"decision": "rejected", "notes": "Unreadable doctor stamp"}`.
   - Server marks prescription `rejected` and **automatically cancels** linked orders (`CANCELLED`), triggering atomic inventory restoration back to the pharmacy shelf (DEF-17).
   - Customer tracking reflects cancellation with rejection reason.
   - Attempting to reuse this rejected prescription ID in subsequent checkouts is rejected with `HTTP 400 Bad Request: Attached prescription has been rejected` (DEF-18).

5. **Privacy Enclosure**:
   - Delivery driver attempting to query `/api/prescriptions/<id>` is rejected with `HTTP 403 Forbidden` (DEF-05).
   - Unauthorized customer attempting to access foreign prescription ID is rejected with `HTTP 403 Forbidden`.

---

### 2.4 Workflow 4: Concurrent Delivery Claim Race Condition

**Objective**: Ensure that two delivery drivers clicking "Claim" simultaneously cannot double-claim the same order, and drivers cannot hoard unlimited active orders.

1. Order `ORD-TEST-CLAIM` is in state `READY_FOR_PICKUP`.
2. Driver A (`user_id = 4`) and Driver B (`user_id = 5`) both view the order in their available pool.
3. Driver A and Driver B fire claim requests simultaneously.
4. Server executes:
   ```sql
   UPDATE orders 
   SET delivery_user_id = 4, status = 'DELIVERY_ASSIGNED', updated_at = CURRENT_TIMESTAMP
   WHERE id = 99 AND delivery_user_id IS NULL AND status = 'READY_FOR_PICKUP';
   ```
5. Driver A's request matches 1 row and succeeds (`HTTP 200`).
6. Driver B's request matches 0 rows (condition `delivery_user_id IS NULL` is false) and immediately fails with `HTTP 409 Conflict`.
7. Driver B receives toast: *"This order was just claimed by another delivery partner."*
8. **Courier Capacity Enforcement**: Driver A can batch up to 5 concurrent active orders for efficient dispatch routing. If Driver A attempts to claim a 6th concurrent order, the request is rejected with `HTTP 409 Conflict: Active delivery capacity reached (max 5 active orders)` (DEF-21).

---

### 2.5 Workflow 5: Pharmacy Inventory Addition & Deletion Lifecycle

**Objective**: Verify complete inventory CRUD lifecycle between Pharmacy management and Customer storefront discovery.

1. **Stock New Catalogue Medicine**:
   - Pharmacist clicks "+ Stock New Medicine" on Pharmacy Inventory screen (DEF-20).
   - Modal allows debounced searching against master 1,250 medicine catalogue.
   - Pharmacist selects medicine, inputs quantity (e.g. 100), unit price (₹45.00), batch number (`BAT-2026-X1`), and expiry date (`2028-12-31`).
   - Server validates medicine exists in catalogue (`POST /api/pharmacy/inventory`, DEF-19) and inserts record.
   - Item immediately becomes discoverable in Customer search and purchasable.

2. **Remove Discontinued Medicine**:
   - Pharmacist clicks "Remove" on an inventory row.
   - Confirmation modal prompts pharmacist (`DELETE /api/pharmacy/inventory/<medicine_id>`, DEF-19).
   - Inventory record is deleted.
   - Customer catalogue immediately reflects out-of-stock status; attempting to add to cart returns stock unavailable error.

---

## 3. Financial & Decimal Precision Audit

To prevent rounding accumulation errors and floating-point inaccuracies, all financial calculations are processed via Python's `Decimal` module with explicit `ROUND_HALF_UP` quantization:

$$ \text{Total} = \text{Quantize}\Big(\sum (\text{unit\_price} \times \text{qty}) \times (1 - \text{discount}) \times (1 + \text{tax\_rate}) + \text{delivery\_fee}\Big) $$

| Component | Customer View | Pharmacy View | Delivery View | Admin Ledger | Discrepancy |
|---|---|---|---|---|---|
| **Subtotal** | ₹44.00 | ₹44.00 | — | ₹44.00 | ₹0.00 |
| **Tax (5%)** | ₹2.20 | ₹2.20 | — | ₹2.20 | ₹0.00 |
| **Delivery Fee** | ₹30.00 | — | ₹30.00 | ₹30.00 | ₹0.00 |
| **Gross Total** | ₹76.20 | ₹46.20 (net items) | ₹30.00 (payout) | ₹76.20 | ₹0.00 |

Across all automated tests and live transactions, zero floating point drift was detected. Every monetary amount in SQLite is stored as exact real numbers quantized to 2 decimal places.

---

## 4. Frontend State Synchronization & Polling Strategy

- **Module**: `app/static/js/sync.js`
- **Visibility-Aware Polling**:
  - When the browser tab is focused (`document.visibilityState === 'visible'`), polling occurs at 5-second intervals.
  - When the browser tab is hidden or minimized, polling slows to 30-second intervals to minimize battery and CPU consumption.
- **Event-Driven Cache Purge**:
  - Role transitions trigger `clearPortalState()`, preventing stale data from bleeding across different user personas on the same workstation.
