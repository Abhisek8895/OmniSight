import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright


# Find the main project folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Website and output locations
WEBSITE_PATH = PROJECT_ROOT / "mock_website" / "index.html"
GENERATED_FIXES_DIR = PROJECT_ROOT / "outputs" / "generated_fixes"
OUTPUT_DIR = PROJECT_ROOT / "css_application" / "outputs"

# Map AI-generated selectors to actual website selectors
SELECTOR_MAPPING = {
    ".checkout-button": "#checkout-form .place",
    ".checkout-section": ".checkout-layout"
}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger(__name__)


def get_latest_css():
    """Find the latest generated CSS fix."""

    css_files = list(GENERATED_FIXES_DIR.glob("proposed_fix_*.css"))

    if not css_files:
        raise FileNotFoundError("No generated CSS files found.")

    return max(css_files, key=lambda file: file.stat().st_mtime)


def read_css(css_path):
    """Read the generated CSS file."""

    if not css_path.exists():
        raise FileNotFoundError(f"CSS file not found: {css_path}")

    css_content = css_path.read_text(
        encoding="utf-8-sig"
    )

    if not css_content.strip():
        raise ValueError("Generated CSS file is empty.")

    return css_content


def map_selectors(css_content):
    """Replace AI-generated selectors with actual website selectors."""

    mapped_details = []

    for original, actual in SELECTOR_MAPPING.items():

        if original in css_content:

            css_content = css_content.replace(original, actual)

            mapped_details.append({
                "original_selector": original,
                "actual_selector": actual
            })

            logger.info(
                "Mapped selector: %s -> %s",
                original,
                actual
            )

    return css_content, mapped_details


def apply_css(css_path, headless=True):
    """Apply the generated CSS fix using Playwright."""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    screenshot_path = OUTPUT_DIR / f"post_application_{timestamp}.png"
    report_path = OUTPUT_DIR / f"application_{timestamp}.json"

    report = {
        "created_at": timestamp,
        "source_css": str(css_path),
        "website": str(WEBSITE_PATH),
        "status": "failed",
        "mapped_selectors": [],
        "unmatched_selectors": [],
        "target_found": False,
        "before_display": None,
        "after_display": None,
        "screenshot": None,
        "error": None
    }

    try:
        # Read and prepare the generated CSS
        css_content = read_css(css_path)

        css_content, mapped_details = map_selectors(css_content)

        report["mapped_selectors"] = mapped_details

        with sync_playwright() as playwright:

            # Launch Chromium browser
            browser = playwright.chromium.launch(
                headless=headless
            )

            page = browser.new_page(
                viewport={"width": 1366, "height": 768}
            )

            # Open the mock website
            page.goto(
                WEBSITE_PATH.as_uri(),
                wait_until="load"
            )

            page.wait_for_timeout(1000)

            # Check the actual checkout button
            checkout_button =  page.locator("#checkout-form button.place").first

            if checkout_button.count() == 0:
                raise ValueError(
                    "Checkout button was not found on the website."
                )

            report["target_found"] = True

            # Check button visibility before applying the fix
            before_display = checkout_button.evaluate(
                "(element) => getComputedStyle(element).display"
            )

            report["before_display"] = before_display

            logger.info(
                "Checkout button display before fix: %s",
                before_display
            )

            # Check that mapped selectors exist
            for item in mapped_details:

                actual_selector = item["actual_selector"]

                if page.locator(actual_selector).count() == 0:
                    raise ValueError(
                        f"Mapped selector not found: {actual_selector}"
                    )

            # Apply the generated CSS to the website
            page.add_style_tag(content=css_content)

            page.wait_for_timeout(500)

            # Check button visibility after applying the fix
            after_display = checkout_button.evaluate(
                "(element) => getComputedStyle(element).display"
            )

            report["after_display"] = after_display

            # Save screenshot after CSS application
            page.screenshot(
                path=str(screenshot_path),
                full_page=True
            )

            report["screenshot"] = str(screenshot_path)

            report["status"] = "success"

            logger.info(
                "Checkout button display after fix: %s",
                after_display
            )

            logger.info("CSS fix applied successfully.")

            browser.close()

    except Exception as error:

        report["error"] = str(error)

        logger.error("CSS application failed: %s", error)

    finally:

        # Save application result as JSON
        report_path.write_text(
            json.dumps(report, indent=4),
            encoding="utf-8"
        )

        logger.info("Application report saved: %s", report_path)

    return report


def main():

    parser = argparse.ArgumentParser(
        description="Apply AI-generated CSS fixes using Playwright."
    )

    parser.add_argument(
        "--css",
        type=str,
        help="Path to the generated CSS file."
    )

    parser.add_argument(
        "--headed",
        action="store_true",
        help="Open the browser visibly."
    )

    args = parser.parse_args()

    try:

        # Use the provided CSS file or find the latest one
        css_path = (
            Path(args.css).resolve()
            if args.css
            else get_latest_css()
        )

        logger.info("Using CSS file: %s", css_path)

        result = apply_css(
            css_path,
            headless=not args.headed
        )

        print("\n========== CSS APPLICATION RESULT ==========")
        print(f"Status: {result['status']}")
        print(f"Target found: {result['target_found']}")
        print(f"Before display: {result['before_display']}")
        print(f"After display: {result['after_display']}")
        print(f"Mapped selectors: {len(result['mapped_selectors'])}")

        if result["error"]:
            print(f"Error: {result['error']}")

    except Exception as error:

        logger.error("Execution failed: %s", error)


if __name__ == "__main__":
    main()
