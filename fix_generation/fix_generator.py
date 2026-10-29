import os
import re
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv
load_dotenv(
    Path(__file__).resolve().parent.parent
    / "vlm_integration"
    / ".env"
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = PROJECT_ROOT / "vlm_integration" / "outputs" / "vlm_analysis.txt"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "generated_fixes"

MODEL_NAME = "openai/gpt-oss-120b"


def generate_fix(report_text):
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set.")

    client = Groq(api_key=api_key)

    prompt = f"""
You are a frontend developer helping fix a UI defect.

Analyze this VLM report:
{report_text[:12000]}

The report describes a missing checkout button and a possible layout overflow.

Generate a proposed CSS fix for the missing checkout button.
If CSS alone cannot fix it because the HTML button is absent, provide a small
HTML button example instead.

Return only one fenced code block with the correct language label, either
css or html. Do not include explanations outside the code block.
Do not claim the fix is verified.
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "Generate minimal, safe, proposed frontend code fixes."
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=1200
    )

    return response.choices[0].message.content or ""


def main():
    if not REPORT_PATH.exists():
        print(f"ERROR: VLM report not found: {REPORT_PATH}")
        return

    full_report = REPORT_PATH.read_text(
        encoding="utf-8-sig",
        errors="replace"
    )

    report_text = full_report[:5000]

    print("Generating a proposed UI fix with Groq...")

    try:
        ai_response = generate_fix(report_text)
    except Exception as error:
        print(f"Fix generation failed: {error}")
        return

    # Keep the remaining existing code unchanged.

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    response_path = OUTPUT_DIR / "ai_fix_response.txt"
    response_path.write_text(ai_response, encoding="utf-8")

    print(f"AI response saved: {response_path}")

    from code_extractor import extract_code_blocks, save_report

    blocks = extract_code_blocks(ai_response)
    result = save_report(blocks)

    print(f"Code blocks extracted: {result['blocks_extracted']}")
    print(f"Extraction status: {result['status']}")

    if not blocks:
        print("No supported code block was returned. Check ai_fix_response.txt.")
    else:
        for item in result["files"]:
            print(f"Proposed fix saved: {item['path']}")


if __name__ == "__main__":
    main()
