"""
Playwright E2E verification for the AI Ailment Specialist tab in CustomerPortalView:
Verifies diverse condition chips, 5-pillar clinical structured output,
emergency red-flag alert, and live dispensary stock linking.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = Path(r"C:\Users\shrey\.gemini\antigravity\brain\3b9376ad-609d-420a-a205-2733e2a778a3")

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        page.goto("http://localhost:3000", wait_until="networkidle")
        page.locator("text=Order Medicines").first.click()
        page.wait_for_timeout(800)

        # Switch to AI Ailment Specialist tab
        page.locator("text=AI Ailment Specialist").first.click()
        page.wait_for_timeout(500)

        # 1. Test non-emergency diverse condition chip: Loose motions & diarrhea
        page.locator("text=Loose motions & diarrhea").first.click()
        page.wait_for_selector("text=Live Stock Verified Dispensary Formulations", timeout=10000)

        page_text = page.locator("body").inner_text()
        assert "Clinical Context" in page_text or "Assessment" in page_text, "5-pillar Clinical Context missing"
        assert "Self-Care" in page_text, "5-pillar Self-Care missing"
        assert "Red Flags" in page_text, "5-pillar Red Flags missing"
        assert "Physician Consultation" in page_text, "5-pillar Physician Consultation missing"

        shot1 = ARTIFACT_DIR / "ai_ailment_diarrhea_verified.png"
        page.screenshot(path=str(shot1))
        print(f"Verified Diarrhea 5-pillar UI -> {shot1}")

        # 2. Test second diverse condition: Mouth ulcers & canker sores
        page.locator("text=Mouth ulcers & canker sores").first.click()
        page.wait_for_timeout(1200)
        ulcer_text = page.locator("body").inner_text()
        assert ulcer_text != page_text, "Response did not update for Mouth ulcers!"

        # 3. Test Emergency Red-Flag Priority
        inp = page.locator("#ailment-query-input")
        inp.fill("Crushing central chest pain radiating to left arm and shortness of breath")
        page.locator("#btn-ailment-assess").click()
        page.wait_for_selector("text=Emergency Red-Flag Alert", timeout=8000)

        shot2 = ARTIFACT_DIR / "ai_ailment_emergency_verified.png"
        page.screenshot(path=str(shot2))
        print(f"Verified Emergency Red-Flag Alert UI -> {shot2}")

        browser.close()
        print("ALL AI AILMENT UI CHECKS PASSED!")

if __name__ == "__main__":
    run()
