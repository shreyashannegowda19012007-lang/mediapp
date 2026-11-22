# MediApp Comprehensive Defect Survey & Audit Report

**Target Project**: `d:\MediApp`  
**Application**: MediApp Healthcare Network (Next.js / TypeScript Frontend & Flask REST API Backend)  
**Report File**: `DEFECTS.md`  
**Audit Mode**: Non-Destructive Defect Discovery & Cataloging (Zero Source Code Modifications)  
**Total Defects Identified**: 29 Verified Defects  

---

## Executive Summary

A comprehensive defect audit of the MediApp healthcare web platform was conducted across the full software stack. The audit evaluated build and compilation pipelines, backend REST APIs and database queries, role-based access control (RBAC) and security invariants, frontend state machines and workflows, dark/light clinical theming and responsive layouts, clinical design guidelines (`AGENTS.md`), and WAI-ARIA / WCAG 2.1 AA accessibility standards.

All identified defects are cataloged below without modifying any source files, adhering strictly to the non-destructive audit mandate.

### Defect Inventory by Category

| Category | Description | Count | Severity Breakdown |
|---|---|:---:|---|
| **Category 1** | Build, Compilation & Type Defects | 2 | 1 High, 1 Medium |
| **Category 2** | Backend API & Runtime Exception Defects | 5 | 1 Critical, 2 High, 2 Medium |
| **Category 3** | Security & Role-Based Access Control (RBAC) Defects | 4 | 2 Critical, 2 High |
| **Category 4** | Frontend State Machine & Functional Workflow Defects | 5 | 4 Medium, 1 Low |
| **Category 5** | Visual, Theming & Clinical Layout Defects | 4 | 2 High, 1 Medium, 1 Low |
| **Category 6** | Clinical Design System & AGENTS.md Invariant Violations | 5 | 1 High, 3 Medium, 1 Low |
| **Category 7** | Accessibility (WCAG 2.1 AA & WAI-ARIA) Defects | 4 | 1 High, 2 Medium, 1 Low |
| **Total** | **Comprehensive Defect Register** | **29** | **3 Critical, 9 High, 13 Medium, 4 Low** |

---

## Category 1: Build, Compilation & Type Defects

### DEF-01: Missing Frontend `node_modules` Preventing Next.js Compilation and ESLint Execution
- **Defect ID & Title**: DEF-01: Missing Frontend `node_modules` Preventing Next.js Compilation and ESLint Execution
- **Description**: The workspace root `package.json` delegates build and linting commands to the Next.js frontend via `"build": "npm run build --prefix frontend"` and `"lint": "npm run lint --prefix frontend"`. However, `d:\MediApp\frontend\node_modules` is not populated on disk. Running `npm run build` or `npm run lint` fails immediately with exit code 1 because the Next.js and ESLint binary executables cannot be resolved.
- **Reproduction Steps**:
  1. Open a terminal prompt at the repository root `d:\MediApp`.
  2. Execute `npm run build`.
  3. Execute `npm run lint`.
  4. Observe the failure messages indicating `'next'` and `'eslint'` are unrecognized.
- **Expected Behavior**: The commands `npm run build` and `npm run lint` execute successfully, compiling the Next.js application into `.next` and passing ESLint verification without terminal process termination.
- **Actual Behavior**: The process terminates with exit code 1:
  `'next' is not recognized as an internal or external command, operable program or batch file.`
  `'eslint' is not recognized as an internal or external command, operable program or batch file.`
- **Severity**: High
- **Affected Component or File**: `d:\MediApp\package.json:8,10`, `d:\MediApp\frontend\package.json:6-9`

---

### DEF-02: TypeScript Data Contract Mismatch on Cold-Chain Schema
- **Defect ID & Title**: DEF-02: TypeScript Data Contract Mismatch on Cold-Chain Schema
- **Description**: In `frontend/src/lib/api.ts`, the core `Medicine` interface defines an optional property `cold_chain?: boolean`. However, the backend database schema in `mediapp.db` lacks any `cold_chain` or `requires_cold_chain` column, while backend routes attempt to filter using `m.requires_cold_chain = 1`. This creates a structural type disconnect where frontend components assume `cold_chain` exists on API responses, while the backend API returns neither `cold_chain` nor `requires_cold_chain`.
- **Reproduction Steps**:
  1. Inspect the `Medicine` interface in `d:\MediApp\frontend\src\lib\api.ts:6-23`.
  2. Inspect the SQLite schema columns via `PRAGMA table_info(medicines)` in `mediapp.db`.
  3. Inspect `d:\MediApp\app\routes\medicine_routes.py:49-51` where `m.requires_cold_chain` is queried.
- **Expected Behavior**: TypeScript interfaces should accurately mirror authoritative backend API response contracts, and database columns should match the properties exposed and queried by both layers.
- **Actual Behavior**: Frontend code relies on `cold_chain?: boolean` or hardcoded substring heuristics because the database schema and API responses do not supply the typed attribute.
- **Severity**: Medium
- **Affected Component or File**: `d:\MediApp\frontend\src\lib\api.ts:22`, `d:\MediApp\app\routes\medicine_routes.py:49-51`

---

## Category 2: Backend API & Runtime Exception Defects

### DEF-03: Unhandled `sqlite3.OperationalError` (HTTP 500) on Cold-Chain Monitored Filter Query
- **Defect ID & Title**: DEF-03: Unhandled `sqlite3.OperationalError` (HTTP 500) on Cold-Chain Monitored Filter Query
- **Description**: In `app/routes/medicine_routes.py`, when a user filters for cold-chain medicines (`?cold_chain=1`), the route appends `conditions.append("m.requires_cold_chain = 1")`. However, the `medicines` table in `mediapp.db` contains only columns `[id, name, generic_name, strength, dosage_form, category, manufacturer, mrp, prescription_required, pack_size, uses, side_effects, created_at]`. Column `requires_cold_chain` does not exist, causing SQLite to raise an uncaught `sqlite3.OperationalError: no such column: m.requires_cold_chain`, crashing the request with HTTP 500 Internal Server Error and rendering a blank catalogue grid in the UI.
- **Reproduction Steps**:
  1. Start the Flask application or instantiate the test client.
  2. Send a `GET` request to `/api/medicines?cold_chain=1&page=1&limit=24`.
  3. Inspect the response status code and error trace.
