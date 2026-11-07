from pathlib import Path
from PIL import Image


def crop_image(
    image_path,
    coordinates,
    padding=20,
    output_dir="optimized_images"
):
    """
    Crop a UI component from a screenshot using defect coordinates.
    """

    image_path = Path(image_path)
    output_dir = Path(output_dir)

    # Validate screenshot
    if not image_path.is_file():
        raise FileNotFoundError(
            f"Screenshot not found: {image_path}"
        )

    # Validate coordinates
    if not isinstance(coordinates, (tuple, list)) or len(coordinates) != 4:
        raise ValueError(
            "Coordinates must contain x1, y1, x2, y2."
        )

    if not isinstance(padding, int) or padding < 0:
        raise ValueError("Padding must be a non-negative integer.")

    x1, y1, x2, y2 = coordinates

    if not all(isinstance(value, (int, float)) for value in coordinates):
        raise ValueError("Coordinates must be numeric.")

    x1, y1, x2, y2 = map(int, (x1, y1, x2, y2))

    # Open screenshot
    with Image.open(image_path) as image:

        width, height = image.size

        # Apply padding
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(width, x2 + padding)
        y2 = min(height, y2 + padding)

        # Validate crop area
        if x1 >= x2 or y1 >= y2:
            raise ValueError("Invalid cropping coordinates.")

        # Crop image
        cropped = image.crop((x1, y1, x2, y2))

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save cropped image
        output_path = output_dir / "cropped_ui.png"
        cropped.save(output_path)

    print("Cropping completed successfully!")
    print(f"Original size: {width} x {height}")
    print(f"Cropped size: {cropped.size}")
    print(f"Saved: {output_path}")

    return {
        "filename": output_path.name,
        "coordinates": {
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2
        }
    }


if __name__ == "__main__":

    result = crop_image(
        image_path="screenshots/updated_screenshot.png",
        coordinates=(500, 300, 800, 400),
        padding=20
    )

    print(result)