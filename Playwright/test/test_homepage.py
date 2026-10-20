from playwright.sync_api import sync_playwright


def test_website_loading():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Open website
        page.goto("http://localhost:8000/Mock-Website")

        # Verify homepage loaded
        assert page.title() != ""
        assert page.locator("header").is_visible()

        browser.close()