- **Expected Behavior**: The API should execute without database exceptions and return medicines categorized under temperature-sensitive biologics, vaccines, or insulins with HTTP 200 OK.
- **Actual Behavior**: The request crashes with HTTP 500 and verbatim error:
  `sqlite3.OperationalError: no such column: m.requires_cold_chain`
- **Severity**: Critical
- **Affected Component or File**: `d:\MediApp\app\routes\medicine_routes.py:49-51`, `d:\MediApp\frontend\src\components\catalogue\MedicineCatalogue.tsx:28, 146-156`

---

### DEF-04: Unhandled `ValueError` Exception (HTTP 500) on Non-Numeric `rx` Query Parameter
- **Defect ID & Title**: DEF-04: Unhandled `ValueError` Exception (HTTP 500) on Non-Numeric `rx` Query Parameter
- **Description**: In `app/routes/medicine_routes.py`, the `search_medicines` handler extracts the query string parameter `rx = request.args.get("rx")` and directly executes `params.append(int(rx))` without exception handling or type validation. Passing any non-numeric string (e.g. `?rx=invalid`, `?rx=all`, `?rx=true`) triggers an uncaught `ValueError: invalid literal for int() with base 10`, terminating request processing with HTTP 500.
- **Reproduction Steps**:
  1. Send a request to `GET /api/medicines?rx=invalid`.
  2. Inspect the HTTP response status code.
- **Expected Behavior**: The server should sanitize and validate query inputs, returning HTTP 400 Bad Request with a descriptive validation error or gracefully ignoring invalid non-numeric inputs.
- **Actual Behavior**: The server raises an uncaught `ValueError` and responds with HTTP 500 Internal Server Error.
- **Severity**: Medium
- **Affected Component or File**: `d:\MediApp\app\routes\medicine_routes.py:45-47`

---

### DEF-05: Customer Registration Address String Discarded Due to Strict Dictionary Type Check
- **Defect ID & Title**: DEF-05: Customer Registration Address String Discarded Due to Strict Dictionary Type Check
- **Description**: The registration modal in `frontend/src/components/auth/AuthModal.tsx` collects a patient's delivery address in a single text `<input>` and submits the payload as `{ email, password, full_name, phone, address: string }`. However, in `app/services/auth_service.py`, `AuthService.register_customer` inspects the address parameter with `if address and isinstance(address, dict):`. Because a string fails `isinstance(dict)`, the entire address block is bypassed and no entry is inserted into `customer_addresses`, silently discarding the user's input.
- **Reproduction Steps**:
  1. Open the "Sign In / Register" modal and switch to "Create Patient Account".
  2. Fill out all fields, including "Default Delivery Address" (e.g. "Flat 201, Lakeview Apts, Bellandur, Bengaluru").
  3. Submit registration.
  4. Inspect the SQLite database table `customer_addresses` for the newly created `user_id`.
- **Expected Behavior**: The customer's registered address is parsed or adapted and saved into `customer_addresses` as their default delivery location.
- **Actual Behavior**: Zero address records are created in `customer_addresses`; the address string is silently ignored without notice to the user.
- **Severity**: High
- **Affected Component or File**: `d:\MediApp\app\services\auth_service.py:71-84`, `d:\MediApp\frontend\src\components\auth\AuthModal.tsx:19, 49-55`

---

### DEF-06: Available Courier Runs Route Omits Address Deserialization, Causing Static Fallback
- **Defect ID & Title**: DEF-06: Available Courier Runs Route Omits Address Deserialization, Causing Static Fallback
- **Description**: In `app/routes/delivery_routes.py`, `get_available_deliveries()` selects orders via `SELECT o.delivery_address_json ...` and returns `order_list = [dict(o) for o in orders]` without parsing the JSON address or populating a `delivery_address` field. In `frontend/src/components/logistics/DeliveryRunsBoard.tsx`, line 111 renders `{run.delivery_address || "Bengaluru Express Delivery Hub"}`. Because `run.delivery_address` is undefined, every available run card displays the generic fallback string `"Bengaluru Express Delivery Hub"` instead of the customer's actual delivery location.
- **Reproduction Steps**:
  1. Switch active persona to "Delivery Rider" (`delivery`).
  2. Open "Delivery Fleet & Tracking" (`DeliveryRunsBoard.tsx`).
  3. Inspect the address line on all available run cards in the pool.
- **Expected Behavior**: Each available run card displays the parsed delivery destination (e.g. "Flat 402, Green Glen Layout, Bellandur, Bengaluru").
- **Actual Behavior**: Every available run card displays the static placeholder text `"Bengaluru Express Delivery Hub"`.
- **Severity**: Medium
- **Affected Component or File**: `d:\MediApp\app\routes\delivery_routes.py:87-97`, `d:\MediApp\frontend\src\components\logistics\DeliveryRunsBoard.tsx:111`

---

### DEF-07: AI Emergency Triage Alert Text Discarded Due to Response Object Key Mismatch
- **Defect ID & Title**: DEF-07: AI Emergency Triage Alert Text Discarded Due to Response Object Key Mismatch
- **Description**: In `app/services/ai_service.py`, when a user's query triggers emergency red-flag symptoms, `query_assistant` returns `{"is_emergency": True, "response": emergency_warning, "disclaimer": ...}`. However, in `frontend/src/components/clinical/AITriageModal.tsx`, line 147 accesses `{result.emergency_message || "Symptoms indicate potential critical illness..."}`. Because the key is `response` rather than `emergency_message`, the authoritative clinical warning string is discarded, and the UI displays generic fallback text.
- **Reproduction Steps**:
  1. Open the AI Triage Modal in the Navbar.
  2. Enter an emergency symptom description (e.g. "Severe crushing chest pain and shortness of breath").
  3. Submit the query.
  4. Inspect the red Emergency Warning Flag banner rendered in the modal.
