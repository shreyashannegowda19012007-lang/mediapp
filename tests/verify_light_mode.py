from playwright.sync_api import sync_playwright

p = sync_playwright().start()
b = p.chromium.launch()
# Emulate dark OS preference to recreate the exact condition
pg = b.new_page(viewport={'width': 1440, 'height': 900}, color_scheme='dark')
pg.goto('http://localhost:3000', wait_until='networkidle')

# Click Hospital Analytics tab (to match user's screenshot)
pg.get_by_role('button', name='Hospital Analytics').click()
pg.wait_for_timeout(500)

# Switch to Light mode
pg.locator('[title*="Light"]').first.click()
pg.wait_for_timeout(1000)

pg.screenshot(path='tests/light_mode_verification.png', full_page=True)
b.close()
p.stop()
print('Screenshot saved to tests/light_mode_verification.png')
