from playwright.sync_api import sync_playwright


def test_new_order():
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

        # Proceed to checkout
        page.locator("#checkout-button").click()

        # Fill valid checkout details
        page.locator("#name").fill("Abhisek Mishra")
        page.locator("#email").fill("abhisek@example.com")
        page.locator("#address").fill("Bhubaneswar, Odisha")

        # Place order
        page.locator("button.place").click()

        # Verify order confirmation
        page.locator("#confirmation h2").wait_for()
        assert page.locator("#confirmation h2").inner_text() == \
            "Order Placed Successfully!"

        # Start a new order
        page.get_by_role("button", name="Start a New Order").click()

        # Verify checkout is available again
        assert page.locator("#checkout-form").is_visible()

        browser.close()