- **Expected Behavior**: The banner displays the backend's urgent clinical alert: `"CRITICAL ALERT: Your query mentions potential life-threatening emergency symptoms. Immediately call 112 / 911 / 108..."`.
- **Actual Behavior**: The banner displays the generic fallback: `"Symptoms indicate potential critical illness. Please seek immediate in-person emergency hospital care."`.
- **Severity**: Medium
- **Affected Component or File**: `d:\MediApp\app\services\ai_service.py:93-98`, `d:\MediApp\frontend\src\components\clinical\AITriageModal.tsx:147`

---

## Category 3: Security & Role-Based Access Control (RBAC) Defects

### DEF-08: Plaintext Patient Delivery Handover OTP Leaked to Delivery Couriers in API Responses
- **Defect ID & Title**: DEF-08: Plaintext Patient Delivery Handover OTP Leaked to Delivery Couriers in API Responses
- **Description**: The 6-digit delivery OTP is a confidential security credential generated at order placement to prevent medication diversion and theft. However, in `app/routes/order_routes.py` lines 128-147 and `app/services/order_service.py` line 411, queries execute `SELECT o.*` and serialize `dict(order)` directly into the JSON response for `GET /api/orders` and `GET /api/orders/<id>`. When a delivery rider fetches orders, the patient's private `delivery_otp` is included in plaintext in the response payload.
- **Reproduction Steps**:
  1. Authenticate with a courier account (`role: "delivery"`).
  2. Send a `GET` request to `/api/orders` or `/api/orders/<order_id>`.
  3. Inspect the returned JSON payload.
  4. Check for the presence of the `delivery_otp` key.
- **Expected Behavior**: The `delivery_otp` field must be redacted/stripped from API responses for delivery riders and non-admin external roles; only the customer receiving the medication should possess the OTP.
- **Actual Behavior**: The plaintext 6-digit OTP (e.g. `"583921"`) is returned in the API response to delivery couriers.
- **Severity**: Critical
- **Affected Component or File**: `d:\MediApp\app\routes\order_routes.py:128-147`, `d:\MediApp\app\services\order_service.py:411`

---

### DEF-09: Courier Interface Exposes Secret Patient OTP Alongside Verification Input, Enabling Self-Verification
- **Defect ID & Title**: DEF-09: Courier Interface Exposes Secret Patient OTP Alongside Verification Input, Enabling Self-Verification
- **Description**: In `frontend/src/components/logistics/OrderTrackingTimeline.tsx`, lines 258-278 render the "Patient Handover Security OTP" card displaying `{selectedOrder.delivery_otp}` whenever present, while lines 395-420 render the OTP verification input box on the very same screen. When a delivery courier views an assigned order, they can view the customer's secret OTP on-screen and immediately type it into the verification box, enabling malicious couriers to falsely mark deliveries as complete without ever arriving at the patient's doorstep. This violates the AGENTS.md mandate: "Include patient delivery OTP handoff verification to prevent medication diversion."
- **Reproduction Steps**:
  1. Switch to "Delivery Rider" role.
  2. Navigate to "Delivery Fleet & Tracking" (`OrderTrackingTimeline.tsx`).
  3. Select any in-transit delivery run.
  4. Inspect the right-hand tracking panel.
- **Expected Behavior**: Delivery couriers should only see the input field to enter the code provided verbally by the patient upon doorstep arrival. The plaintext OTP must never be visible to the courier.
- **Actual Behavior**: The secret OTP is displayed prominently on the courier's screen, allowing self-verification and defeating the diversion prevention control.
- **Severity**: Critical
- **Affected Component or File**: `d:\MediApp\frontend\src\components\logistics\OrderTrackingTimeline.tsx:258-278, 395-420`

---

### DEF-10: Customer Handover OTP Verification UI Invokes Courier-Restricted Endpoint Returning HTTP 403 Forbidden
- **Defect ID & Title**: DEF-10: Customer Handover OTP Verification UI Invokes Courier-Restricted Endpoint Returning HTTP 403 Forbidden
- **Description**: In `frontend/src/components/logistics/OrderTrackingTimeline.tsx`, the order tracking panel contains an OTP input field and "Verify OTP" button that executes `handleVerifyOtp()`. This function invokes `api.delivery.verifyHandoff(selectedOrder.id, otpInput)`, which sends a `POST` request to `/api/delivery/orders/<id>/verify-otp`. In `app/routes/delivery_routes.py` lines 263-266, this endpoint is guarded by `@roles_required("delivery", "admin")`. When legitimate customers attempt to use this control, the backend rejects the request with HTTP 403 Forbidden, triggering an unhelpful error popup.
- **Reproduction Steps**:
  1. Log in as a customer persona (`customer`).
  2. Navigate to "My Orders & Tracking".
  3. Enter the delivery OTP in the verification input and click "Verify OTP".
  4. Observe the response and UI alert.
- **Expected Behavior**: Customers should not be prompted to verify the courier's handoff via a courier-restricted API; the customer view should clarify that the code must be shown to the delivery rider.
- **Actual Behavior**: The UI triggers an unauthorized API call returning HTTP 403 Forbidden: `{"error": "Unauthorized role: required delivery, admin"}`.
- **Severity**: High
- **Affected Component or File**: `d:\MediApp\frontend\src\components\logistics\OrderTrackingTimeline.tsx:125-142`, `d:\MediApp\app\routes\delivery_routes.py:263-266`

---

### DEF-11: Unauthenticated Visitors Retained as Logged-In Demo Customer #1 Upon Failed Session Check
- **Defect ID & Title**: DEF-11: Unauthenticated Visitors Retained as Logged-In Demo Customer #1 Upon Failed Session Check
- **Description**: In `frontend/src/store/useAuthStore.ts`, the store initializes state with default demo customer #1 (`{ user_id: 1, email: "customer@mediapp.local", full_name: "Clinical Customer Demo", role: "customer" }`). In `fetchSession()`, when `api.auth.getSession()` responds with `{ authenticated: false }`, the store does not reset `user` to `null`. As a consequence, unauthenticated visitors who clear their cookies or open the site in a private window remain permanently flagged as authenticated user #1 across the frontend.
- **Reproduction Steps**:
  1. Clear all browser cookies and session storage for `localhost:3000`.
  2. Load the web application.
  3. Inspect `useAuthStore.getState().user`.
