from playwright.sync_api import sync_playwright


def test_invalid_checkout():
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

        # Submit invalid checkout details
        page.locator("#name").fill("")
        page.locator("#email").fill("invalid-email")
        page.locator("#address").fill("short")

        page.locator("button.place").click()

        # Verify validation errors are displayed
        assert page.locator('small.error[data-for="name"]').inner_text() != ""
        assert page.locator('small.error[data-for="email"]').inner_text() != ""
        assert page.locator('small.error[data-for="address"]').inner_text() != ""
        
        browser.close()