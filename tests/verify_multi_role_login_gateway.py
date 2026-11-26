"""
Playwright Browser Test Suite for Multi-Role Login Gateway & Dedicated Role Pages:
1. Initial Landing Page Verification:
   - 4 Login Tabs visible: Customer/Patient, Clinical Pharmacist, Delivery Courier, Hospital HQ Admin.
   - AI Medicine Suggestor Tool embedded directly on initial page.
   - Stock of Medicines Deliverable Instantly Nearby embedded directly on initial page.
2. Isolated Login & Dedicated Workspaces:
   - Patient Login -> navigates to Customer Workspace (catalogue, triage, prescriptions, orders, cart drawer; no staff tools).
   - Sign out -> returns to Initial Page.
   - Clinical Pharmacist Login -> navigates to Pharmacist Verification Desk (Rx review, OCR molecules, DDI; no cart/courier/admin).
   - Sign out -> returns to Initial Page.
   - Delivery Courier Login -> navigates to Delivery Fleet (dispatches, 2-8°C IoT telemetry, customer OTP verification; no patient clinical data).
   - Sign out -> returns to Initial Page.
   - Hospital HQ Admin Login -> navigates to Hospital HQ Analytics (fulfillment velocity, compliance, generic savings; no cart/courier).
   - Sign out -> returns to Initial Page.
3. AuthModal positioning & close verification (verifies modal is not cut off at top).
"""
import asyncio
import os
import shutil
from playwright.async_api import async_playwright

RECORDING_DIR = r"C:\Users\shrey\.gemini\antigravity\brain\3b9376ad-609d-420a-a205-2733e2a778a3"

