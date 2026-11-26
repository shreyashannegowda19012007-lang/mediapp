"""
Playwright automated test verifying Google OAuth 2.0 initiation, callback,
token extraction, session hydration, and customer workspace display in MediApp.
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = Path(r"C:\Users\shrey\.gemini\antigravity\brain\3b9376ad-609d-420a-a205-2733e2a778a3")

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        print("[1/5] Loading landing page on http://localhost:3000 ...")
        page.goto("http://localhost:3000", wait_until="networkidle")

        # Select Customer Portal
        print("[2/5] Entering Customer Portal ...")
        customer_card = page.locator("text=Order Medicines").first
        customer_card.click()
        page.wait_for_timeout(1000)

        # If already signed in, sign out first to test fresh login
        sign_out_initial = page.locator("text=Sign Out").first
        if sign_out_initial.is_visible():
            print("Existing active session detected. Clicking Sign Out for fresh OAuth test...")
            sign_out_initial.click()
            page.wait_for_timeout(1000)

        # Verify Google Sign-In button is visible
        print("[3/5] Locating Google Sign-In button ...")
        google_btn = page.locator("#btn-customer-google-signin")
        assert google_btn.is_visible(), "Google Sign-In button is not visible in customer portal header!"
        print("Google Sign-In button verified present!")

        # Click Google Sign-In
        print("[4/5] Clicking Google Sign-In button and awaiting OAuth redirect ...")
        google_btn.click()

        # Wait for redirect back to localhost:3000 and session hydration
        page.wait_for_selector("text=Sign Out", timeout=10000)
        current_url = page.url
        print(f"Current URL after OAuth redirect: {current_url}")

        # Check authenticated customer state
        print("[5/5] Verifying authenticated customer state ...")
        sign_out_btn = page.locator("text=Sign Out").first
        assert sign_out_btn.is_visible(), "Sign Out button should be visible when authenticated!"

        # Check user profile name or avatar
        user_name_text = page.locator("text=Shreyash").first
        assert user_name_text.is_visible(), "Verified Google user name should be displayed!"
        print("User Shreyash (Google Verified) verified successfully!")

        # Capture high-res verification screenshot
        screenshot_path = ARTIFACT_DIR / "exact_ui_google_auth_verified.png"
        page.screenshot(path=str(screenshot_path))
        print(f"Screenshot successfully saved: {screenshot_path}")

        browser.close()
        print("ALL GOOGLE AUTH E2E CHECKS PASSED PERFECTLY!")

if __name__ == "__main__":
    run()
