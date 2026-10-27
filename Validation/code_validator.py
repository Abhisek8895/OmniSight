SUPPORTED_TYPES = ["css", "react"]
MAX_CODE_LENGTH = 5000


def validate_code(code, code_type):
    if not code:
        return {
            "valid": False,
            "reason": "No code provided"
        }

    if code_type not in SUPPORTED_TYPES:
        return {
            "valid": False,
            "reason": f"Unsupported code type: {code_type}"
        }

    if len(code) > MAX_CODE_LENGTH:
        return {
            "valid": False,
            "reason": "Code exceeds maximum allowed length"
        }

    return {
        "valid": True,
        "reason": "Basic validation passed"
    }