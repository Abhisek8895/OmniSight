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
