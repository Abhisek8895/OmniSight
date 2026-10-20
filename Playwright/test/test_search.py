from playwright.sync_api import sync_playwright


def test_product_search():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Open website
        page.goto("http://localhost:8000/Mock-Website")

        # Go to Products
        page.get_by_role("link", name="Products", exact=True).click()

        # Search for Smart Watch
        page.locator("#search").fill("Smart Watch")

        # Verify matching product appears
        products = page.locator("#product-grid article")
        assert products.count() == 1
        assert products.first.locator("h3").inner_text() == "Smart Watch"

        browser.close()