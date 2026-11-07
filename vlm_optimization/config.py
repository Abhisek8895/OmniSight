import os
from pathlib import Path
from dotenv import load_dotenv

# Get the main OmniSight directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load the common environment file
load_dotenv(PROJECT_ROOT / ".env")

# Groq API configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Qwen VLM model
MODEL_NAME = "qwen/qwen3.8-27b"

# Model settings
MAX_COMPLETION_TOKENS = 1200
TEMPERATURE = 0

# Image and output directories
BASE_DIR = Path(__file__).resolve().parent
TEST_IMAGES_DIR = BASE_DIR / "test_images"
OUTPUT_DIR = BASE_DIR / "outputs"

# Check API key
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in common .env file")
