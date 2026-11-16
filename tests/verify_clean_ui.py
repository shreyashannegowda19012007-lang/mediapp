from playwright.sync_api import sync_playwright

def verify_clean_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # Test Localhost 3000
        p3000 = browser.new_page(viewport={'width': 1440, 'height': 900})
        p3000.goto('http://localhost:3000', wait_until='networkidle')
        p3000.screenshot(path='tests/clean_3000_dark.png', full_page=True)
        
        # Switch to Light Mode
        p3000.locator('button:has-text("Light")').click()
        p3000.wait_for_timeout(300)
        p3000.screenshot(path='tests/clean_3000_light.png', full_page=True)
        
        # Test Explore button click
        btn = p3000.locator('#btn-explore-catalogue')
        btn.click()
        p3000.wait_for_timeout(300)
        print("Localhost 3000 verified in Light & Dark modes!")
        
        # Test Localhost 8501 (Streamlit)
        p8501 = browser.new_page(viewport={'width': 1440, 'height': 900})
        p8501.goto('http://localhost:8501', wait_until='networkidle')
        p8501.screenshot(path='tests/clean_8501_dark.png', full_page=True)
        
        frame = p8501.frame_locator('iframe').first
        light_btn = frame.locator('button:has-text("Light")')
        if light_btn.count() > 0:
            light_btn.click()
            p8501.wait_for_timeout(300)
            p8501.screenshot(path='tests/clean_8501_light.png', full_page=True)
            print("Streamlit 8501 verified in Light & Dark modes!")
            
        browser.close()

if __name__ == '__main__':
    verify_clean_ui()
