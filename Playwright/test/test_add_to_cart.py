from playwright.sync_api import sync_playwright


def test_add_to_cart():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Open website
        page.goto("http://localhost:8000/Mock-Website")

        # Go to Products
        page.get_by_role("link", name="Products", exact=True).click()

        # Add the first product to cart
        product = page.locator("#product-grid article").first
        product.locator("button").click()

        # Verify cart count increased to 1
        assert page.locator("#cart-count").inner_text() == "1"

        browser.close()