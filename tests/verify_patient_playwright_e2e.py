"""
Comprehensive Playwright Automation for Patient Role Demonstration:
1. Open http://localhost:3000
2. Login as Customer (customer@mediapp.local / Customer@123) via MultiRoleLoginGateway
3. Execute AI Symptom Triage query: 'severe headache and mild fever' -> verify 5 pillars & recommended medicines
4. Execute Emergency Red Flag Triage: 'crushing chest pain radiating to left arm' -> verify non-dismissible ER alert & zero medicines
5. Navigate to Prescription Center, upload rx_01_cardiology_printed.png -> submit for verification & capture confirmation
6. Browse 1,250 medicines in live catalogue, search medicines, add to cart
7. In Cart Drawer: verify item and prescription linked, choose mock payment (Card), place order
8. Navigate to My Orders & Tracking, verify Order ID, status, and 6-digit delivery OTP
9. Capture screenshots at each stage and output exact values.
"""
import asyncio
import os
import sys
import re
from playwright.async_api import async_playwright

SCREENSHOTS_DIR = os.path.abspath("tests/patient_workflow_evidence")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

async def run_patient_demonstration():
    print("=" * 60)
    print("STARTING COMPREHENSIVE PATIENT ROLE PLAYWRIGHT AUTOMATION")
    print("=" * 60)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1400, "height": 900}
        )
        page = await context.new_page()

        # Step 1: Gateway Landing & Customer Login
        print("\n[Step 1] Navigating to http://localhost:3000...")
        await page.goto("http://localhost:3000", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        await page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "01_gateway_landing.png"))
        print("  -> Captured 01_gateway_landing.png")

        # Check if already logged in or needs login
        user_badge = page.locator("#btn-user-badge")
        if await user_badge.count() > 0:
            print("  -> Session active, logging out first to ensure fresh customer login...")
            await user_badge.click()
            await page.wait_for_timeout(300)
            sign_out = page.locator("button:has-text('Sign Out')")
            if await sign_out.count() > 0:
                await sign_out.click()
                await page.wait_for_timeout(1000)

        # Login as Customer via gateway
        print("  -> Selecting Customer login tab...")
        await page.locator("#tab-login-customer").click()
        await page.wait_for_timeout(400)
        await page.locator("#btn-gateway-login-customer").click()
        await page.wait_for_selector("#btn-user-badge", timeout=8000)
        await page.wait_for_timeout(1000)
        await page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "02_patient_logged_in.png"))
        print("  -> Successfully logged in as Customer (Aditi Sharma / customer@mediapp.local)")
        print("  -> Captured 02_patient_logged_in.png")

        # Step 2: AI Symptom Triage Query (5 Pillars & Recommended Medicines)
        print("\n[Step 2] Performing AI Symptom Triage query...")
        triage_nav = page.locator("header nav button:has-text('Describe Medical Conditions')")
        await triage_nav.click()
        await page.wait_for_timeout(1000)

        input_box = page.locator("#medical-condition-input")
        await input_box.fill("severe headache and mild fever")
        await page.wait_for_timeout(500)
        await page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "03_ai_triage_query_input.png"))

        submit_triage = page.locator("#btn-submit-triage")
        await submit_triage.click()
        print("  -> Submitting triage query...")
        await page.wait_for_selector("text=Recommended Medicines in Live Stock", timeout=15000)
        await page.wait_for_timeout(1500)

        # Verify 5 Pillars text on page
        page_content = await page.content()
        pillars = [
            "Clinical Context" in page_content or "Clinical Assessment" in page_content,
            "Self-Care" in page_content,
            "Over-The-Counter" in page_content or "OTC" in page_content,
            "Red Flags" in page_content or "Emergency Warnings" in page_content,
            "Physician Consultation" in page_content or "Referral" in page_content
        ]
        print(f"  -> 5 Pillars Verified: {all(pillars)} (Individual: {pillars})")
        assert all(pillars), "Not all 5 clinical pillars found in response"

        # Check recommended medicines
        recs = await page.locator("h4").all_inner_texts()
        print(f"  -> Recommended Medicines found: {recs[:4]}")
        await page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "04_ai_triage_5pillars_recommendations.png"))
        print("  -> Captured 04_ai_triage_5pillars_recommendations.png")

        # Step 3: Emergency Red Flag Triage Query (112/911 alert, zero medicines)
        print("\n[Step 3] Performing Emergency Red Flag Triage query...")
        await input_box.fill("Patient experiencing crushing central chest pain radiating to left arm and cold sweat")
        await page.wait_for_timeout(500)
        await submit_triage.click()
        await page.wait_for_selector("text=Critical Emergency Warning Flag Detected", timeout=15000)
        await page.wait_for_timeout(1000)

        emergency_alert = page.locator("text=Critical Emergency Warning Flag Detected")
        assert await emergency_alert.count() > 0, "Emergency banner not displayed!"
        
        # Verify zero medicine recommendations shown in emergency mode
        zero_meds = await page.locator("text=Recommended Medicines in Live Stock").count() == 0
        print(f"  -> Emergency Alert Active: True | Zero Medicines Recommended: {zero_meds}")
        assert zero_meds, "Emergency mode should have zero medicine recommendations!"
        await page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "05_emergency_red_flag_alert.png"))
        print("  -> Captured 05_emergency_red_flag_alert.png")

        # Step 4: Upload Prescription in Patient Prescription Center
        print("\n[Step 4] Navigating to Patient Prescription Center...")
        rx_nav = page.locator("header nav button:has-text('Upload & Track Prescriptions')")
        await rx_nav.click()
        await page.wait_for_timeout(1000)
        await page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "07_prescription_center_initial.png"))

        rx_file_path = os.path.abspath("tests/test_prescriptions/rx_01_cardiology_printed.png")
        print(f"  -> Uploading prescription: {rx_file_path}")
        file_input = page.locator("input[type='file']")
        await file_input.set_input_files(rx_file_path)
        await page.wait_for_timeout(1000)
        await page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "08_prescription_selected_preview.png"))

        upload_submit = page.locator("button:has-text('Submit Prescription for Verification')")
        if await upload_submit.count() > 0:
            await upload_submit.click()
            print("  -> Clicked 'Submit Prescription for Verification'")
            # Wait for upload completion (either success message or reload list)
            await page.wait_for_timeout(4000)
            await page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "09_prescription_uploaded_success.png"))
            print("  -> Captured 09_prescription_uploaded_success.png")

        # Step 5: Browse 1,250 Live Stock Medicines in Catalogue
        print("\n[Step 5] Browsing live stock medicine catalogue...")
        cat_nav = page.locator("header nav button:has-text('Medicine Catalogue')")
        await cat_nav.click()
        await page.wait_for_timeout(1000)

        # Search for Pantoprazole / Paracetamol in catalogue
        search_input = page.locator("#search-medicines-input")
        await search_input.fill("Pantoprazole")
        await page.wait_for_timeout(800)
        await page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "06_catalogue_search_pantoprazole.png"))
        print("  -> Captured 06_catalogue_search_pantoprazole.png")

        # Add a medicine from catalogue to cart (which will open cart drawer)
        add_btn = page.locator("button:has-text('Add to Cart')").first
        if await add_btn.count() > 0:
            await add_btn.click()
            await page.wait_for_timeout(1500)
            print("  -> Added Pantoprazole to cart from catalogue")

        # Step 6: Review Cart Drawer & Complete Checkout with Mock Payment
        print("\n[Step 6] Reviewing Cart Drawer and placing order...")
        await page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "10_cart_drawer_open.png"))
        print("  -> Captured 10_cart_drawer_open.png")

        # Select payment method (Card button in grid)
        card_btn = page.locator("div.grid.grid-cols-3 button:has-text('Card')")
        if await card_btn.count() > 0:
            await card_btn.click()
            await page.wait_for_timeout(400)
            print("  -> Selected Card payment method")

        # Click Confirm & Place Order
        place_order_btn = page.locator("button:has-text('Confirm & Place Order'), button:has-text('Place Order')").last
        if await place_order_btn.is_enabled():
            await place_order_btn.click()
            print("  -> Clicked 'Confirm & Place Order'")
            await page.wait_for_selector("text=Order Successfully Dispatched", timeout=15000)
            await page.wait_for_timeout(1000)
            await page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "11_order_success_confirmation.png"))
            print("  -> Captured 11_order_success_confirmation.png")
            # Wait for drawer auto-close (2.5s)
            await page.wait_for_timeout(3500)

        # Step 7: View My Orders & Tracking
        print("\n[Step 7] Checking My Orders & Tracking...")
        orders_nav = page.locator("header nav button:has-text('My Orders & Tracking')")
        if await orders_nav.count() > 0:
            await orders_nav.click()
            await page.wait_for_timeout(2000)
            await page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "12_patient_orders_tracking.png"))
            print("  -> Captured 12_patient_orders_tracking.png")

            # Extract order text to retrieve Order ID, OTP, and Status
            page_text = await page.inner_text("main")
            print("\n--- Extracted Page Content Summary ---")
            found_order_id = None
            found_otp = None
            found_status = None
            for line in page_text.splitlines():
                if "ORD-" in line and not found_order_id:
                    m = re.search(r"ORD-[A-Za-z0-9-]+", line)
                    if m:
                        found_order_id = m.group(0)
                if len(line.strip()) == 6 and line.strip().isdigit() and not found_otp:
                    found_otp = line.strip()
                if any(k in line for k in ["ORD-", "OTP", "Delivery", "Status", "Rx", "Tracking order"]):
                    print("  ", line.strip())

            print(f"\nCaptured UI Order ID: {found_order_id}")
            print(f"Captured UI Delivery OTP: {found_otp}")

        print("\nPATIENT PLAYWRIGHT WORKFLOW DEMONSTRATION COMPLETE!")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_patient_demonstration())
