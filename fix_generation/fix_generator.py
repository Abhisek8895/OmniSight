# import os
# import re
# from pathlib import Path
# from groq import Groq
# from dotenv import load_dotenv
# load_dotenv(
#     Path(__file__).resolve().parent.parent
#     / "vlm_integration"
#     / ".env"
# )

# PROJECT_ROOT = Path(__file__).resolve().parent.parent
# REPORT_PATH = PROJECT_ROOT / "vlm_integration" / "outputs" / "vlm_analysis.txt"
# OUTPUT_DIR = PROJECT_ROOT / "outputs" / "generated_fixes"

# MODEL_NAME = "openai/gpt-oss-120b"


# def generate_fix(report_text):
#     api_key = os.getenv("GROQ_API_KEY")

#     if not api_key:
#         raise ValueError("GROQ_API_KEY environment variable is not set.")

#     client = Groq(api_key=api_key)

#     prompt = f"""
# You are a frontend developer helping fix a UI defect.

# Analyze this VLM report:
# {report_text[:12000]}

# The report describes a missing checkout button and a possible layout overflow.

# Generate a proposed CSS fix for the missing checkout button.
# If CSS alone cannot fix it because the HTML button is absent, provide a small
# HTML button example instead.

# Return only one fenced code block with the correct language label, either
# css or html. Do not include explanations outside the code block.
# Do not claim the fix is verified.
# """

#     response = client.chat.completions.create(
#         model=MODEL_NAME,
#         messages=[
#             {
#                 "role": "system",
#                 "content": "Generate minimal, safe, proposed frontend code fixes."
#             },
#             {"role": "user", "content": prompt}
#         ],
#         temperature=0.2,
#         max_tokens=1200
#     )

#     return response.choices[0].message.content or ""


# def main():
#     if not REPORT_PATH.exists():
#         print(f"ERROR: VLM report not found: {REPORT_PATH}")
#         return

#     full_report = REPORT_PATH.read_text(
#         encoding="utf-8-sig",
#         errors="replace"
#     )

#     report_text = full_report[:5000]

#     print("Generating a proposed UI fix with Groq...")

#     try:
#         ai_response = generate_fix(report_text)
#     except Exception as error:
#         print(f"Fix generation failed: {error}")
#         return

#     # Keep the remaining existing code unchanged.

#     OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

#     response_path = OUTPUT_DIR / "ai_fix_response.txt"
#     response_path.write_text(ai_response, encoding="utf-8")

#     print(f"AI response saved: {response_path}")

#     from code_extractor import extract_code_blocks, save_report

#     blocks = extract_code_blocks(ai_response)
#     result = save_report(blocks)

#     print(f"Code blocks extracted: {result['blocks_extracted']}")
#     print(f"Extraction status: {result['status']}")

#     if not blocks:
#         print("No supported code block was returned. Check ai_fix_response.txt.")
#     else:
#         for item in result["files"]:
#             print(f"Proposed fix saved: {item['path']}")


# if __name__ == "__main__":
#     main()


import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

PROJECT_ROOT = Path(__file__).resolve().parent.parent

ENV_PATH = PROJECT_ROOT / "vlm_integration" / ".env"

load_dotenv(ENV_PATH)

MODEL_NAME = os.getenv(
    "GROQ_FIX_MODEL",
    "openai/gpt-oss-120b"
)


def generate_fix(report_text: str) -> str:
    """Generate a CSS repair from the actual detected defect and DOM context."""

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            f"GROQ_API_KEY is not configured. Check {ENV_PATH}"
        )

    client = Groq(api_key=api_key)

    prompt = f"""
You are a careful frontend engineer working on the OmniSight UI repair system.

Use the defect report and DOM context below to propose the smallest safe CSS-only
repair. The report may describe any UI defect; do not assume it is a checkout
button problem.

Requirements:
- Return exactly one fenced code block labelled css.
- Prefer the supplied target selector when it is valid and relevant.
- Return complete CSS rules with selectors, not HTML or JavaScript.
- Do not invent DOM elements or selectors that are not supported by the report.
- Preserve the existing design and unrelated layout.
- Make the smallest change that addresses the described defect.
- Do not claim that the fix has been applied or verified.
- If the report is insufficient for a safe CSS repair, return an empty CSS block.

Defect report:
{report_text[:12000]}
""".strip()

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "Generate minimal, safe, evidence-based CSS repairs."
                ),
            },
            {
                "role": "user",
                "content": prompt
            },
        ],
        temperature=0.2,
        max_tokens=1200,
    )

    return response.choices[0].message.content or ""