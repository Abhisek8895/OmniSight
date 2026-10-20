from playwright.sync_api import sync_playwright


def test_category_filter():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Open website
        page.goto("http://localhost:8000/Mock-Website")

        # Go to Products
        page.get_by_role("link", name="Products", exact=True).click()

        # Select Audio category
        page.get_by_role("button", name="Audio", exact=True).click()

        # Verify only audio products are displayed
        products = page.locator("#product-grid article")
        assert products.count() == 3

        # Verify the displayed products
        names = products.locator("h3").all_inner_texts()
        assert set(names) == {
            "Wireless Headphones",
            "Bluetooth Speaker",
            "True Wireless Earbuds"
        }

        browser.close()