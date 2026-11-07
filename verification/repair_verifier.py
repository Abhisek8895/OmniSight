import argparse
import base64
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / "vlm_integration" / ".env"
DEFAULT_SCREENSHOT = PROJECT_ROOT / "verification" / "post_fix_screenshot.png"
RESULTS_DIR = PROJECT_ROOT / "verification" / "verification_results"

load_dotenv(ENV_PATH)

API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("OmniSight-Repair-Verification")


def validate_screenshot(image_path):
    """Check that the post-fix screenshot exists and has a supported format."""
    if not image_path.exists() or not image_path.is_file():
        raise FileNotFoundError(f"Screenshot not found: {image_path}")

    supported_formats = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }

    mime_type = supported_formats.get(image_path.suffix.lower())
    if mime_type is None:
        raise ValueError("Supported screenshot formats: PNG, JPG, JPEG, WEBP.")

    if image_path.stat().st_size == 0:
        raise ValueError("The screenshot file is empty.")

    return mime_type


def encode_screenshot(image_path):
    """Encode the screenshot for the Groq vision request."""
    with image_path.open("rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def build_verification_prompt(defect_description):
    """Create a prompt focused only on verifying the original defect."""
    return f"""
You are the UI repair verification assistant for the OmniSight project.

The original UI defect was:
{defect_description}

You are reviewing a screenshot captured AFTER a proposed fix was applied.

Verify whether the original defect is visibly corrected.

Rules:
- Inspect the supplied screenshot carefully.
- Focus on the original defect, not unrelated design preferences.
- Do not assume that a fix worked just because CSS was generated.
- Do not claim hidden functionality works based only on a screenshot.
- If the relevant element or area cannot be seen clearly, use INCONCLUSIVE.
- Use FIXED only when the screenshot provides visible evidence that the
  original visual defect is corrected.
- Use NOT_FIXED when the original visual defect is still visible.
- Return valid JSON only. Do not use Markdown fences.

Use exactly this JSON structure:
{{
  "status": "FIXED, NOT_FIXED, or INCONCLUSIVE",
  "confidence": "HIGH, MEDIUM, or LOW",
  "defect": "Short description of the original defect",
  "evidence": "What is visibly present or absent in the screenshot",
  "reason": "Why this status was selected"
}}
""".strip()


def parse_verification_response(response_text):
    """Extract and validate the JSON returned by the VLM."""
    text = response_text.strip()

    # Remove optional Markdown code fences.
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)

    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise ValueError("The VLM did not return valid JSON.")
        result = json.loads(match.group(0))

    allowed_statuses = {"FIXED", "NOT_FIXED", "INCONCLUSIVE"}
    status = str(result.get("status", "")).strip().upper()

    if status not in allowed_statuses:
        raise ValueError(f"Unexpected verification status: {status}")

    confidence = str(result.get("confidence", "LOW")).strip().upper()
    if confidence not in {"HIGH", "MEDIUM", "LOW"}:
        confidence = "LOW"

    return {
        "status": status,
        "confidence": confidence,
        "defect": str(result.get("defect", "")),
        "evidence": str(result.get("evidence", "")),
        "reason": str(result.get("reason", "")),
    }


def verify_repair(client, screenshot_path, defect_description):
    """Send the post-fix screenshot and defect context to the VLM."""
    mime_type = validate_screenshot(screenshot_path)
    encoded_image = encode_screenshot(screenshot_path)
    image_data_url = f"data:{mime_type};base64,{encoded_image}"

    prompt = build_verification_prompt(defect_description)

    logger.info("Sending post-fix screenshot to %s...", MODEL_NAME)

    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a careful visual UI repair verifier. "
                    "Judge only what is supported by the screenshot."
                ),
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_data_url},
                    },
                ],
            },
        ],
        temperature=0.1,
        max_completion_tokens=700,
    )

    response_text = completion.choices[0].message.content
    if not response_text:
        raise ValueError("The VLM returned an empty response.")

    return parse_verification_response(response_text), response_text


def save_verification_report(result, screenshot_path, defect_description, raw_response):
    """Save a timestamped JSON verification report."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    report = {
        "created_at": timestamp,
        "model": MODEL_NAME,
        "screenshot": str(screenshot_path),
        "original_defect": defect_description,
        "verification": result,
        "raw_vlm_response": raw_response,
    }

    report_path = RESULTS_DIR / f"verification_{timestamp}.json"
    report_path.write_text(
        json.dumps(report, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )

    return report_path


def main():
    parser = argparse.ArgumentParser(
        description="Verify an applied UI fix using the OmniSight VLM."
    )
    parser.add_argument(
        "--screenshot",
        type=Path,
        default=DEFAULT_SCREENSHOT,
        help="Path to the screenshot captured after applying the fix.",
    )
    parser.add_argument(
        "--defect",
        required=True,
        help="Description of the original UI defect.",
    )
    args = parser.parse_args()

    if not API_KEY:
        raise ValueError(
            f"GROQ_API_KEY was not found. Check your environment file: {ENV_PATH}"
        )

    client = Groq(api_key=API_KEY)

    result, raw_response = verify_repair(
        client,
        args.screenshot.resolve(),
        args.defect,
    )

    report_path = save_verification_report(
        result,
        args.screenshot.resolve(),
        args.defect,
        raw_response,
    )

    print("\n===== OmniSight Repair Verification =====")
    print(f"Status     : {result['status']}")
    print(f"Confidence : {result['confidence']}")
    print(f"Evidence   : {result['evidence']}")
    print(f"Reason     : {result['reason']}")
    print(f"\nReport saved: {report_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        logger.error("Repair verification failed: %s", error)
        raise SystemExit(1)
