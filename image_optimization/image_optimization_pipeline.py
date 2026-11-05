
from pathlib import Path

from screenshot_chunking import (
    chunk_screenshot
)


def optimize_screenshot(
    screenshot_path,
    coordinates=None,
    output_dir="optimized_images"
):
    """
    Select the appropriate image optimization method.

    Coordinates available: Cropping (pending integration).
    Coordinates unavailable: Screenshot chunking.
    """

    screenshot_path = Path(screenshot_path)

    if not screenshot_path.is_file():
        raise FileNotFoundError(
            f"Screenshot not found: {screenshot_path}"
        )

    # Select cropping when coordinates are available
    if coordinates is not None:

        raise NotImplementedError(
            "Screenshot cropping module is pending integration."
        )

    # Use chunking when coordinates are unavailable
    chunks = chunk_screenshot(
        screenshot_path=str(screenshot_path),
        output_dir=output_dir,
        chunk_width=500,
        chunk_height=500,
        overlap=50
    )

    return {
        "status": "success",
        "method": "chunking",
        "total_images": len(chunks),
        "images": [
            {
                "path": str(Path(output_dir) / chunk["filename"]),
                "coordinates": chunk["coordinates"]
            }
            for chunk in chunks
        ]
    }


if __name__ == "__main__":

    result = optimize_screenshot(
        screenshot_path="../screenshots/updated_screenshot.png"
    )

    print(result)