async def run_multi_role_gateway_verification():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 850},
            record_video_dir=RECORDING_DIR,
            record_video_size={"width": 1280, "height": 850}
        )
        page = await context.new_page()

        print("\n============================================================")
        print("STAGE 1: Initial Login Page (Unauthenticated / Guest State)")
        print("============================================================")
        # Clear cookies/session first to ensure fresh unauthenticated guest view
        await context.clear_cookies()
        await page.goto("http://localhost:3000", wait_until="networkidle")
        await page.wait_for_timeout(1000)

        # 1.1 Verify the 4 Login Tabs on Gateway
        print("Checking 4 Role Login Tabs...")
        assert await page.locator("#tab-login-customer").count() > 0, "Patient login tab missing"
        assert await page.locator("#tab-login-pharmacy").count() > 0, "Pharmacist login tab missing"
        assert await page.locator("#tab-login-delivery").count() > 0, "Delivery login tab missing"
        assert await page.locator("#tab-login-admin").count() > 0, "Admin login tab missing"
        print("All 4 Role Login Tabs confirmed present!")

        # 1.2 Verify AI Medicine Suggestor Tool is present on initial page
        print("Checking AI Medicine Suggestor Tool on Initial Page...")
        assert await page.locator("#ai-medicine-suggestor").count() > 0, "AI suggestor section missing on initial page"
        # Check condition chips
        assert await page.locator("button:has-text('Acid reflux')").count() > 0, "Condition chip 'Acid reflux' missing"
        assert await page.locator("button:has-text('Fever')").count() > 0, "Condition chip 'Fever' missing"
        print("AI Medicine Suggestor Tool confirmed on initial page!")

        # 1.3 Verify Stock of Medicines Deliverable Instantly Nearby on initial page
        print("Checking Stock of Medicines Deliverable Instantly Nearby on Initial Page...")
        assert await page.locator("#instant-nearby-stock").count() > 0, "Instant nearby stock section missing"
        assert await page.locator("#search-medicines-input").count() > 0, "Search medicines input missing"
        assert await page.locator("text=Apollo Hospital Central Dispensary").count() > 0, "Apollo dispensary callout missing"
        print("Nearby Deliverable Medicine Stock confirmed on initial page!")

        await page.screenshot(path="tests/1_initial_landing_page.png")

        print("\n============================================================")
        print("STAGE 2: Customer / Patient Portal Isolated Workspace")
        print("============================================================")
        # Click patient fast login
        patient_login_btn = page.locator("#btn-gateway-login-customer")
        await patient_login_btn.click()
        await page.wait_for_timeout(1200)

        # Confirm user is authenticated as customer
        user_badge = page.locator("#btn-user-badge")
        await page.wait_for_selector("#btn-user-badge", timeout=5000)
        assert await user_badge.count() > 0, "User account badge not found after login"

        # Check allowed customer tabs
        tabs = await page.locator("header nav button").all_inner_texts()
        print(f"Customer Workspace Tabs: {tabs}")
        assert "Medicine Catalogue" in tabs
        assert "Describe Medical Conditions" in tabs
        assert "Upload & Track Prescriptions" in tabs
        assert "My Orders & Tracking" in tabs

        # Confirm staff controls are HIDDEN
        assert "Pharmacist Verification Desk" not in tabs
        assert "Hospital Analytics & Oversight" not in tabs
        assert await page.locator("header button[title='Open prescription cart']").count() > 0, "Cart should be accessible to customer"
        assert await page.locator("header button:has-text('Upload Rx')").count() > 0, "Upload Rx should be accessible to customer"

        await page.screenshot(path="tests/2_customer_isolated_workspace.png")
        print("Customer Portal verified with zero staff tools!")

        # Sign out from Customer
        await user_badge.click()
        await page.wait_for_timeout(300)
        sign_out_btn = page.locator("button:has-text('Sign Out')")
        await sign_out_btn.click()
        await page.wait_for_timeout(1000)
        print("Customer signed out. Returned to Initial Login Page.")

        print("\n============================================================")
        print("STAGE 3: Clinical Pharmacist Portal Isolated Workspace")
        print("============================================================")
        # Click Pharmacist Tab on Gateway
        await page.locator("#tab-login-pharmacy").click()
        await page.wait_for_timeout(400)
        pharmacy_login_btn = page.locator("#btn-gateway-login-pharmacy")
        await pharmacy_login_btn.click()
        await page.wait_for_timeout(1200)

        # Confirm landing directly on Pharmacist Verification Desk
        await page.wait_for_selector("#btn-user-badge", timeout=5000)
        pharm_tabs = await page.locator("header nav button").all_inner_texts()
        print(f"Pharmacist Workspace Tabs: {pharm_tabs}")
        assert "Pharmacist Verification Desk" in pharm_tabs
        assert "Formulary Lookup" in pharm_tabs

        # Verify Pharmacist Desk contents
        assert await page.locator("h1:has-text('Pharmacist Verification Desk')").count() > 0, "Pharmacist desk header missing"

        # Confirm customer cart and admin analytics are HIDDEN
        assert await page.locator("header button[title='Open prescription cart']").count() == 0, "Cart should be hidden for Pharmacist"
        assert await page.locator("header button:has-text('Upload Rx')").count() == 0, "Upload Rx should be hidden for Pharmacist"
        assert "Hospital Analytics & Oversight" not in pharm_tabs

        await page.screenshot(path="tests/3_pharmacist_isolated_workspace.png")
        print("Pharmacist Verification Desk verified with zero customer/admin clutter!")

        # Sign out from Pharmacist
        await page.locator("#btn-user-badge").click()
        await page.wait_for_timeout(300)
        await page.locator("button:has-text('Sign Out')").click()
        await page.wait_for_timeout(1000)
        print("Pharmacist signed out. Returned to Initial Login Page.")

        print("\n============================================================")
        print("STAGE 4: Delivery Courier Portal Isolated Workspace")
        print("============================================================")
        # Click Delivery Tab on Gateway
        await page.locator("#tab-login-delivery").click()
        await page.wait_for_timeout(400)
        delivery_login_btn = page.locator("#btn-gateway-login-delivery")
        await delivery_login_btn.click()
        await page.wait_for_timeout(1200)

        # Confirm landing directly on Delivery Fleet Portal
        await page.wait_for_selector("#btn-user-badge", timeout=5000)
        deliv_tabs = await page.locator("header nav button").all_inner_texts()
        print(f"Courier Workspace Tabs: {deliv_tabs}")
        assert "Delivery Fleet & Tracking" in deliv_tabs

        # Verify Courier Handoff OTP console / verified handover and IoT Telemetry
        has_otp_box = await page.locator("text=Courier Handover OTP Verification").count() > 0
        has_delivered_handover = await page.locator("text=Delivery Handover Verified").count() > 0
        assert has_otp_box or has_delivered_handover, "Courier OTP verification console or verified handover missing"
        assert await page.locator("text=IoT Telemetry").count() > 0, "IoT telemetry missing"

        # Confirm customer cart, prescription upload, and admin analytics are HIDDEN
        assert await page.locator("header button[title='Open prescription cart']").count() == 0
        assert await page.locator("header button:has-text('Upload Rx')").count() == 0
        assert "Pharmacist Verification Desk" not in deliv_tabs
        assert "Hospital Analytics & Oversight" not in deliv_tabs

        await page.screenshot(path="tests/4_delivery_isolated_workspace.png")
        print("Delivery Fleet Portal verified with courier OTP console and zero clinical clutter!")

        # Sign out from Delivery
        await page.locator("#btn-user-badge").click()
        await page.wait_for_timeout(300)
        await page.locator("button:has-text('Sign Out')").click()
        await page.wait_for_timeout(1000)
        print("Courier signed out. Returned to Initial Login Page.")

        print("\n============================================================")
        print("STAGE 5: Hospital HQ Admin Portal Isolated Workspace")
        print("============================================================")
        # Click Admin Tab on Gateway
        await page.locator("#tab-login-admin").click()
        await page.wait_for_timeout(400)
        admin_login_btn = page.locator("#btn-gateway-login-admin")
        await admin_login_btn.click()
        await page.wait_for_timeout(1200)

        # Confirm landing directly on Hospital HQ Portal
        await page.wait_for_selector("#btn-user-badge", timeout=5000)
        admin_tabs = await page.locator("header nav button").all_inner_texts()
        print(f"Admin Workspace Tabs: {admin_tabs}")
        assert "Hospital Analytics & Oversight" in admin_tabs
        assert "Network Formulary" in admin_tabs

        # Verify Admin Analytics Dashboard contents
        assert await page.locator("h1:has-text('Hospital Analytics')").count() > 0, "Admin analytics header missing"
        assert await page.locator("text=Cold-Chain Compliance").count() > 0, "Admin analytics metric missing"

        # Confirm customer cart and courier OTP controls are HIDDEN
        assert await page.locator("header button[title='Open prescription cart']").count() == 0
        assert await page.locator("header button:has-text('Upload Rx')").count() == 0
        assert "Delivery Fleet & Tracking" not in admin_tabs

        await page.screenshot(path="tests/5_admin_isolated_workspace.png")
        print("Hospital HQ Portal verified with executive oversight and zero customer/courier clutter!")

        # Sign out from Admin
        await page.locator("#btn-user-badge").click()
        await page.wait_for_timeout(300)
        await page.locator("button:has-text('Sign Out')").click()
        await page.wait_for_timeout(1000)
        print("Admin signed out. Returned to Initial Login Page.")

        print("\n============================================================")
        print("STAGE 6: AuthModal Positioning & Visibility Verification")
        print("============================================================")
        # Open AuthModal via header button
        header_login_btn = page.locator("#btn-header-login")
        await header_login_btn.click()
        await page.wait_for_timeout(600)

        # Verify AuthModal element
        auth_modal = page.locator("#auth-modal")
        assert await auth_modal.count() > 0, "Auth modal not found"

        # Check modal bounding box to ensure it is NOT clipped at top (y >= 0)
        box = await auth_modal.bounding_box()
        print(f"AuthModal Bounding Box: {box}")
        assert box is not None, "Auth modal has no bounding box"
        assert box['y'] >= 10, f"Auth modal top is clipped! y={box['y']}"

        # Check close button is visible and clickable
        close_btn = page.locator("button[aria-label='Close authentication modal']")
        assert await close_btn.count() > 0, "Close button not found in modal"
        await page.screenshot(path="tests/6_auth_modal_fixed_positioning.png")

        # Click close button and confirm modal closes
        await close_btn.click()
        await page.wait_for_timeout(500)
        assert await auth_modal.count() == 0, "Auth modal did not close after clicking close button"
        print("AuthModal positioning and close button verified 100% functional!")

        # Final video capture
        await page.wait_for_timeout(1000)
        video_path = await page.video.path()
        await context.close()
        await browser.close()

        print(f"\nVerification finished successfully! Video recorded at: {video_path}")
        
        # Copy to recording_14.webm and recording_14.mp4 in RECORDING_DIR
        target_webm = os.path.join(RECORDING_DIR, "recording_14.webm")
        target_mp4 = os.path.join(RECORDING_DIR, "recording_14.mp4")
        if os.path.exists(video_path):
            shutil.copyfile(video_path, target_webm)
            shutil.copyfile(video_path, target_mp4)
            print(f"Video saved to: {target_mp4}")

if __name__ == "__main__":
    asyncio.run(run_multi_role_gateway_verification())
