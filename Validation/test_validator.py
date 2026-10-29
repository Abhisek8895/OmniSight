from code_validator import validate_code


def test_valid_css():
    result = validate_code(
        ".checkout-button { margin-bottom: 20px; }",
        "css"
    )

    assert result["valid"] is True


def test_valid_react():
    result = validate_code(
        "function Button() { return <button>Checkout</button>; }",
        "react"
    )

    assert result["valid"] is True


def test_empty_code():
    result = validate_code("", "css")

    assert result["valid"] is False


def test_unsupported_type():
    result = validate_code("print('hello')", "python")

    assert result["valid"] is False


def test_code_too_short():
    result = validate_code("abc", "css")

    assert result["valid"] is False