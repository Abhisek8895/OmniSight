
from PIL import Image
import os

# Step 1: Create a function for cropping
def crop_image(image_path, coordinates, padding=20):

    # Step 2: Open the screenshot
    image = Image.open(image_path)

    # Step 3: Get image width and height
    width, height = image.size

    # Step 4: Get coordinates
    x1, y1, x2, y2 = coordinates

    # Step 5: Add padding
    x1 = x1 - padding
    y1 = y1 - padding
    x2 = x2 + padding
    y2 = y2 + padding

    # Step 6: Keep coordinates inside image
    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(width, x2)
    y2 = min(height, y2)

    # Step 7: Check coordinates
    if x1 >= x2 or y1 >= y2:
        print("Invalid coordinates!")
        return

    # Step 8: Crop the image
    cropped = image.crop((x1, y1, x2, y2))

    # Step 9: Create output folder
    os.makedirs("output", exist_ok=True)

    # Step 10: Save cropped image
    cropped.save("output/cropped_ui.png")

    print("Cropping completed successfully!")
    print("Original size:", image.size)
    print("Cropped size:", cropped.size)
    print("Saved in output folder!")


# Step 11: Give screenshot location
image_path = "input/Screenshot.png"

# Step 12: Give example coordinates
coordinates = (500, 300, 800, 400)

# Step 13: Run the function
crop_image(image_path, coordinates, padding=20)
