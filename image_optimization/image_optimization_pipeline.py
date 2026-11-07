from pathlib import Path

from .screenshot_chunking import chunk_screenshot
from .screenshot_cropping import crop_image


def optimize_screenshot(
    screenshot_path,
    coordinates=None,
    output_dir="optimized_images"
):
    """
    Select the appropriate image optimization method.

    Coordinates available: Screenshot cropping.
    Coordinates unavailable: Screenshot chunking.
    """

    screenshot_path = Path(screenshot_path)
    output_dir = Path(output_dir)

    # Validate screenshot
    if not screenshot_path.is_file():
        raise FileNotFoundError(
            f"Screenshot not found: {screenshot_path}"
        )

    # Route 1: Crop when defect coordinates are available
    if coordinates is not None:

        try:
            result = crop_image(
                image_path=str(screenshot_path),
                coordinates=coordinates,
                padding=20,
                output_dir=str(output_dir)
            )

            image_path = output_dir / result["filename"]

            if not image_path.is_file():
                raise FileNotFoundError(
                    f"Cropped image not found: {image_path}"
                )

            images = [{
                "path": str(image_path),
                "coordinates": result["coordinates"]
            }]

            return {
                "status": "success",
                "method": "cropping",
                "total_images": len(images),
                "images": images
            }

        except Exception as error:
            raise RuntimeError(
                f"Screenshot cropping failed: {error}"
            ) from error

    # Route 2: Use chunking when coordinates are unavailable
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

    # Test cropping by supplying coordinates
    result = optimize_screenshot(
        screenshot_path="screenshots/updated_screenshot.png",
        coordinates=(500, 300, 800, 400)
    )

    print(result)