from playwright.sync_api import sync_playwright


MAX_RETRIES = 3

SUPPORTED_TYPES = ["css", "react"]
MAX_CODE_LENGTH = 5000


def apply_fix(css_code, fixed_code):
    """
    Apply the generated fix to the original CSS code.
    """

    if not fixed_code:
        return css_code

    return fixed_code


def capture_screenshot():
    """
    Open the website and capture a screenshot after applying the fix.
    """

    print("Capturing updated screenshot...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("http://localhost:8000/Mock-Website")

        screenshot_path = "updated_screenshot.png"
        page.screenshot(path=screenshot_path, full_page=True)

        browser.close()

    return screenshot_path

def verify_with_vlm(screenshot):
    """
    Verify whether the UI defect has been fixed.

    This is a placeholder for the actual VLM verification.
    """

    print(f"Sending {screenshot} to VLM for verification...")

    # Placeholder result.
    # This will later come from the actual VLM.
    return {
        "fixed": True,
        "reason": "UI defect appears to be fixed"
    }


def verify_fix(fixed_code, code_type):
    """
    Validate the generated repair code.
    """

    if not fixed_code:
        return {
            "valid": False,
            "reason": "No code provided"
        }

    if not isinstance(fixed_code, str):
        return {
            "valid": False,
            "reason": "Code must be a string"
        }

    if code_type not in SUPPORTED_TYPES:
        return {
            "valid": False,
            "reason": "Unsupported code type"
        }

    if len(fixed_code) > MAX_CODE_LENGTH:
        return {
            "valid": False,
            "reason": "Code exceeds maximum length"
        }

    return {
        "valid": True,
        "reason": "Code passed basic validation"
    }


def self_healing_loop(css_code, fixed_code, code_type):
    """
    Apply a fix, capture a new screenshot, and verify the result.

    The process retries until the defect is fixed or the
    maximum retry limit is reached.
    """

    last_validation = None
    last_verification = None

    for attempt in range(1, MAX_RETRIES + 1):

        print(f"\nRepair attempt {attempt}/{MAX_RETRIES}")

        # Step 1: Apply generated fix
        repaired_code = apply_fix(
            css_code,
            fixed_code
        )

        # Step 2: Validate generated code
        validation_result = verify_fix(
            repaired_code,
            code_type
        )

        last_validation = validation_result

        if not validation_result["valid"]:
            print("Generated code failed validation.")

            continue

        print("Code validation successful.")

        # Step 3: Capture screenshot after applying fix
        screenshot = capture_screenshot()

        # Step 4: Ask VLM whether the defect is fixed
        verification_result = verify_with_vlm(
            screenshot
        )

        last_verification = verification_result

        # Step 5: Stop if defect is fixed
        if verification_result["fixed"]:

            print("UI defect fixed successfully.")

            return {
                "status": "success",
                "attempt": attempt,
                "repaired_code": repaired_code,
                "validation": validation_result,
                "verification": verification_result
            }

        # Step 6: Retry if defect is still present
        print("UI defect still exists. Retrying...")

    # Maximum retry limit reached
    print("Maximum retry limit reached.")

    return {
        "status": "failed",
        "attempts": MAX_RETRIES,
        "repaired_code": None,
        "validation": last_validation,
        "verification": last_verification
    }


if __name__ == "__main__":

    original_code = ".button { width: 100px; }"

    fixed_code = ".button { width: 100%; }"

    result = self_healing_loop(
        original_code,
        fixed_code,
        "css"
    )

    print("\nFinal Result:")
    print(result)