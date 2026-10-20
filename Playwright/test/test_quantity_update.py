from playwright.sync_api import sync_playwright


def test_quantity_update():
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

        # Get the cart item
        cart_item = page.locator(".cart-item").first

        # Verify initial quantity
        assert cart_item.locator(".qty").inner_text() == "1"

        # Increase quantity
        cart_item.locator('button[data-act="inc"]').click()

        # Verify quantity increased
        assert cart_item.locator(".qty").inner_text() == "2"

        # Verify cart count also increased
        assert page.locator("#cart-count").inner_text() == "2"

        browser.close()