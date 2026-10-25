"""Screenshot capture, tiling, annotation and zoomed crops."""

from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import Page

from omnisight.context_pipeline.config import PipelineConfig

SEVERITY_COLORS = {
    "high": (220, 38, 38),
    "medium": (234, 138, 0),
    "low": (37, 99, 235),
}
_SEV_ORDER = {"high": 3, "medium": 2, "low": 1}


def _meta(path: Path, root: Path, **extra) -> dict:
    with Image.open(path) as im:
        w, h = im.size
    return {"path": path.relative_to(root).as_posix(), "width": w, "height": h, **extra}


def _font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # very old Pillow
        return ImageFont.load_default()


# --------------------------------------------------------------------------
# Raw captures
# --------------------------------------------------------------------------
def capture_raw(page: Page, out_dir: Path, cfg: PipelineConfig) -> dict:
    """Viewport (above the fold) and full-page screenshots.

    Everything is written in CSS pixels (`scale="css"`) so element bounding
    boxes in the context map onto the images 1:1, whatever the device pixel ratio.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    shots: dict = {}
    page.evaluate("window.scrollTo(0, 0)")

    if cfg.capture_viewport_shot:
        p = out_dir / "screenshot_viewport.png"
        page.screenshot(path=str(p), full_page=False, animations="disabled", scale="css")
        shots["viewport"] = _meta(p, out_dir, description="Above-the-fold view exactly as a user first sees it.")

    if cfg.capture_full_page:
        dims = page.evaluate(
            "() => ({w: document.documentElement.scrollWidth, h: document.documentElement.scrollHeight})"
        )
        width = min(max(dims["w"], 1), cfg.max_image_dim)
        height = min(max(dims["h"], 1), cfg.max_image_dim)
        p = out_dir / "screenshot_full.png"
        page.screenshot(
            path=str(p), full_page=True, animations="disabled", scale="css",
            clip={"x": 0, "y": 0, "width": width, "height": height},
        )
        shots["full_page"] = _meta(
            p, out_dir,
            description="Entire scrollable page.",
            truncated=dims["h"] > cfg.max_image_dim or dims["w"] > cfg.max_image_dim,
        )
    return shots


def _base_image(out_dir: Path, shots: dict) -> Image.Image | None:
    key = "full_page" if "full_page" in shots else "viewport" if "viewport" in shots else None
    if key is None:
        return None
    return Image.open(out_dir / shots[key]["path"]).convert("RGB")


# --------------------------------------------------------------------------
# Tiles
# --------------------------------------------------------------------------
def make_tiles(out_dir: Path, shots: dict, cfg: PipelineConfig) -> list[dict]:
    """Slice a tall full-page capture into overlapping tiles.

    Most VLMs downscale large images, which erases small text. Tiles keep
    detail while still covering the whole page.
    """
    tiles_dir = out_dir / "tiles"
    if tiles_dir.exists():
        shutil.rmtree(tiles_dir)
    if not cfg.tile_tall_pages or "full_page" not in shots:
        return []
    img = Image.open(out_dir / shots["full_page"]["path"]).convert("RGB")
    w, h = img.size
    if h <= cfg.tile_height * 1.3:
        return []
    tiles_dir.mkdir(parents=True)
    step = cfg.tile_height - cfg.tile_overlap
    out: list[dict] = []
    y = 0
    while y < h and len(out) < cfg.max_tiles:
        bottom = min(y + cfg.tile_height, h)
        p = tiles_dir / f"tile_{len(out) + 1:02d}.png"
        img.crop((0, y, w, bottom)).save(p)
        out.append(_meta(p, out_dir, y_start=y, y_end=bottom))
        if bottom >= h:
            break
        y += step
    if out and out[-1]["y_end"] < h:
        out[-1]["note"] = f"page continues below y={out[-1]['y_end']} (max_tiles reached)"
    return out


# --------------------------------------------------------------------------
# Annotation & crops
# --------------------------------------------------------------------------
def _hinted_boxes(elements: list[dict], hints: list[dict]) -> dict[int, dict]:
    by_id = {e["id"]: e for e in elements}
    boxes: dict[int, dict] = {}
    for h in hints:
        eid = h.get("element_id")
        if eid is None or eid not in by_id:
            continue
        slot = boxes.setdefault(eid, {"bbox": by_id[eid]["bbox"], "hints": [], "severity": "low"})
        slot["hints"].append(h["id"])
        if _SEV_ORDER[h["severity"]] > _SEV_ORDER[slot["severity"]]:
            slot["severity"] = h["severity"]
    return boxes


def annotate(out_dir: Path, shots: dict, elements: list[dict], hints: list[dict], cfg: PipelineConfig) -> dict | None:
    """Draw numbered boxes (H<hint id>) around flagged elements.

    The unannotated screenshot stays the primary image; this is a companion
    that lets the VLM and the repair stage map a pixel region to a selector.
    """
    if cfg.annotate == "none":
        return None
    img = _base_image(out_dir, shots)
    if img is None:
        return None
    boxes = _hinted_boxes(elements, hints)
    if not boxes:
        return None

    draw = ImageDraw.Draw(img, "RGBA")
    font = _font(14)
    # Draw big boxes first so small ones remain visible on top.
    for eid, slot in sorted(boxes.items(), key=lambda kv: -(kv[1]["bbox"]["w"] * kv[1]["bbox"]["h"])):
        b = slot["bbox"]
        x0, y0, x1, y1 = b["x"], b["y"], b["x"] + b["w"], b["y"] + b["h"]
        if x0 >= img.width or y0 >= img.height:
            continue
        color = SEVERITY_COLORS[slot["severity"]]
        draw.rectangle([x0, y0, x1, y1], outline=color + (255,), width=2)
        label = " ".join(f"H{i}" for i in slot["hints"][:3])
        tw = draw.textlength(label, font=font)
        ly = y0 - 18 if y0 >= 18 else y0
        draw.rectangle([x0, ly, x0 + tw + 8, ly + 18], fill=color + (235,))
        draw.text((x0 + 4, ly + 1), label, fill=(255, 255, 255, 255), font=font)

    p = out_dir / "screenshot_annotated.png"
    img.save(p)
    return _meta(
        p, out_dir,
        description="Same page with numbered boxes (H<n>) marking elements flagged by the layout checks. "
        "Colour: red=high, orange=medium, blue=low severity.",
    )


def make_crops(out_dir: Path, shots: dict, elements: list[dict], hints: list[dict], cfg: PipelineConfig) -> list[dict]:
    """Zoomed crops around the most serious flagged elements."""
    crops_dir = out_dir / "crops"
    if crops_dir.exists():
        shutil.rmtree(crops_dir)
    if cfg.crop_hinted_elements <= 0:
        return []
    img = _base_image(out_dir, shots)
    if img is None:
        return []
    by_id = {e["id"]: e for e in elements}
    crops: list[dict] = []
    used: set[int] = set()
    crops_dir.mkdir(parents=True)
    pad = cfg.crop_padding
    for h in sorted(hints, key=lambda x: (-_SEV_ORDER[x["severity"]], x["id"])):
        if len(crops) >= cfg.crop_hinted_elements:
            break
        eid = h.get("element_id")
        if eid is None or eid in used or eid not in by_id:
            continue
        boxes = [by_id[eid]["bbox"]]
        rid = h.get("related_id")
        if rid in by_id:
            boxes.append(by_id[rid]["bbox"])
        x0 = min(b["x"] for b in boxes) - pad
        y0 = min(b["y"] for b in boxes) - pad
        x1 = max(b["x"] + b["w"] for b in boxes) + pad
        y1 = max(b["y"] + b["h"] for b in boxes) + pad
        x0, y0 = max(0, int(x0)), max(0, int(y0))
        x1, y1 = min(img.width, int(x1)), min(img.height, int(y1))
        if x1 - x0 < 8 or y1 - y0 < 8:
            continue
        used.add(eid)
        p = crops_dir / f"h{h['id']:02d}_{h['type']}.png"
        img.crop((x0, y0, x1, y1)).save(p)
        crops.append(
            _meta(p, out_dir, hint_id=h["id"], element_id=eid, hint_type=h["type"],
                  region={"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0})
        )
    return crops
