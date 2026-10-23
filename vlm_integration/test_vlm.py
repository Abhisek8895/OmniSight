
# ==================================================
# SECTION 1: CONFIGURATION
# ==================================================

import os
import logging
from pathlib import Path

from dotenv import load_dotenv

# Load variables from the .env file
load_dotenv()

# Read the Groq API key
API_KEY = os.getenv("GROQ_API_KEY")

# Model selected for VLM integration
MODEL_NAME = os.getenv(
    "GROQ_MODEL",
    "qwen/qwen3.8-27b"
)

# Current project folder
PROJECT_DIR = Path(__file__).resolve().parent

# Screenshot path
SCREENSHOT_PATH = PROJECT_DIR / "screenshot.png"

# Folder to store analysis reports
OUTPUT_DIR = PROJECT_DIR / "outputs"

# Create the output folder if it does not exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ==================================================
# SECTION 2: LOGGING CONFIGURATION
# ==================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger("OmniSight-VLM")


# ==================================================
# SECTION 3: CHECK API CONFIGURATION
# ==================================================

def check_api_key():
    """Check whether the Groq API key is configured."""

    if not API_KEY:
        logger.error(
            "GROQ_API_KEY is missing from your .env file."
        )
        return False

    logger.info("Groq API key configuration found.")
    return True


# ==================================================
# TEST PART 1
# ==================================================

if __name__ == "__main__":
    print("\nOmniSight - VLM Setup")
    print("---------------------")

    if check_api_key():
        print("Part 1 completed successfully!")
    else:
        print("Please configure your Groq API key.")



# ==================================================
# SECTION 4: VALIDATE SCREENSHOT
# ==================================================

def validate_screenshot(image_path):
    """Check whether the screenshot exists and is valid."""

    if not image_path.exists():
        logger.error(f"Screenshot not found: {image_path}")
        logger.info("Save your website screenshot as screenshot.png")
        return False

    if not image_path.is_file():
        logger.error("The screenshot path is not a file.")
        return False

    supported_formats = {".png", ".jpg", ".jpeg", ".webp"}

    if image_path.suffix.lower() not in supported_formats:
        logger.error("Unsupported screenshot format.")
        return False

    if image_path.stat().st_size == 0:
        logger.error("The screenshot file is empty.")
        return False

    logger.info("Screenshot validation successful.")
    return True


# ==================================================
# SECTION 5: CONVERT SCREENSHOT TO BASE64
# ==================================================

import base64


def encode_image(image_path):
    """Read the image and convert it to Base64."""

    try:
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(
                image_file.read()
            ).decode("utf-8")

        logger.info("Screenshot converted to Base64.")
        return encoded_image

    except OSError as error:
        logger.error(f"Unable to read screenshot: {error}")
        return None


# ==================================================
# SECTION 6: IDENTIFY IMAGE MIME TYPE
# ==================================================

def get_image_mime_type(image_path):
    """Identify the image format for the API request."""

    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }

    mime_type = mime_types.get(image_path.suffix.lower())

    if mime_type is None:
        logger.error("Could not identify the image format.")
    else:
        logger.info(f"Image format identified: {mime_type}")

    return mime_type


# ==================================================
# TEST PART 2
# ==================================================

if __name__ == "__main__":
    print("\nOmniSight - Part 2: Image Preparation")
    print("-------------------------------------")

    if validate_screenshot(SCREENSHOT_PATH):
        image_data = encode_image(SCREENSHOT_PATH)
        image_type = get_image_mime_type(SCREENSHOT_PATH)

        if image_data and image_type:
            print("Part 2 completed successfully!")
            print(f"Image format: {image_type}")
            print(f"Base64 characters: {len(image_data)}")
        else:
            print("Image preparation failed.")
    else:
        print("Please check your screenshot file.")