- **Expected Behavior**: When session verification returns `authenticated: false`, `user` is set to `null` and the UI presents an unauthenticated visitor state.
- **Actual Behavior**: `user` remains populated with user ID 1 and role `"customer"`.
- **Severity**: High
- **Affected Component or File**: `d:\MediApp\frontend\src\store\useAuthStore.ts:21-43`

---

## Category 4: Frontend State Machine & Functional Workflow Defects

### DEF-12: Milestone Tracking Stepper Regresses to Step 0 on Intermediate Order Lifecycle States
- **Defect ID & Title**: DEF-12: Milestone Tracking Stepper Regresses to Step 0 on Intermediate Order Lifecycle States
- **Description**: In `frontend/src/components/logistics/OrderTrackingTimeline.tsx`, the helper function `getStepIndex(status)` handles only a limited subset of lowercase statuses (`placed`, `pending`, `approved`, `verified`, `packed`, `ready_for_pickup`, `out_for_delivery`, `in_transit`, `assigned`, `delivered`, `completed`). Authoritative backend statuses defined in `OrderStateMachine` (`app/services/order_service.py`), including `"AWAITING_PRESCRIPTION"`, `"PRESCRIPTION_VERIFIED"`, `"ACCEPTED"`, `"PREPARING"`, `"DELIVERY_ASSIGNED"`, and `"PICKED_UP"`, fall through to `default: return 0`. This causes the visual milestone progress bar to regress to Stage 0 ("Order Placed") for orders actively being processed or out for delivery.
- **Reproduction Steps**:
  1. Create or inspect an order in status `"PRESCRIPTION_VERIFIED"`, `"PREPARING"`, or `"DELIVERY_ASSIGNED"`.
  2. Open "My Orders & Tracking" in the customer portal.
  3. Inspect the active milestone stepper indicator at the top of the order details card.
- **Expected Behavior**: The milestone stepper reflects the accurate stage of fulfillment (e.g. Step 1 for verified prescription, Step 2 for pharmacy preparation).
- **Actual Behavior**: The stepper indicator regresses to Step 0 ("Order Placed"), confusing patients about their order progress.
- **Severity**: Medium
- **Affected Component or File**: `d:\MediApp\frontend\src\components\logistics\OrderTrackingTimeline.tsx:102-123`

---

### DEF-13: Catalogue Filter Pills Omit Pagination Reset, Triggering False Empty Results
- **Defect ID & Title**: DEF-13: Catalogue Filter Pills Omit Pagination Reset, Triggering False Empty Results
- **Description**: In `frontend/src/components/catalogue/MedicineCatalogue.tsx`, clicking any category pill or attribute filter ("All Items", "OTC Only", "Prescription (Rx)", "Cold-Chain Monitored") updates the respective filter state but fails to call `setPage(1)`. If a user navigates to Page 3 or 4 of the general catalogue and then clicks a category with fewer items (such as "Vaccines" or "Cardiology"), the component requests `page=3` with the new filter, causing the backend to return an empty array and triggering a false "No clinical formulations found" empty state.
- **Reproduction Steps**:
  1. Open the Medicine Catalogue and paginate to Page 3 or 4.
  2. Click on the "Vaccines" category pill or "OTC Only" filter pill.
  3. Inspect the catalogue grid.
- **Expected Behavior**: Selecting any filter or category resets active pagination `page` to 1 and displays matching formulations.
- **Actual Behavior**: The page remains set to 3 or 4, causing 0 results and rendering an empty state message.
- **Severity**: Medium
- **Affected Component or File**: `d:\MediApp\frontend\src\components\catalogue\MedicineCatalogue.tsx:101-157, 165-188`

---

### DEF-14: Inconsistent Pharmacist Review Desk State Transitions Allowing Re-Approval of Cancelled Rx and Rejection of Verified Rx
- **Defect ID & Title**: DEF-14: Inconsistent Pharmacist Review Desk State Transitions Allowing Re-Approval of Cancelled Rx and Rejection of Verified Rx
- **Description**: In `frontend/src/components/clinical/PharmacistReviewDesk.tsx`, the approval button condition is `disabled={isProcessing || selectedRx.status === "verified"}` and the rejection button condition is `disabled={isProcessing || selectedRx.status === "rejected"}`. When a prescription has already been rejected (`status === "rejected"`), the "Certify & Approve Rx" button remains fully enabled. However, rejecting a prescription already permanently cancelled the linked customer order in the backend database (`OrderService.transition_order_status(..., "CANCELLED")`), creating an orphaned, inconsistent state where the prescription is verified but the order remains cancelled. Similarly, an already verified prescription allows pharmacists to click "Reject".
- **Reproduction Steps**:
  1. Switch to "Clinical Pharmacist" role and open the Verification Desk.
  2. Select an already rejected prescription in the audit queue.
  3. Observe that the "Certify & Approve Rx" button is active and clickable.
  4. Click "Certify & Approve Rx".
- **Expected Behavior**: Terminal states ("verified" or "rejected") should disable review action buttons or enforce a strict re-evaluation workflow.
- **Actual Behavior**: Action buttons remain active, permitting conflicting state transitions.
- **Severity**: Medium
- **Affected Component or File**: `d:\MediApp\frontend\src\components\clinical\PharmacistReviewDesk.tsx:390, 400`

---

### DEF-15: Missing Logout Mechanism in Frontend Navigation and Persistent "Sign In" State
- **Defect ID & Title**: DEF-15: Missing Logout Mechanism in Frontend Navigation and Persistent "Sign In" State
- **Description**: In `frontend/src/components/layout/Navbar.tsx`, lines 142-150 permanently render a static "Sign In" button opening `AuthModal`. There is no "Sign Out" or "Log Out" button or user profile menu anywhere in the Next.js frontend interface. Users who log in with real or demo credentials have no UI mechanism to terminate their session or switch accounts without manually opening browser dev tools to delete cookies.
- **Reproduction Steps**:
  1. Log in with customer or administrative credentials.
  2. Inspect the Navbar, mobile drawer, and footer for a logout option.
