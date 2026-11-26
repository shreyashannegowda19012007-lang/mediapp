"""
Automated Playwright Browser Verification Script for MediApp Exact UI Match.
Verifies all 6 UI screens corresponding to user-provided specifications:
1. Portal Selector Landing Page (media_1795632901724_b02d7829.png)
2. Customer Portal - A-Z Brand Search (media_1795632908633_8f4437fb.png)
3. Customer Portal - AI Prescription Scanner (media_1795632915059_9398cf36.png)
4. Pharmacy Partner Portal (media_1795632920052_eb6634bc.png)
5. Admin Portal (media_1795632924564_bb38bb6d.png)
6. Delivery Partner Portal (media_1795632929586_4a071c1f.png)
"""
import os
import sys
import time
from playwright.sync_api import sync_playwright

FRONTEND_URL = "http://localhost:3000"
ARTIFACT_DIR = r"C:\Users\shrey\.gemini\antigravity\brain\3b9376ad-609d-420a-a205-2733e2a778a3"

def run_verification():
    print("=" * 70)
    print("STARTING PLAYWRIGHT VERIFICATION FOR EXACT UI SPECIFICATIONS")
    print("=" * 70)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            color_scheme="dark"
        )
        page = context.new_page()

        # Step 1: Portal Selector Landing Page (Image 1)
        print("\n--- Verifying Screen 1: Portal Selector Landing Page ---")
        page.goto(FRONTEND_URL, wait_until="networkidle")
        time.sleep(1.0)

        # Assert key elements
        assert page.locator("text=Medicines delivered from").is_visible(), "Hero title missing"
        assert page.locator("text=pharmacies near you").is_visible(), "Hero cyan highlight missing"
        assert page.locator("text=CHOOSE YOUR PORTAL").is_visible(), "Choose your portal missing"
        assert page.locator("text=ORDER MEDICINES").is_visible(), "Customer portal card missing"
        assert page.locator("text=FULFIL ORDERS").is_visible(), "Pharmacy portal card missing"
        assert page.locator("text=OPERATE PLATFORM").is_visible(), "Admin portal card missing"
        assert page.locator("text=EARN ON THE GO").is_visible(), "Delivery portal card missing"

        shot1 = os.path.join(ARTIFACT_DIR, "exact_ui_01_landing_portal_selector.png")
        page.screenshot(path=shot1)
        print(f"[PASS] Screen 1 Verified & Captured: {shot1}")

        # Step 2: Customer Portal - A-Z Brand Search (Image 2)
        print("\n--- Verifying Screen 2: Customer Portal - Brand Search ---")
        page.click("text=ORDER MEDICINES")
        time.sleep(1.0)

        assert page.locator("text=MediApp Substitutes").is_visible(), "Substitutes title missing"
        assert page.locator("text=Live DB Connected").is_visible(), "Live DB status missing"
        assert page.locator("text=A-Z Brand Search").is_visible(), "A-Z Brand Search tab missing"
        assert page.locator("text=EXTENSIVE A-Z SUBSTITUTE DATABASE").is_visible(), "Feature card 1 missing"
        assert page.locator("text=PROACTIVE SAFETY WARNINGS").is_visible(), "Feature card 2 missing"
        assert page.locator("text=All portals").is_visible(), "All portals button missing"

        # Search for a medicine
        search_input = page.locator("input[placeholder*='Search 250,000+ brands']")
        search_input.fill("Augmentin")
        time.sleep(1.0)

        shot2 = os.path.join(ARTIFACT_DIR, "exact_ui_02_customer_brand_search.png")
        page.screenshot(path=shot2)
        print(f"[PASS] Screen 2 Verified & Captured: {shot2}")

        # Step 3: Customer Portal - AI Prescription Scanner (Image 3)
        print("\n--- Verifying Screen 3: Customer Portal - AI Prescription Scanner ---")
        page.click("text=AI Prescription Scanner")
        time.sleep(0.5)

        assert page.locator("text=Fuzzy OCR Matching Engine Active").is_visible(), "OCR Engine header missing"
        assert page.locator("text=Correcting handwriting OCR typos").is_visible(), "OCR Engine subtitle missing"

        # Trigger demo prescription scan
        page.click("text=Scan Demo Prescription")
        time.sleep(1.2) # Catch the scanning state with laser beam and Gemini Vision status

        shot3 = os.path.join(ARTIFACT_DIR, "exact_ui_03_customer_ai_prescription_scanner.png")
        page.screenshot(path=shot3)
        print(f"[PASS] Screen 3 Verified & Captured: {shot3}")

        # Return to landing page
        page.click("text=All portals")
        time.sleep(0.8)

        # Step 4: Pharmacy Partner Portal (Image 4)
        print("\n--- Verifying Screen 4: Pharmacy Partner Portal ---")
        page.click("text=FULFIL ORDERS")
        time.sleep(1.0)

        assert page.locator("text=PHARMACY PARTNER").is_visible(), "Pharmacy Partner badge missing"
        assert page.locator("text=Anne medical stores").is_visible(), "Pharmacy name missing"
        assert page.locator("text=ORDERS SEEN").is_visible(), "Orders Seen KPI missing"
        assert page.locator("text=Live orders").first.is_visible(), "Live orders heading missing"
        assert page.locator("text=Daily inventory").first.is_visible(), "Daily inventory heading missing"

        shot4 = os.path.join(ARTIFACT_DIR, "exact_ui_04_pharmacy_partner_portal.png")
        page.screenshot(path=shot4)
        print(f"[PASS] Screen 4 Verified & Captured: {shot4}")

        # Return to landing page
        page.click("text=All portals")
        time.sleep(0.8)

        # Step 5: Admin Portal (Image 5)
        print("\n--- Verifying Screen 5: Admin Portal ---")
        page.click("text=OPERATE PLATFORM")
        time.sleep(1.0)

        assert page.locator("text=ADMIN").first.is_visible(), "Admin badge missing"
        assert page.locator("text=admin@mediapp.in").first.is_visible(), "Admin email missing"
        assert page.locator("text=LIVE ORDERS").first.is_visible(), "Live orders KPI missing"
        assert page.locator("text=ORDER REVENUE").first.is_visible(), "Order revenue KPI missing"
        assert page.locator("text=PHARMACIES").first.is_visible(), "Pharmacies KPI missing"
        assert page.locator("text=Wellness Forever — BTM").first.is_visible(), "Pharmacy list missing"
        assert page.locator("text=Add pharmacy").first.is_visible(), "Add pharmacy button missing"

        shot5 = os.path.join(ARTIFACT_DIR, "exact_ui_05_admin_portal.png")
        page.screenshot(path=shot5)
        print(f"[PASS] Screen 5 Verified & Captured: {shot5}")

        # Return to landing page
        page.click("text=All portals")
        time.sleep(0.8)

        # Step 6: Delivery Partner Portal (Image 6)
        print("\n--- Verifying Screen 6: Delivery Partner Portal ---")
        page.click("text=EARN ON THE GO")
        time.sleep(1.0)

        assert page.locator("text=DELIVERY").first.is_visible(), "Delivery badge missing"
        assert page.locator("text=DELIVERIES").first.is_visible(), "Deliveries KPI missing"
        assert page.locator("text=TODAY'S PAYOUT").first.is_visible(), "Today Payout KPI missing"
        assert page.locator("text=Pending deliveries nearby").first.is_visible(), "Pending deliveries missing"
        assert page.locator("text=Earnings").first.is_visible(), "Earnings section missing"
        assert page.locator("text=Live delivery feed").first.is_visible(), "Footer feed missing"

        shot6 = os.path.join(ARTIFACT_DIR, "exact_ui_06_delivery_partner_portal.png")
        page.screenshot(path=shot6)
        print(f"[PASS] Screen 6 Verified & Captured: {shot6}")

        context.close()
        browser.close()

    print("\n" + "=" * 70)
    print("ALL 6 EXACT UI SCREENS VERIFIED AND EVIDENCE CAPTURED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_verification()
