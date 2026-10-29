SUPPORTED_TYPES = ["css", "react"]

MIN_CODE_LENGTH = 10
MAX_CODE_LENGTH = 5000


def validate_code(code, code_type):

    # Check whether code exists
    if not code or not code.strip():
        return {
            "valid": False,
            "reason": "No code provided"
        }

    # Check whether code type is supported
    if code_type not in SUPPORTED_TYPES:
        return {
            "valid": False,
            "reason": f"Unsupported code type: {code_type}"
        }

    # Check minimum length
    if len(code.strip()) < MIN_CODE_LENGTH:
        return {
            "valid": False,
            "reason": "Code is too short"
        }

    # Check maximum length
    if len(code) > MAX_CODE_LENGTH:
        return {
            "valid": False,
            "reason": "Code exceeds maximum allowed length"
        }

    return {
        "valid": True,
        "reason": "Basic validation passed"
    }