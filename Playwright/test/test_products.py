from playwright.sync_api import sync_playwright


def test_product_display():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Open website
        page.goto("http://localhost:8000/Mock-Website")

        # Go to Products
        page.get_by_role("link", name="Products", exact=True).click()

        # Verify all six products are displayed
        products = page.locator("#product-grid article")
        assert products.count() == 6

        browser.close()