
import unittest
import tempfile
import json

from pathlib import Path
from PIL import Image

from image_optimization.screenshot_chunking import (
    chunk_screenshot,
    generate_positions
)


class TestScreenshotChunking(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)

        self.screenshot_path = self.base_path / "test.png"

        # Create a sample screenshot
        image = Image.new("RGB", (1200, 800), "white")
        image.save(self.screenshot_path)

        self.output_dir = self.base_path / "chunks"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_chunk_generation(self):
        chunks = chunk_screenshot(
            screenshot_path=self.screenshot_path,
            output_dir=self.output_dir,
            chunk_width=500,
            chunk_height=500,
            overlap=50
        )

        self.assertEqual(len(chunks), 6)

    def test_chunk_files_exist(self):
        chunk_screenshot(
            self.screenshot_path,
            self.output_dir
        )

        images = list(self.output_dir.glob("chunk_*.png"))

        self.assertEqual(len(images), 6)

    def test_metadata_creation(self):
        chunk_screenshot(
            self.screenshot_path,
            self.output_dir
        )

        metadata_path = self.output_dir / "chunk_metadata.json"

        self.assertTrue(metadata_path.exists())

        with open(metadata_path, encoding="utf-8") as file:
            metadata = json.load(file)

        self.assertEqual(metadata["total_chunks"], 6)

    def test_coordinate_tracking(self):
        chunks = chunk_screenshot(
            self.screenshot_path,
            self.output_dir
        )

        first_chunk = chunks[0]

        self.assertEqual(
            first_chunk["coordinates"],
            {"x1": 0, "y1": 0, "x2": 500, "y2": 500}
        )

    def test_invalid_screenshot_path(self):
        with self.assertRaises(FileNotFoundError):
            chunk_screenshot(
                self.base_path / "missing.png",
                self.output_dir
            )

    def test_invalid_overlap(self):
        with self.assertRaises(ValueError):
            chunk_screenshot(
                self.screenshot_path,
                self.output_dir,
                overlap=500
            )


if __name__ == "__main__":
    unittest.main()
