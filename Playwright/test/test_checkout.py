from playwright.sync_api import sync_playwright


def test_checkout_flow():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # 1. Open website
        page.goto("http://localhost:8000/Mock-Website")

        # 2. Go to Products
        page.get_by_role("link", name="Products", exact=True).click()

        # 3. Add first product to cart
        product = page.locator("#product-grid article").first
        product.locator("button").click()

        # 4. Verify product was added to cart
        page.locator("#cart-count").wait_for()
        assert page.locator("#cart-count").inner_text() == "1"

        # 5. Proceed to Checkout
        page.locator("#checkout-button").click()

        # 6. Fill checkout form
        page.locator("#name").fill("Abhisek Mishra")
        page.locator("#email").fill("abhisek@example.com")
        page.locator("#address").fill("Bhubaneswar, Odisha")

        # 7. Place order
        page.locator("button.place").click()

        # 8. Verify order confirmation
        page.locator("#confirmation").wait_for()
        assert page.locator("#confirmation h2").inner_text() == "Order Placed Successfully!"

        # 9. Verify order number was generated
        order_id = page.locator(".order-id").inner_text()
        assert order_id.startswith("OS-")

        print("Order created successfully:", order_id)

        browser.close()