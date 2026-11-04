
from PIL import Image
from pathlib import Path
import json


def generate_positions(length, chunk_size, overlap):
    """Generate starting positions for overlapping image chunks."""

    effective_size = min(length, chunk_size)
    stride = effective_size - overlap

    positions = [0]

    while positions[-1] + effective_size < length:
        next_position = positions[-1] + stride

        if next_position + effective_size >= length:
            next_position = length - effective_size

        if next_position <= positions[-1]:
            break

        positions.append(next_position)

    return positions


def chunk_screenshot(
    screenshot_path,
    output_dir="chunks",
    chunk_width=500,
    chunk_height=500,
    overlap=50
):
    """Divide a screenshot into overlapping image chunks."""

    screenshot_path = Path(screenshot_path)
    output_dir = Path(output_dir)

    # Validate input file
    if not screenshot_path.is_file():
        raise FileNotFoundError(
            f"Screenshot not found: {screenshot_path}"
        )

    # Validate chunk dimensions
    if chunk_width <= 0 or chunk_height <= 0:
        raise ValueError("Chunk dimensions must be positive.")

    if overlap < 0:
        raise ValueError("Overlap cannot be negative.")

    if overlap >= min(chunk_width, chunk_height):
        raise ValueError(
            "Overlap must be smaller than both chunk dimensions."
        )

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        with Image.open(screenshot_path) as source:
            image = source.convert("RGB")

    except (OSError, ValueError) as error:
        raise ValueError(
            f"Unable to load screenshot: {error}"
        ) from error

    width, height = image.size

    x_positions = generate_positions(
        width, chunk_width, overlap
    )

    y_positions = generate_positions(
        height, chunk_height, overlap
    )

    chunk_details = []
    chunk_number = 1

    # Generate image chunks
    for y in y_positions:
        for x in x_positions:

            right = min(x + chunk_width, width)
            bottom = min(y + chunk_height, height)

            chunk = image.crop(
                (x, y, right, bottom)
            )

            filename = (
                f"chunk_{chunk_number:03d}_"
                f"x{x}_y{y}.png"
            )

            chunk_path = output_dir / filename

            chunk.save(chunk_path, format="PNG")

            # Store original screenshot coordinates
            chunk_details.append({
                "chunk_id": chunk_number,
                "filename": filename,
                "coordinates": {
                    "x1": x,
                    "y1": y,
                    "x2": right,
                    "y2": bottom
                },
                "width": right - x,
                "height": bottom - y
            })

            print(f"Saved: {chunk_path}")

            chunk_number += 1

    # Save chunk information as JSON
    metadata = {
        "original_screenshot": str(screenshot_path),
        "original_dimensions": {
            "width": width,
            "height": height
        },
        "chunk_dimensions": {
            "width": chunk_width,
            "height": chunk_height
        },
        "overlap": overlap,
        "total_chunks": len(chunk_details),
        "chunks": chunk_details
    }

    metadata_path = output_dir / "chunk_metadata.json"

    with open(metadata_path, "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=4)

    print(f"\nTotal chunks created: {len(chunk_details)}")
    print(f"Metadata saved: {metadata_path}")

    return chunk_details


if __name__ == "__main__":
    chunk_screenshot(
        screenshot_path="screenshots/checkout.png",
        output_dir="chunks",
        chunk_width=500,
        chunk_height=500,
        overlap=50
    )
