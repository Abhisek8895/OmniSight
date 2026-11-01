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
    Try to apply and verify a generated fix.
    """

    for attempt in range(1, MAX_RETRIES + 1):
        print(f"Repair attempt {attempt}")

        repaired_code = apply_fix(css_code, fixed_code)

        validation_result = verify_fix(
            repaired_code,
            code_type
        )

        if validation_result["valid"]:
            return {
                "status": "success",
                "attempt": attempt,
                "repaired_code": repaired_code,
                "validation": validation_result
            }

    return {
        "status": "failed",
        "attempts": MAX_RETRIES,
        "repaired_code": None,
        "validation": validation_result
    }