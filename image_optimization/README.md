# Screenshot Chunking Module

## Overview

The Screenshot Chunking module divides large UI screenshots into smaller image regions for focused Visual Language Model (VLM) analysis.

When exact anomaly coordinates are unavailable, the module divides the full screenshot into smaller chunks that can be analysed individually to identify potential UI defects.

## Features

- Loads full UI screenshots.
- Divides screenshots into configurable image chunks.
- Supports overlapping chunks to reduce missed defects near boundaries.
- Tracks the original coordinates of every chunk.
- Saves individual chunks as PNG images.
- Generates JSON metadata containing chunk information.
- Handles invalid paths, dimensions and image-loading errors.

## Technologies Used

- Python
- Pillow (PIL)
- JSON
- pathlib

## Project Structure

```text
OmniSight/
│
├── image_optimization/
│   ├── __init__.py
│   ├── screenshot_chunking.py
│   └── README.md
│
├── screenshots/
│   └── checkout.png
│
├── chunks/
│
└── tests/
    └── test_screenshot_chunking.py
```

## Installation

```bash
pip install Pillow
```

## Configuration

| Parameter | Description | Default |
|---|---|---|
| screenshot_path | Input screenshot path | Required |
| output_dir | Chunk output directory | chunks |
| chunk_width | Chunk width in pixels | 500 |
| chunk_height | Chunk height in pixels | 500 |
| overlap | Shared pixels between adjacent chunks | 50 |

## Usage

Place the input screenshot inside the screenshots directory.

Run:

```bash
python image_optimization/screenshot_chunking.py
```

Or import the function:

```python
from image_optimization.screenshot_chunking import chunk_screenshot

chunk_screenshot(
    screenshot_path="screenshots/checkout.png",
    output_dir="chunks",
    chunk_width=500,
    chunk_height=500,
    overlap=50
)
```

## Overlapping Chunk Generation

The module uses configurable overlap to ensure adjacent image regions share some pixels.

This reduces the possibility of missing UI defects located near chunk boundaries.

## Coordinate Tracking

Each generated chunk stores its original screenshot coordinates:

- x1: Left boundary
- y1: Top boundary
- x2: Right boundary
- y2: Bottom boundary

These coordinates help identify the original location of a chunk.

## Output

Generated files are saved in the chunks directory.

```text
chunks/
├── chunk_001_x0_y0.png
├── chunk_002_x450_y0.png
├── chunk_003_x700_y0.png
└── chunk_metadata.json
```

The metadata JSON contains:

- Original screenshot dimensions.
- Configured chunk dimensions.
- Overlap value.
- Total number of chunks.
- Individual chunk filenames and coordinates.

## Testing

Run the test suite:

```bash
python -m unittest discover -s tests -v
```

The tests validate chunk generation, file creation, metadata, coordinate tracking and invalid input handling.

## Integration with OmniSight

The generated chunks can be passed individually to the VLM for focused UI defect analysis when exact anomaly coordinates are unavailable.

The module prepares image regions; it does not independently detect UI defects.

## Future Integration

- Connect chunk generation with Playwright screenshot capture.
- Pass generated chunks to the VLM.
- Collect and combine anomaly detection results.
- Evaluate chunk-based analysis against full-image analysis.

## Status

**Implementation:** Screenshot chunking with overlap and coordinate tracking.

**Testing:** Unit tests included.

**Integration:** Ready for connection with the OmniSight VLM workflow.