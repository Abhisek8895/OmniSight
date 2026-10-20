from playwright.sync_api import sync_playwright


def test_responsive_layout():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Open website at desktop size
        page.set_viewport_size({"width": 1280, "height": 720})
        page.goto("http://localhost:8000/Mock-Website")

        # Wait 5 seconds for desktop layout
        page.wait_for_timeout(5000)

        # Verify homepage is visible
        assert page.locator("header").is_visible()
        assert page.locator("#products").is_visible()

        # Open website at mobile size
        page.set_viewport_size({"width": 375, "height": 667})
        page.reload()

        # Wait 5 seconds for mobile layout
        page.wait_for_timeout(5000)

        # Verify content remains usable on mobile
        assert page.locator("header").is_visible()
        assert page.locator("#products").is_visible()

        browser.close()