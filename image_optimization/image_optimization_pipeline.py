from pathlib import Path

from .screenshot_chunking import chunk_screenshot


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
    output_dir = Path(output_dir)

    # Validate screenshot
    if not screenshot_path.is_file():
        raise FileNotFoundError(
            f"Screenshot not found: {screenshot_path}"
        )

    # Cropping integration is pending
    if coordinates is not None:
        raise NotImplementedError(
            "Screenshot cropping module is pending integration."
        )

    # Perform screenshot chunking
    try:
        chunks = chunk_screenshot(
            screenshot_path=str(screenshot_path),
            output_dir=str(output_dir),
            chunk_width=500,
            chunk_height=500,
            overlap=50
        )

    except Exception as error:
        raise RuntimeError(
            f"Screenshot chunking failed: {error}"
        ) from error

    # Validate chunking output
    if not isinstance(chunks, list) or not chunks:
        raise RuntimeError(
            "Chunking did not generate any valid images."
        )

    images = []

    for chunk in chunks:

        if not isinstance(chunk, dict):
            raise ValueError("Invalid chunk information returned.")

        if "filename" not in chunk or "coordinates" not in chunk:
            raise ValueError(
                "Chunk information is missing filename or coordinates."
            )

        image_path = output_dir / chunk["filename"]

        if not image_path.is_file():
            raise FileNotFoundError(
                f"Generated chunk not found: {image_path}"
            )

        images.append({
            "path": str(image_path),
            "coordinates": chunk["coordinates"]
        })

    return {
        "status": "success",
        "method": "chunking",
        "total_images": len(images),
        "images": images
    }


if __name__ == "__main__":

    result = optimize_screenshot(
        screenshot_path="screenshots/updated_screenshot.png"
    )

    print(result)