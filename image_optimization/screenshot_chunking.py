
from PIL import Image
import os


def chunk_screenshot(
    screenshot_path,
    output_dir="chunks",
    chunk_width=500,
    chunk_height=500
):
    # Load the screenshot
    image = Image.open(screenshot_path)

    # Get screenshot dimensions
    width, height = image.size

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    chunk_number = 1

    # Divide screenshot into smaller regions
    for y in range(0, height, chunk_height):
        for x in range(0, width, chunk_width):

            # Calculate chunk boundaries
            right = min(x + chunk_width, width)
            bottom = min(y + chunk_height, height)

            # Crop the screenshot
            chunk = image.crop((x, y, right, bottom))

            # Save individual chunk
            chunk_path = os.path.join(
                output_dir,
                f"chunk_{chunk_number}.png"
            )

            chunk.save(chunk_path)

            print(f"Saved: {chunk_path}")

            chunk_number += 1

    print(f"\nTotal chunks created: {chunk_number - 1}")


if __name__ == "__main__":
    chunk_screenshot(
        screenshot_path="screenshot.png"
    )