- **Expected Behavior**: Authenticated users see their profile avatar/name and a "Sign Out" button that clears the session.
- **Actual Behavior**: The Navbar always displays "Sign In", providing no way to log out.
- **Severity**: Medium
- **Affected Component or File**: `d:\MediApp\frontend\src\components\layout\Navbar.tsx:142-150`

---

### DEF-16: Invisible Cart Accumulation for Non-Customer Roles Due to Conditional Drawer Unmounting
- **Defect ID & Title**: DEF-16: Invisible Cart Accumulation for Non-Customer Roles Due to Conditional Drawer Unmounting
- **Description**: In `frontend/src/components/catalogue/MedicineCard.tsx`, the "Add to Cart" button is rendered unconditionally for all users, including pharmacists and system administrators. When clicked, items are successfully dispatched to the session cart in the backend. However, in `frontend/src/app/page.tsx` line 89, `CartDrawer` is mounted only if `currentRoleDef.canAccessCart` (customer role only). Non-customer users can accumulate items invisibly without any drawer opening, cart counter, or access to checkout.
- **Reproduction Steps**:
  1. Switch to "Clinical Pharmacist" or "Operations Administrator" role.
  2. Navigate to the Medicine Catalogue and click "Add to Cart" on multiple medicines.
  3. Look for a cart drawer or confirmation.
- **Expected Behavior**: For non-customer roles, the "Add to Cart" button should be hidden or replaced with "Catalogue Lookup Only", or the cart drawer should clarify customer-only checkout.
- **Actual Behavior**: The button adds items invisibly without drawer access or user feedback.
- **Severity**: Low
- **Affected Component or File**: `d:\MediApp\frontend\src\app\page.tsx:89-91`, `d:\MediApp\frontend\src\components\catalogue\MedicineCard.tsx:155-169`

---

## Category 5: Visual, Theming & Clinical Layout Defects

### DEF-17: Dark Theme Canvas Color Violation: Utility Class `dark:bg-slate-950` Overrides Clinical Token `#070D1A`
- **Defect ID & Title**: DEF-17: Dark Theme Canvas Color Violation: Utility Class `dark:bg-slate-950` Overrides Clinical Token `#070D1A`
- **Description**: `d:\MediApp\AGENTS.md` Section 1 explicitly specifies the authoritative dark theme canvas token: `Dark: Canvas #070D1A, Surface/Cards #0F172A (slate-900), Borders #1E293B (slate-800)`. In `frontend/src/app/globals.css`, `--background: #070d1a;` is correctly declared under `.dark`. However, in `frontend/src/app/layout.tsx` line 18, `<body className="...">` hardcodes `dark:bg-slate-950`. Tailwind's utility class applies `#020617`, directly overriding the clinical trust canvas token on the entire document body.
- **Reproduction Steps**:
  1. Toggle to Dark Mode using the theme switcher.
  2. Open browser developer tools and inspect `document.body`.
  3. Check the computed `background-color`.
- **Expected Behavior**: In Dark Mode, `document.body` background is `#070D1A` as mandated by `AGENTS.md`.
- **Actual Behavior**: The computed background is `#020617` (`slate-950`).
- **Severity**: High
- **Affected Component or File**: `d:\MediApp\frontend\src\app\layout.tsx:18`, `d:\MediApp\frontend\src\app\globals.css:43-44`

---

### DEF-18: Prescription Document Viewport Flex & Overflow Clipping on Magnification/Zoom
- **Defect ID & Title**: DEF-18: Prescription Document Viewport Flex & Overflow Clipping on Magnification/Zoom
- **Description**: In `frontend/src/components/clinical/PharmacistReviewDesk.tsx`, lines 191-201, the document canvas container specifies `className="max-w-full max-h-[500px] flex items-center justify-center shadow-lg rounded-xl overflow-hidden bg-white"` and applies `transform: scale(${zoomLevel})`. Because `overflow-hidden` is placed directly on the transformed container with a rigid 500px maximum height, magnifying the prescription document (up to 250%) causes header details, doctor signatures, and dosage instructions to be clipped off outside the 500px boundary without scrollbars.
- **Reproduction Steps**:
  1. Switch to "Clinical Pharmacist" role and open the Verification Desk.
  2. Select an uploaded prescription document.
  3. Click the zoom button (`+`) repeatedly to zoom to 150% - 250%.
  4. Attempt to scroll to view the clipped top and bottom regions.
- **Expected Behavior**: The magnified document can be panned or scrolled within an auto-overflowing viewport container so pharmacists can audit the entire document.
- **Actual Behavior**: Magnified content extends beyond 500px and is cut off by `overflow-hidden` with no ability to scroll.
- **Severity**: High
- **Affected Component or File**: `d:\MediApp\frontend\src\components\clinical\PharmacistReviewDesk.tsx:191-201`

---

### DEF-19: Critical Navigation Triggers (Sign In and AI Triage) Hidden on Mobile and Omitted from Mobile Drawer
- **Defect ID & Title**: DEF-19: Critical Navigation Triggers (Sign In and AI Triage) Hidden on Mobile and Omitted from Mobile Drawer
- **Description**: In `frontend/src/components/layout/Navbar.tsx`, the desktop navigation bar hides the "AI Triage" trigger (`hidden sm:inline-flex`) and the "Sign In" trigger (`hidden md:inline-flex`) on small screens. However, in the mobile menu drawer (`mobileMenuOpen`, lines 207-252), neither of these triggers is included. Mobile users on smartphone viewports have no visual control or button to access patient authentication or the AI Clinical Assistant from the navigation bar.
- **Reproduction Steps**:
  1. Resize browser viewport to 375px width (iPhone / mobile resolution).
  2. Tap the hamburger icon to open the mobile drawer.
  3. Look for "AI Triage" and "Sign In".
