"""Before/after image comparison: pixel diff and a labelled side-by-side."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

BG = (243, 244, 246)
LABEL_BG = {"before": (75, 85, 99), "after": (22, 163, 74)}


def _font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # very old Pillow
        return ImageFont.load_default()


def _pad(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Pad to `size` with white so pages of different heights can be compared."""
    if img.size == size:
        return img
    canvas = Image.new("RGB", size, (255, 255, 255))
    canvas.paste(img, (0, 0))
    return canvas


def pixel_diff(before_path: Path, after_path: Path, out_path: Path | None, threshold: int = 16) -> dict:
    """Compare two screenshots.

    Returns the share of changed pixels (any channel differing by more than
    `threshold`), the bounding box of the change, and optionally writes a diff
    image (changed pixels in red over a faded copy of the after screenshot).
    """
    with Image.open(before_path) as b, Image.open(after_path) as a:
        b, a = b.convert("RGB"), a.convert("RGB")
        size = (max(b.width, a.width), max(b.height, a.height))
        b, a = _pad(b, size), _pad(a, size)

    diff = ImageChops.difference(b, a)
    mask = diff.convert("L").point(lambda v: 255 if v > threshold else 0)
    changed = mask.histogram()[255]
    total = size[0] * size[1]
    box = mask.getbbox()

    if out_path is not None:
        faded = Image.blend(a, Image.new("RGB", size, (255, 255, 255)), 0.65)
        red = Image.new("RGB", size, (220, 38, 38))
        faded.paste(red, (0, 0), mask)
        faded.save(out_path)

    return {
        "changed_pixels": changed,
        "changed_pixel_ratio": round(changed / total, 6) if total else 0.0,
        "changed_region": (
            {"x": box[0], "y": box[1], "w": box[2] - box[0], "h": box[3] - box[1]} if box else None
        ),
        "size_changed": Image.open(before_path).size != Image.open(after_path).size,
        "visible_change": changed > 0,
    }


def side_by_side(before_path: Path, after_path: Path, out_path: Path, gap: int = 24, header: int = 40) -> Path:
    """Write one image with BEFORE on the left and AFTER on the right."""
    with Image.open(before_path) as b, Image.open(after_path) as a:
        b, a = b.convert("RGB"), a.convert("RGB")
    h = max(b.height, a.height)
    canvas = Image.new("RGB", (b.width + a.width + gap * 3, h + header + gap), BG)
    draw = ImageDraw.Draw(canvas)
    font = _font(20)
    for name, img, x in (("before", b, gap), ("after", a, b.width + gap * 2)):
        draw.rectangle([x, 8, x + img.width, header - 6], fill=LABEL_BG[name])
        draw.text((x + 12, 12), name.upper(), fill=(255, 255, 255), font=font)
        canvas.paste(img, (x, header))
    canvas.save(out_path)
    return out_path
