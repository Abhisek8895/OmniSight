
import base64
import mimetypes
import time
from pathlib import Path

from groq import Groq

from config import (
    GROQ_API_KEY,
    MODEL_NAME,
    MAX_COMPLETION_TOKENS,
    TEMPERATURE
)


# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)


def encode_image(image_path):
    """Convert an image into Base64 format."""

    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    mime_type, _ = mimetypes.guess_type(str(image_path))

    if not mime_type or not mime_type.startswith("image/"):
        raise ValueError("Unsupported image format")

    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(
            image_file.read()
        ).decode("utf-8")

    return f"data:{mime_type};base64,{image_data}"


def analyze_screenshot(image_path, method, defect):
    """Analyze a screenshot and measure VLM performance."""

    print(f"\nAnalyzing: {method}")

    image_url = encode_image(image_path)

    prompt = f"""
You are a UI defect detection expert.

Analyze the provided website screenshot.

Expected defect:
{defect}

Identify whether the expected defect is visible in the screenshot.

Return your response in this format:

DEFECT_DETECTED: YES or NO
OBSERVATION: Short explanation
CONFIDENCE: HIGH, MEDIUM, or LOW

Do not claim that a defect is fixed unless the screenshot
provides clear evidence.
"""

    start_time = time.perf_counter()

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    }
                ]
            }
        ],
        temperature=TEMPERATURE,
        max_tokens=MAX_COMPLETION_TOKENS
    )

    end_time = time.perf_counter()

    # Extract VLM response
    result_text = response.choices[0].message.content or ""

    # Extract token usage
    usage = response.usage

    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0
    total_tokens = usage.total_tokens if usage else 0

    # Store performance information
    result = {
        "method": method,
        "image": str(image_path),
        "response_time": round(end_time - start_time, 3),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "response": result_text
    }

    print(f"Response time: {result['response_time']} seconds")
    print(f"Total tokens: {total_tokens}")
    print("VLM analysis completed.")

    return result
