from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    page.goto("http://localhost:8000/Mock-Website")

    print(page.title())
    # Keep the page open for 10 seconds
    page.wait_for_timeout(10000)

    browser.close()