- **Expected Behavior**: All desktop navigation actions are available within the mobile slide-down menu drawer.
- **Actual Behavior**: "AI Triage" and "Sign In" are completely missing from the mobile drawer.
- **Severity**: Medium
- **Affected Component or File**: `d:\MediApp\frontend\src\components\layout\Navbar.tsx:135, 146, 207-252`

---

### DEF-20: Conflicting OTP Length Guidance (4-Digit Input Placeholder vs 6-Digit Server OTP)
- **Defect ID & Title**: DEF-20: Conflicting OTP Length Guidance (4-Digit Input Placeholder vs 6-Digit Server OTP)
- **Description**: In `frontend/src/components/logistics/OrderTrackingTimeline.tsx`, line 269 instructs the patient to "Provide this 6-digit verification code", line 403 sets `maxLength={6}`, and the backend generates a 6-digit number (`secrets.randbelow(900000) + 100000`). However, line 406 sets `placeholder="Enter 4-digit OTP (e.g. 4821)"`. This contradiction confuses patients and couriers regarding the required token length.
- **Reproduction Steps**:
  1. Open "My Orders & Tracking" in `OrderTrackingTimeline.tsx`.
  2. Inspect the placeholder text in the OTP verification input box.
- **Expected Behavior**: The placeholder text specifies 6 digits (e.g. `placeholder="Enter 6-digit OTP (e.g. 582914)"`).
- **Actual Behavior**: The placeholder displays `Enter 4-digit OTP (e.g. 4821)`.
- **Severity**: Low
- **Affected Component or File**: `d:\MediApp\frontend\src\components\logistics\OrderTrackingTimeline.tsx:269, 403, 406`

---

## Category 6: Clinical Design System & AGENTS.md Invariant Violations

### DEF-21: Hardcoded Substring Matching Overrides Cold-Chain Flag and Omits Cold-Chain Temperature Guarantee in Cart Drawer
- **Defect ID & Title**: DEF-21: Hardcoded Substring Matching Overrides Cold-Chain Flag and Omits Cold-Chain Temperature Guarantee in Cart Drawer
- **Description**: `d:\MediApp\AGENTS.md` Section 3 mandates: "For insulin, vaccines, and biologics, always render the Cold-Chain Temperature Guarantee badge (`2°C - 8°C Nominal IoT Monitored`)." In `frontend/src/components/catalogue/MedicineCard.tsx` lines 23-27, cold-chain status is determined purely via substring searching against `"insulin"`, `"vaccine"`, and `"biological"`, ignoring database flags. Furthermore, in `frontend/src/components/cart/CartDrawer.tsx` lines 216-231, items in the cart drawer omit the Cold-Chain Temperature Guarantee badge entirely, failing to display temperature monitoring status during the checkout phase.
- **Reproduction Steps**:
  1. Search for cold-chain formulations (e.g. "Lantus Solostar" or "Huminsulin").
  2. Add the item to the cart and open `CartDrawer.tsx`.
  3. Inspect the cart line item.
- **Expected Behavior**: The Cold-Chain Temperature Guarantee badge (`2°C - 8°C Nominal IoT Monitored`) is rendered on catalogue cards and inside the cart drawer for temperature-controlled products.
- **Actual Behavior**: The cart drawer does not display any cold-chain guarantee badge for temperature-sensitive items.
- **Severity**: Medium
- **Affected Component or File**: `d:\MediApp\frontend\src\components\catalogue\MedicineCard.tsx:23-27, 77`, `d:\MediApp\frontend\src\components\cart\CartDrawer.tsx:216-231`

---

### DEF-22: Non-Compliant StatusBadge Clinical Tokens and Missing Clinical Crimson Rejection Badge
- **Defect ID & Title**: DEF-22: Non-Compliant StatusBadge Clinical Tokens and Missing Clinical Crimson Rejection Badge
- **Description**: `d:\MediApp\AGENTS.md` Section 1 specifies precise clinical color tokens:
  - Clinical Emerald: `bg-emerald-500/10`, `text-emerald-700 dark:text-emerald-400`, `border-emerald-500/20`
  - Clinical Crimson (Rejection / Critical Restock): `bg-rose-500/10`, `text-rose-700 dark:text-rose-400`, `border-rose-500/20`
  In `frontend/src/components/ui/StatusBadge.tsx`, `verified` and `delivered` badges use `border-emerald-500/30 text-emerald-800`, violating the token spec. Furthermore, `StatusBadge.tsx` lacks a `"crimson"` or `"rejected"` badge type entirely. In `frontend/src/components/clinical/PharmacistReviewDesk.tsx` line 302, rejected prescriptions fall back to `type="rx"`, rendering rejected medical documents with an Amber caution badge instead of Clinical Crimson.
- **Reproduction Steps**:
  1. Open the Pharmacist Verification Desk and select a rejected prescription.
  2. Inspect the badge rendered in the prescription audit card header.
- **Expected Behavior**: Rejected prescriptions display a Clinical Crimson badge (`bg-rose-500/10 text-rose-700 dark:text-rose-400 border-rose-500/20`).
- **Actual Behavior**: The badge is rendered in Amber (`type="rx"`: `bg-amber-500/10 text-amber-800 border-amber-500/30`), confusing rejection with an active prescription requirement.
- **Severity**: Medium
- **Affected Component or File**: `d:\MediApp\frontend\src\components\ui\StatusBadge.tsx:64, 83-94, 126-136`, `d:\MediApp\frontend\src\components\clinical\PharmacistReviewDesk.tsx:302`

---

### DEF-23: Generic Price Match Trigger Omits Exact ₹ and % Savings on Card and Displays Unconditionally on Generic Formulations
- **Defect ID & Title**: DEF-23: Generic Price Match Trigger Omits Exact ₹ and % Savings on Card and Displays Unconditionally on Generic Formulations
- **Description**: `d:\MediApp\AGENTS.md` Section 3 mandates: "When a cheaper bioequivalent exists, provide the `Generic Price Match` trigger calculating exact ₹ and % savings." In `frontend/src/components/catalogue/MedicineCard.tsx` lines 118-130:
  1. The trigger button renders static text `"Generic Price Match • Check Bioequivalent"` without displaying calculated ₹ or % savings on the card.
  2. The trigger button is unconditionally rendered on every medicine card, even when the medicine is already a generic (e.g. `Generic Regular Soluble Insulin 100IU/ml`) or has no cheaper bioequivalent.
