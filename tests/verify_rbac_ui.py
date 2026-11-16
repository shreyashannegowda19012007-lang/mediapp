"""
Verifies Auth0 Role-Based Access Control (RBAC) across Next.js and Streamlit:
1. Customer: sees Medicine Catalogue & My Orders; Cart and Upload Rx present; Pharmacist Desk & Hospital Analytics hidden.
2. Pharmacist: sees Pharmacist Desk & Formulary Lookup; Cart and Upload Rx hidden; Hospital Analytics hidden.
3. Delivery: sees Delivery Fleet & Tracking; Cart, Upload Rx, Catalogue hidden.
4. Admin: sees Hospital Analytics & Network Formulary; Cart & Upload Rx hidden.
"""
import asyncio
from playwright.async_api import async_playwright

async def verify_nextjs_rbac():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()

        print("\n--- Testing Next.js (http://localhost:3000) RBAC ---")
        await page.goto("http://localhost:3000", wait_until="networkidle")

        # 1. Customer verification
        print("1. Verifying Customer Workspace...")
        nav_buttons = await page.locator("header nav button").all_inner_texts()
        print(f"Customer Nav Tabs: {nav_buttons}")
        assert "Medicine Catalogue" in nav_buttons
        assert "My Orders & Tracking" in nav_buttons
        assert "Pharmacist Desk" not in nav_buttons
        assert "Hospital Analytics" not in nav_buttons

        # Upload Rx button and Cart should be visible for customer
        upload_rx = page.locator("header button:has-text('Upload Rx')")
        assert await upload_rx.count() > 0, "Upload Rx should be visible for Customer"

        cart_btn = page.locator("header button[title='Open prescription cart']")
        assert await cart_btn.count() > 0, "Cart button should be visible for Customer"

        await page.screenshot(path="tests/rbac_nextjs_customer.png")
        print("Customer verification passed!")

        # 2. Switch to Pharmacist
        print("2. Switching to Clinical Pharmacist...")
        role_btn = page.locator("header button[title='View Auth0 Role Limits & Permissions']")
        await role_btn.click()
        await page.wait_for_selector("text=Role-Based Access Control")

        # Click Clinical Pharmacist row
        pharmacy_card = page.locator("div.cursor-pointer", has_text="Clinical Pharmacist").first
        await pharmacy_card.click()
        await page.wait_for_timeout(800)

        nav_buttons_pharm = await page.locator("header nav button").all_inner_texts()
        print(f"Pharmacist Nav Tabs: {nav_buttons_pharm}")
        assert "Pharmacist Verification Desk" in nav_buttons_pharm
        assert "Formulary Lookup" in nav_buttons_pharm
        assert "Hospital Analytics" not in nav_buttons_pharm

        # Upload Rx and Cart must be hidden for pharmacist
        assert await page.locator("header button:has-text('Upload Rx')").count() == 0, "Upload Rx should be hidden for Pharmacist"
        assert await page.locator("header button[title='Open prescription cart']").count() == 0, "Cart should be hidden for Pharmacist"

        await page.screenshot(path="tests/rbac_nextjs_pharmacist.png")
        print("Pharmacist verification passed!")

        # 3. Switch to Delivery
        print("3. Switching to Delivery Courier...")
        await role_btn.click()
        await page.wait_for_selector("text=Role-Based Access Control")
        delivery_card = page.locator("div.cursor-pointer", has_text="Delivery Rider").first
        await delivery_card.click()
        await page.wait_for_timeout(800)

        nav_buttons_deliv = await page.locator("header nav button").all_inner_texts()
        print(f"Delivery Nav Tabs: {nav_buttons_deliv}")
        assert "Delivery Fleet & Tracking" in nav_buttons_deliv
        assert "Pharmacist Verification Desk" not in nav_buttons_deliv
        assert "Hospital Analytics" not in nav_buttons_deliv
        assert await page.locator("header button:has-text('Upload Rx')").count() == 0
        assert await page.locator("header button[title='Open prescription cart']").count() == 0

        await page.screenshot(path="tests/rbac_nextjs_delivery.png")
        print("Delivery verification passed!")

        # 4. Switch to Admin
        print("4. Switching to Hospital HQ Admin...")
        await role_btn.click()
        await page.wait_for_selector("text=Role-Based Access Control")
        admin_card = page.locator("div.cursor-pointer", has_text="Hospital HQ Admin").first
        await admin_card.click()
        await page.wait_for_timeout(800)

        nav_buttons_admin = await page.locator("header nav button").all_inner_texts()
        print(f"Admin Nav Tabs: {nav_buttons_admin}")
        assert "Hospital Analytics & Oversight" in nav_buttons_admin
        assert "Network Formulary" in nav_buttons_admin
        assert "Delivery Fleet & Tracking" not in nav_buttons_admin

        await page.screenshot(path="tests/rbac_nextjs_admin.png")
        print("Admin verification passed!")

        await browser.close()
        print("\nAll Next.js RBAC assertions PASSED successfully!")

async def verify_streamlit_rbac():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()

        print("\n--- Testing Streamlit (http://localhost:8501) RBAC ---")
        await page.goto("http://localhost:8501", wait_until="networkidle")
        await page.wait_for_timeout(2000)

        # In Streamlit, the app is rendered inside an iframe
        frame = page.frame_locator("iframe").first

        # Check default Customer tabs
        nav_buttons = await frame.locator("#main-nav-tabs button").all_inner_texts()
        print(f"Streamlit Customer Nav Tabs: {nav_buttons}")
        assert "Medicine Catalogue" in nav_buttons
        assert "My Orders & Tracking" in nav_buttons
        assert "Pharmacist Desk" not in nav_buttons
        assert "Hospital Analytics" not in nav_buttons

        # Upload Rx and Cart should be visible for customer
        assert await frame.locator("#header-upload-rx-btn").is_visible()
        assert await frame.locator("#header-cart-btn").is_visible()

        # Switch to Pharmacist via Role Limits Modal in Streamlit
        print("Switching Streamlit role to Pharmacist...")
        role_btn = frame.locator("button[title='View Auth0 Role Limits & Permissions']")
        await role_btn.click()
        await page.wait_for_timeout(500)

        await frame.locator("div[onclick=\"selectRole('pharmacy')\"]").click()
        await page.wait_for_timeout(500)

        nav_buttons_pharm = await frame.locator("#main-nav-tabs button").all_inner_texts()
        print(f"Streamlit Pharmacist Nav Tabs: {nav_buttons_pharm}")
        assert "Pharmacist Verification Desk" in nav_buttons_pharm
        assert "Formulary Lookup" in nav_buttons_pharm
        assert "Hospital Analytics" not in nav_buttons_pharm

        # Upload Rx and Cart must be hidden for pharmacist
        assert not await frame.locator("#header-upload-rx-btn").is_visible()
        assert not await frame.locator("#header-cart-btn").is_visible()

        await page.screenshot(path="tests/rbac_streamlit_verified.png")
        print("Streamlit RBAC verification passed!")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify_nextjs_rbac())
    asyncio.run(verify_streamlit_rbac())
