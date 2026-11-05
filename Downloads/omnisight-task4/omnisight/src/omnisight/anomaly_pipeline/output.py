"""Write detection results: `anomalies.json`, an annotated screenshot and a crop of the primary anomaly."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from omnisight.anomaly_pipeline.models import Anomaly, DetectionResult

_COLORS = {"high": (220, 38, 38), "medium": (234, 138, 0), "low": (37, 99, 235)}
JSON_NAME = "anomalies.json"
ANNOTATED_NAME = "anomalies_annotated.png"
CROP_NAME = "primary_anomaly.png"


def _font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.load_default(size=size)
    except TypeError:                       # Pillow < 10.1
        return ImageFont.load_default()


def annotate(image: Image.Image, anomalies: list[Anomaly], doc_size: tuple[float, float]) -> Image.Image:
    """Draw a numbered box per anomaly. Boxes are CSS px; the image may be clamped in height."""
    img = image.convert("RGB")
    sx = img.width / doc_size[0] if doc_size[0] else 1.0
    sy = img.height / doc_size[1] if doc_size[1] else 1.0
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    font = _font(max(12, img.width // 90))
    labels: list[tuple[tuple[float, float], str, tuple[int, int, int]]] = []

    for a in reversed(anomalies):           # draw the primary last so it sits on top
        r, g, b = _COLORS.get(a.severity, _COLORS["medium"])
        bb = a.bbox.scaled(sx, sy)
        if bb.y > img.height or bb.x > img.width:
            continue
        width = 4 if a.rank == 1 else 2
        od.rectangle([bb.x, bb.y, bb.x2, bb.y2], fill=(r, g, b, 40), outline=(r, g, b, 255), width=width)
        if a.related_bbox is not None:
            rb = a.related_bbox.scaled(sx, sy)
            od.rectangle([rb.x, rb.y, rb.x2, rb.y2], outline=(r, g, b, 200), width=1)
        labels.append(((bb.x, bb.y), f"{a.id} {a.type}", (r, g, b)))

    img = Image.alpha_composite(img.convert("RGBA"), overlay)
    d = ImageDraw.Draw(img)
    for (x, y), text, col in labels:
        tb = d.textbbox((0, 0), text, font=font)
        tw, th = tb[2] - tb[0] + 8, tb[3] - tb[1] + 6
        ty = y - th if y - th >= 0 else y
        d.rectangle([x, ty, x + tw, ty + th], fill=col)
        d.text((x + 4, ty + 2), text, fill=(255, 255, 255), font=font)
    return img.convert("RGB")


def crop_primary(image: Image.Image, anomaly: Anomaly, doc_size: tuple[float, float], pad: int = 32) -> Image.Image:
    sx = image.width / doc_size[0] if doc_size[0] else 1.0
    sy = image.height / doc_size[1] if doc_size[1] else 1.0
    box = anomaly.bbox
    if anomaly.related_bbox is not None:
        box = box.union_with(anomaly.related_bbox)
    b = box.padded(pad).scaled(sx, sy).clamped(image.width, image.height)
    return image.crop((int(b.x), int(b.y), int(b.x2) + 1, int(b.y2) + 1))


def write_outputs(result: DetectionResult, bundle: dict, bundle_dir: str | Path, out_dir: str | Path) -> dict[str, str]:
    """Write all artefacts into `out_dir`; returns the file map that is also stored in the JSON."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    files: dict[str, str] = {}

    shot = (bundle.get("screenshots") or {}).get("full_page") or {}
    shot_path = Path(bundle_dir) / shot.get("path", "screenshot_full.png")
    if result.anomalies and shot_path.exists():
        with Image.open(shot_path) as im:
            annotate(im, result.anomalies, result.document).save(out / ANNOTATED_NAME)
            files["annotated"] = ANNOTATED_NAME
            crop_primary(im.convert("RGB"), result.anomalies[0], result.document).save(out / CROP_NAME)
            files["primary_crop"] = CROP_NAME
    elif result.anomalies:
        result.warnings.append(f"Screenshot {shot_path} not found; skipped the annotated image and crop.")

    result.files = {**files, "json": JSON_NAME}
    payload = result.to_dict()
    payload["created_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (out / JSON_NAME).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result.files