- **Reproduction Steps**:
  1. In the Medicine Catalogue, locate an unbranded generic medicine.
  2. Inspect the card.
  3. Click the "Generic Price Match" trigger button.
- **Expected Behavior**: The trigger is conditionally rendered when a cheaper bioequivalent exists and displays calculated savings (e.g. "Save ₹16.00 (62.7%)").
- **Actual Behavior**: The button is statically shown on all medicines, opening a modal that states "No Cheaper Generic Needed".
- **Severity**: Medium
- **Affected Component or File**: `d:\MediApp\frontend\src\components\catalogue\MedicineCard.tsx:118-130`

---

### DEF-24: Order Item Formulation Details and Active Generic Molecules Omitted in Order Tracking
- **Defect ID & Title**: DEF-24: Order Item Formulation Details and Active Generic Molecules Omitted in Order Tracking
- **Description**: `d:\MediApp\AGENTS.md` Section 3.1 mandates: "Always display both the commercial brand name and the active generic chemical molecule (e.g. *Aciloc 150mg* • *Ranitidine Hydrochloride*), dosage form, and strength (`Tablet • 150mg`)." In `frontend/src/components/logistics/OrderTrackingTimeline.tsx` lines 227-432, when an order is selected, telemetry, ETA, courier info, OTP, and status stepper are rendered, but `selectedOrder.items` is never referenced or rendered. Patients tracking their medication cannot view which items or chemical formulations are in the parcel.
- **Reproduction Steps**:
  1. Place an order containing multiple medicines.
  2. Navigate to "My Orders & Tracking".
  3. Select the order and review the right-hand details pane.
- **Expected Behavior**: The panel displays itemized formulations, active molecules, dosage forms, strengths, quantities, and line item costs.
- **Actual Behavior**: Item formulation details and active molecule names are entirely omitted from the order tracking view.
- **Severity**: High
- **Affected Component or File**: `d:\MediApp\frontend\src\components\logistics\OrderTrackingTimeline.tsx:227-432`

---

### DEF-25: Zero-Emoji Invariant Violation: Hardcoded Unicode Clockwise Arrow Symbol (`↻`) in Action Buttons
- **Defect ID & Title**: DEF-25: Zero-Emoji Invariant Violation: Hardcoded Unicode Clockwise Arrow Symbol (`↻`) in Action Buttons
- **Description**: `d:\MediApp\AGENTS.md` Section 2 strictly establishes the Zero-Emoji Invariant: "Never use unicode emojis in code, templates, or component labels. All visual metaphors must use Lucide React clinical vector icons." Across `app/static/js/admin.js`, `customer.js`, `delivery.js`, and `pharmacy.js`, 10 action buttons hardcode the raw unicode symbol `↻` (`\u21BB` CLOCKWISE OPEN CIRCLE ARROW) directly in button labels (e.g. `↻ Refresh Analytics`, `↻ Refresh`, `↻ Refresh Status`, `↻ Refresh Pool`).
- **Reproduction Steps**:
  1. Inspect `d:\MediApp\app\static\js\admin.js` at line 32.
  2. Observe `<button type="button" class="btn-demo-pill" id="btn-refresh-admin-stats">↻ Refresh Analytics</button>`.
- **Expected Behavior**: Button labels use clinical vector SVG icons (e.g. `RotateCcw` or `RefreshCw`) or plain text without raw unicode pictographs.
- **Actual Behavior**: Raw unicode character `↻` is embedded directly into user-facing action buttons.
- **Severity**: Low
- **Affected Component or File**: `d:\MediApp\app\static\js\admin.js:32, 151, 236, 318`, `customer.js:880`, `delivery.js:49, 272, 362`, `pharmacy.js:30, 239`

---

## Category 7: Accessibility (WCAG 2.1 AA & WAI-ARIA) Defects

### DEF-26: Modal Dialogs and Slide-Over Drawer Lack WAI-ARIA Semantics, Focus Trapping, and Scroll Locking
- **Defect ID & Title**: DEF-26: Modal Dialogs and Slide-Over Drawer Lack WAI-ARIA Semantics, Focus Trapping, and Scroll Locking
- **Description**: Across all modal overlays and drawers (`AuthModal.tsx`, `RoleLimitsModal.tsx`, `GenericPriceMatchModal.tsx`, `AITriageModal.tsx`, `RxUploadModal.tsx`, `CartDrawer.tsx`, and the pharmacist rejection modal in `PharmacistReviewDesk.tsx`):
  1. Containers lack `role="dialog"` and `aria-modal="true"`.
  2. Containers lack accessible title associations (`aria-labelledby` or `aria-label`).
  3. No focus trapping is implemented: pressing `Tab` allows focus to escape outside the modal into background page content.
  4. Body scroll is not locked: scrolling with a mouse wheel or touch gesture while a modal is open scrolls the background page.
  5. `GenericPriceMatchModal.tsx`, `RoleLimitsModal.tsx`, `RxUploadModal.tsx`, and the rejection modal lack backdrop click dismiss handlers.
  6. `RxUploadModal.tsx` and the rejection modal lack `Escape` key close listeners.
- **Reproduction Steps**:
  1. Open `RxUploadModal.tsx` or `RoleLimitsModal.tsx`.
  2. Press `Tab` repeatedly to cycle focus.
  3. Press `Escape` or click the dimmed backdrop in `RxUploadModal.tsx`.
  4. Scroll the mouse wheel while the modal is open.
- **Expected Behavior**: Modals conform to WAI-ARIA dialog specifications: `role="dialog"`, `aria-modal="true"`, focus trapped inside the container, background scroll locked, and dismissed via `Escape` or backdrop click.
- **Actual Behavior**: Focus escapes into background elements, background content scrolls, and modals fail to close via backdrop click or `Escape`.
- **Severity**: High
- **Affected Component or File**: `d:\MediApp\frontend\src\components\auth\AuthModal.tsx`, `RoleLimitsModal.tsx`, `GenericPriceMatchModal.tsx`, `AITriageModal.tsx`, `RxUploadModal.tsx`, `CartDrawer.tsx`, `PharmacistReviewDesk.tsx`

