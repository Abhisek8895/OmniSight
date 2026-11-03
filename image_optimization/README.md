# Screenshot Chunking Module

## Overview

The Screenshot Chunking module is responsible for dividing large UI screenshots into smaller image regions for focused Visual Language Model (VLM) analysis.

When the exact coordinates of a UI defect are unavailable, the module divides the complete screenshot into smaller chunks. These chunks can later be analysed individually by the VLM to identify potential UI anomalies.

## Objectives

- Load full UI screenshots.
- Divide large screenshots into smaller rectangular regions.
- Support configurable chunk width and height.
- Save individual chunks separately.
- Prepare smaller image regions for future VLM analysis.

## Project Structure

```text
OmniSight/
│
├── image_optimization/
│   └── screenshot_chunking.py
│
├── screenshots/
│   └── checkout.png
│
├── chunks/
│
└── README.md
```

## Technologies Used

- Python
- Pillow (PIL)
- OS module

## Installation

Install the required dependency:

```bash
pip install Pillow
```

## How It Works

1. The module loads the original UI screenshot.
2. It retrieves the screenshot's width and height.
3. It divides the screenshot according to the configured chunk dimensions.
4. Each region is extracted using image cropping.
5. Individual chunks are saved as separate PNG images.
6. The total number of generated chunks is displayed.

## Configuration

The chunking function supports the following parameters:

| Parameter | Description | Default |
|---|---|---|
| screenshot_path | Path of the input screenshot | Required |
| output_dir | Directory for saving generated chunks | chunks |
| chunk_width | Width of each chunk in pixels | 500 |
| chunk_height | Height of each chunk in pixels | 500 |

## Usage

Place the screenshot inside the `screenshots` directory.

Example:

```text
screenshots/checkout.png
```

Run the module:

```bash
python image_optimization/screenshot_chunking.py
```

Alternatively, call the function from another Python file:

```python
from image_optimization.screenshot_chunking import chunk_screenshot

chunk_screenshot(
    screenshot_path="screenshots/checkout.png",
    output_dir="chunks",
    chunk_width=500,
    chunk_height=500
)
```

## Output

The generated image chunks are automatically stored inside the configured output directory.

Example:

```text
chunks/
├── chunk_1.png
├── chunk_2.png
├── chunk_3.png
├── chunk_4.png
└── ...
```

The number of generated chunks depends on the original screenshot dimensions and configured chunk size.

## Integration with OmniSight

The generated chunks will serve as smaller input images for VLM-based UI defect analysis.

Instead of processing an entire large screenshot, OmniSight can analyse individual image regions to focus on smaller portions of the interface.

## Future Improvements

- Implement overlapping chunks to avoid missing defects near chunk boundaries.
- Track the original screenshot coordinates of each chunk.
- Add input validation and error handling.
- Support different screenshot dimensions.
- Integrate chunk generation with the OmniSight image optimization pipeline.
- Evaluate chunk-based VLM analysis against full-image analysis.

## Status

**Current Status:** Basic screenshot chunking implementation.

**Next Steps:** Overlap support, coordinate tracking, testing, and pipeline integration.