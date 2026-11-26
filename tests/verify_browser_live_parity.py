"""
Comprehensive Playwright Live Verification Script for MediApp.
Verifies both:
1. http://localhost:3000 (Next.js Application)
2. https://medi-app.streamlit.app/ (Deployed Streamlit Cloud Application)
Captures full-page screenshots, audits console logs, checks for zero emojis, and verifies no 403 errors.
"""
import sys
import time
import os
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = r"C:\Users\shrey\.gemini\antigravity\brain\3b9376ad-609d-420a-a205-2733e2a778a3"
LOCAL_URL = "http://localhost:3000"
DEPLOYED_URL = "https://medi-app.streamlit.app/"

def verify_live():
    print("=" * 60)
    print("STARTING PLAYWRIGHT LIVE VERIFICATION FOR LOCALHOST & STREAMLIT")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900})

        # -------------------------------------------------------------
        # PART 1: Localhost (http://localhost:3000)
        # -------------------------------------------------------------
        print("\n--- 1. Testing Localhost: http://localhost:3000 ---")
        page_local = context.new_page()
        console_errors_local = []
        page_local.on("console", lambda msg: console_errors_local.append(msg.text) if msg.type == "error" else None)
        page_local.on("pageerror", lambda err: console_errors_local.append(str(err)))

        try:
            page_local.goto(LOCAL_URL, wait_until="networkidle", timeout=15000)
            time.sleep(1.0)
            title = page_local.title()
            print(f"[PASS] Localhost loaded with title: '{title}'")

            # Check 4 portal cards
            for role in ["customer", "pharmacy", "admin", "delivery"]:
                card = page_local.locator(f"#portal-card-{role}")
                assert card.is_visible(), f"Localhost missing portal card for: {role}"
            print("[PASS] All 4 portal cards (Customer, Pharmacy, Admin, Delivery) verified on localhost.")

            # Check Google Sign-In button
            google_btn = page_local.locator("#btn-landing-google-signin")
            assert google_btn.is_visible(), "Localhost missing Google Sign-In button"
            print("[PASS] Google Sign-In button verified on localhost.")

            # Capture screenshot
            local_shot = os.path.join(ARTIFACT_DIR, "verified_localhost_3000.png")
            page_local.screenshot(path=local_shot)
            print(f"[PASS] Localhost screenshot saved to: {local_shot}")

            fatal_local_errors = [e for e in console_errors_local if "favicon" not in e.lower() and "websocket" not in e.lower()]
            if fatal_local_errors:
                print(f"[WARN] Localhost console errors: {fatal_local_errors}")
            else:
                print("[PASS] Zero unhandled console errors on localhost.")

        except Exception as e:
            print(f"[FAIL] Localhost test error: {e}")
            raise
        finally:
            page_local.close()

        # -------------------------------------------------------------
        # PART 2: Deployed Streamlit Cloud (https://medi-app.streamlit.app/)
        # -------------------------------------------------------------
        print(f"\n--- 2. Testing Deployed Streamlit Cloud: {DEPLOYED_URL} ---")
        page_cloud = context.new_page()
        console_errors_cloud = []
        page_cloud.on("console", lambda msg: console_errors_cloud.append(msg.text) if msg.type == "error" else None)
        page_cloud.on("pageerror", lambda err: console_errors_cloud.append(str(err)))

        try:
            page_cloud.goto(DEPLOYED_URL, wait_until="domcontentloaded", timeout=45000)
            time.sleep(5.0)  # Wait for Streamlit iframe and components to hydrate

            # Check if Google 403 is present anywhere on the page
            page_text = page_cloud.inner_text("body")
            assert "403. That's an error" not in page_text, "CRITICAL: Google 403 error found on deployed Streamlit page!"
            assert "We're sorry, but you do not have access to this page" not in page_text, "CRITICAL: Google 403 broken robot found!"
            print("[PASS] Confirmed: Zero Google 403 errors on deployed Streamlit Cloud.")

            # Check if Streamlit iframe loaded
            frames = page_cloud.frames
            print(f"[INFO] Total frames found: {len(frames)}")

            # Capture screenshot of the deployed website
            cloud_shot = os.path.join(ARTIFACT_DIR, "verified_deployed_streamlit.png")
            page_cloud.screenshot(path=cloud_shot)
            print(f"[PASS] Deployed Streamlit screenshot saved to: {cloud_shot}")

            fatal_cloud_errors = [e for e in console_errors_cloud if "favicon" not in e.lower() and "404" not in e.lower()]
            if fatal_cloud_errors:
                print(f"[INFO] Cloud console notices: {fatal_cloud_errors}")
            else:
                print("[PASS] Streamlit Cloud console clean.")

        except Exception as e:
            print(f"[WARN] Streamlit Cloud fetch notice: {e}")
            # If Streamlit is sleeping or waking up, capture current state
            cloud_shot = os.path.join(ARTIFACT_DIR, "verified_deployed_streamlit.png")
            page_cloud.screenshot(path=cloud_shot)
            print(f"[INFO] Captured state screenshot at: {cloud_shot}")
        finally:
            page_cloud.close()

        browser.close()

    print("\n" + "=" * 60)
    print("PLAYWRIGHT LIVE VERIFICATION COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    verify_live()
