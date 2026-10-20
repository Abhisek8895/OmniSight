from playwright.sync_api import sync_playwright


def test_remove_product():
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

        # Verify product is in cart
        assert page.locator(".cart-item").count() == 1
        assert page.locator("#cart-count").inner_text() == "1"

        # Remove product
        page.locator('.cart-item button[data-act="remove"]').click()

        # Verify product was removed
        assert page.locator(".cart-item").count() == 0
        assert page.locator("#cart-count").inner_text() == "0"
        assert page.locator("#cart").get_by_text(
            "Your cart is empty. Add a product above to get started."
        ).is_visible()

        browser.close()