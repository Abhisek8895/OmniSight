import re
import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = PROJECT_ROOT / "vlm_integration" / "outputs" / "vlm_analysis.txt"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "generated_fixes"

SUPPORTED_LANGUAGES = {
    "html": ".html",
    "css": ".css",
    "javascript": ".js",
    "js": ".js",
    "python": ".py",
    "py": ".py",
}


def extract_code_blocks(response):
    pattern = r"```([a-zA-Z0-9_+-]*)\s*\n(.*?)```"
    matches = re.findall(pattern, response, re.DOTALL)
    extracted = []

    for language, code in matches:
        language = language.strip().lower()

        if language in SUPPORTED_LANGUAGES and code.strip():
            extracted.append({
                "language": language,
                "extension": SUPPORTED_LANGUAGES[language],
                "code": code.strip()
            })

    return extracted


def save_report(blocks):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved_files = []

    for index, block in enumerate(blocks, start=1):
        filename = f"proposed_fix_{timestamp}_{index}{block['extension']}"
        output_path = OUTPUT_DIR / filename
        output_path.write_text(block["code"] + "\n", encoding="utf-8")

        saved_files.append({
            "file": filename,
            "language": block["language"],
            "path": str(output_path)
        })

    report = {
        "created_at": timestamp,
        "source_report": str(REPORT_PATH),
        "blocks_extracted": len(blocks),
        "files": saved_files,
        "status": "success" if blocks else "no_code_found"
    }

    report_path = OUTPUT_DIR / f"extraction_{timestamp}.json"
    report_path.write_text(json.dumps(report, indent=4), encoding="utf-8")

    return report


def main():
    if not REPORT_PATH.exists():
        print(f"ERROR: VLM report not found: {REPORT_PATH}")
        return

    try:
        response = REPORT_PATH.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        response = REPORT_PATH.read_text(encoding="utf-16")
    blocks = extract_code_blocks(response)
    report = save_report(blocks)

    print("Code extraction completed.")
    print(f"Source: {REPORT_PATH}")
    print(f"Code blocks extracted: {report['blocks_extracted']}")
    print(f"Status: {report['status']}")

    for item in report["files"]:
        print(f"Saved proposed fix: {item['path']}")

    if not blocks:
        print("No supported code blocks found in the VLM report.")
        print("This is expected if the report contains suggestions but no fenced code.")


if __name__ == "__main__":
    main()