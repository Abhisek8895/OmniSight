import json

from code_validator import validate_code


def prepare_fix(fix_data):
    code = fix_data.get("code")
    code_type = fix_data.get("code_type")

    validation = validate_code(code, code_type)

    if not validation["valid"]:
        return {
            "status": "rejected",
            "code": None,
            "code_type": code_type,
            "reason": validation["reason"]
        }

    return {
        "status": "validated",
        "code": code,
        "code_type": code_type,
        "reason": validation["reason"]
    }


with open("sample_fix.json", "r") as file:
    fix_data = json.load(file)


result = prepare_fix(fix_data)

print(json.dumps(result, indent=4))