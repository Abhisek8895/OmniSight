from playwright.sync_api import sync_playwright


def test_empty_cart_checkout():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Open website
        page.goto("http://localhost:8000/Mock-Website")

        # Click Place Demo Order with an empty cart
        page.locator("button.place").click()

        # Verify empty cart message
        assert page.locator("#toast").inner_text() == \
            "Add a product to your cart before checkout."

        browser.close()