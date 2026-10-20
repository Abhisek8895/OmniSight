from playwright.sync_api import sync_playwright


def test_price_sorting():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Open website
        page.goto("http://localhost:8000/Mock-Website")

        # Go to Products
        page.get_by_role("link", name="Products", exact=True).click()

        # Select low to high price sorting
        page.locator("#sort").select_option(label="Price: low to high")
        
        # Get displayed product prices
        products = page.locator("#product-grid article")
        prices = []

        for i in range(products.count()):
            price_text = products.nth(i).locator("p").inner_text()
            price = int(price_text.replace("Price: ₹", "").replace(",", ""))
            prices.append(price)

        # Verify ascending order
        assert prices == sorted(prices)

        browser.close()