---

### DEF-27: Missing Form Input Accessible Labels in Patient Authentication and Tracking
- **Defect ID & Title**: DEF-27: Missing Form Input Accessible Labels in Patient Authentication and Tracking
- **Description**:
  1. In `frontend/src/components/auth/AuthModal.tsx` lines 156-236, all five form fields (Full Name, Phone Number, Default Delivery Address, Email Address, Password) contain visual `<label>` elements without `htmlFor` and `<input>` elements without `id` or `aria-label`. Clicking the text label does not transfer focus to the input, and screen readers cannot announce field purpose.
  2. In `frontend/src/components/logistics/OrderTrackingTimeline.tsx` lines 401-409, the OTP input field has no `<label>` or `aria-label`.
- **Reproduction Steps**:
  1. Open the "Sign In / Register" modal (`AuthModal.tsx`).
  2. Click on the text label "Email Address" or "Password".
  3. Run an accessibility inspector or screen reader on the form inputs.
- **Expected Behavior**: Every form input is programmatically associated with its label via `id` and `htmlFor` or has an `aria-label`, satisfying WCAG 2.1 Success Criterion 1.3.1 (Info and Relationships) and 4.1.2 (Name, Role, Value).
- **Actual Behavior**: Inputs are disconnected from their visual labels, preventing click-to-focus and screen reader identification.
- **Severity**: Medium
- **Affected Component or File**: `d:\MediApp\frontend\src\components\auth\AuthModal.tsx:156-236`, `d:\MediApp\frontend\src\components\logistics\OrderTrackingTimeline.tsx:401-409`

---

### DEF-28: Interactive Clickable Elements Lack Keyboard Navigation Attributes and Contain Nested Buttons
- **Defect ID & Title**: DEF-28: Interactive Clickable Elements Lack Keyboard Navigation Attributes and Contain Nested Buttons
- **Description**:
  1. In `frontend/src/components/auth/RoleLimitsModal.tsx` lines 134-196, the persona selection cards are `<div>` elements with `onClick` and `cursor-pointer`, but lack `role="button"`, `tabIndex={0}`, and `onKeyDown` listeners. Keyboard users navigating via `Tab` cannot focus or activate the cards. Furthermore, line 184 nests an interactive `<button>` inside the clickable `<div>`, causing nested interactive control violations.
  2. In `frontend/src/components/prescriptions/RxUploadModal.tsx` line 128, the drag-and-drop file upload target is a `<div>` with `onClick` but lacks `role="button"`, `tabIndex={0}`, and keyboard activation listeners.
  3. In `RoleLimitsModal.tsx` line 66, the close button contains only `<X className="h-5 w-5" />` without `aria-label` or `title`, announcing only "button" to screen readers.
- **Reproduction Steps**:
  1. Open `RoleLimitsModal.tsx` using keyboard navigation.
  2. Press `Tab` to navigate to the role cards.
  3. Observe that role cards are skipped by the tab sequence.
  4. Inspect the modal close button for accessible naming.
- **Expected Behavior**: All interactive components are keyboard operable with `tabIndex={0}`, proper ARIA roles, `Enter`/`Space` handlers, accessible names, and without nested interactive elements.
- **Actual Behavior**: Interactive `<div>` elements are unreachable via keyboard, close button lacks an accessible name, and nested interactive controls violate HTML semantics.
- **Severity**: Medium
- **Affected Component or File**: `d:\MediApp\frontend\src\components\auth\RoleLimitsModal.tsx:66, 134-196`, `d:\MediApp\frontend\src\components\prescriptions\RxUploadModal.tsx:128`

---

### DEF-29: Low Text Contrast Ratios Failing WCAG 2.1 AA 4.5:1 Minimum Threshold
- **Defect ID & Title**: DEF-29: Low Text Contrast Ratios Failing WCAG 2.1 AA 4.5:1 Minimum Threshold
- **Description**: Several text and data visualization elements fail the WCAG 2.1 AA minimum contrast ratio of 4.5:1 for normal text:
  1. In `frontend/src/components/admin/AnalyticsDashboard.tsx` lines 194 and 227, chart Cartesian axes hardcode `stroke="#64748b"`. Against dark card backgrounds (`#0F172A`), this produces a contrast ratio of only 3.75:1.
  2. In `AnalyticsDashboard.tsx` line 261, table column headers use `text-slate-400` on `#FFFFFF` in light mode, resulting in a low contrast ratio of 2.5:1.
  3. In `frontend/src/components/catalogue/MedicineCard.tsx` lines 94 and 102, clinical specification labels use `text-slate-400 dark:text-slate-500`, yielding 2.5:1 in light mode and 3.76:1 in dark mode.
- **Reproduction Steps**:
  1. Switch to Dark Mode and view `AnalyticsDashboard.tsx`.
  2. Measure contrast of chart axis text `#64748b` against background `#0F172A`.
  3. Switch to Light Mode and inspect table headers in `AnalyticsDashboard.tsx` and specification headers in `MedicineCard.tsx`.
- **Expected Behavior**: All text elements provide a contrast ratio of at least 4.5:1 against their backgrounds in both light and dark themes.
- **Actual Behavior**: Multiple text and axis elements exhibit contrast ratios between 2.5:1 and 3.75:1, failing WCAG 2.1 AA standards.
- **Severity**: Medium
- **Affected Component or File**: `d:\MediApp\frontend\src\components\admin\AnalyticsDashboard.tsx:194, 227, 261`, `d:\MediApp\frontend\src\components\catalogue\MedicineCard.tsx:94, 102`

---

## Verification & Audit Invariants

### Verification of Zero Code Modifications
All investigations were performed strictly in read-only and static analysis modes. No source code files in `d:\MediApp` have been modified, updated, or deleted. The only change to the repository is the addition of this audit deliverable `DEFECTS.md`.
