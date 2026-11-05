"""Bounding-box geometry and coordinate-format normalisation.

Everything in OmniSight is expressed in **CSS pixels, origin at the top-left of
the full page** (see the Week 2 README). VLMs do not always answer that way, so
this module converts the common alternatives:

* `[x1, y1, x2, y2]` (corners) vs `[x, y, w, h]` (size)  - ambiguous when bare
* normalised 0-1 or 0-1000 coordinates (Qwen/Gemini style)
* pixels of a downscaled image the model actually saw
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

SPACE_AUTO = "auto"
SPACE_CSS = "css"
SPACE_NORM = "normalized"          # 0..1
SPACE_NORM1000 = "normalized1000"  # 0..1000
SPACES = (SPACE_AUTO, SPACE_CSS, SPACE_NORM, SPACE_NORM1000)

FMT_XYWH = "xywh"
FMT_XYXY = "xyxy"


@dataclass(frozen=True)
class BBox:
    """Axis-aligned box: top-left corner plus size, in CSS pixels."""

    x: float
    y: float
    w: float
    h: float

    # -- construction ------------------------------------------------------
    @classmethod
    def from_xyxy(cls, x1: float, y1: float, x2: float, y2: float) -> "BBox":
        return cls(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "BBox":
        return cls(float(d["x"]), float(d["y"]), float(d["w"]), float(d["h"]))

    # -- derived -----------------------------------------------------------
    @property
    def x2(self) -> float:
        return self.x + self.w

    @property
    def y2(self) -> float:
        return self.y + self.h

    @property
    def area(self) -> float:
        return max(self.w, 0.0) * max(self.h, 0.0)

    @property
    def center(self) -> tuple[float, float]:
        return (self.x + self.w / 2, self.y + self.h / 2)

    @property
    def valid(self) -> bool:
        return self.w > 0 and self.h > 0

    # -- geometry ----------------------------------------------------------
    def intersection(self, o: "BBox") -> float:
        iw = min(self.x2, o.x2) - max(self.x, o.x)
        ih = min(self.y2, o.y2) - max(self.y, o.y)
        return iw * ih if iw > 0 and ih > 0 else 0.0

    def iou(self, o: "BBox") -> float:
        inter = self.intersection(o)
        union = self.area + o.area - inter
        return inter / union if union > 0 else 0.0

    def contains_point(self, px: float, py: float) -> bool:
        return self.x <= px <= self.x2 and self.y <= py <= self.y2

    def union_with(self, o: "BBox") -> "BBox":
        return BBox.from_xyxy(min(self.x, o.x), min(self.y, o.y), max(self.x2, o.x2), max(self.y2, o.y2))

    def scaled(self, sx: float, sy: float) -> "BBox":
        return BBox(self.x * sx, self.y * sy, self.w * sx, self.h * sy)

    def clamped(self, width: float, height: float) -> "BBox":
        """Clip to the page rectangle (0,0)-(width,height)."""
        x1, y1 = max(self.x, 0.0), max(self.y, 0.0)
        x2, y2 = min(self.x2, width), min(self.y2, height)
        return BBox(x1, y1, max(x2 - x1, 0.0), max(y2 - y1, 0.0))

    def padded(self, px: float) -> "BBox":
        return BBox(self.x - px, self.y - px, self.w + 2 * px, self.h + 2 * px)

    # -- serialisation -----------------------------------------------------
    def to_dict(self) -> dict[str, float]:
        r = lambda v: round(float(v), 2)  # noqa: E731
        return {"x": r(self.x), "y": r(self.y), "w": r(self.w), "h": r(self.h), "x2": r(self.x2), "y2": r(self.y2)}

    def normalized(self, width: float, height: float) -> dict[str, float]:
        if width <= 0 or height <= 0:
            return {"x": 0.0, "y": 0.0, "w": 0.0, "h": 0.0}
        r = lambda v: round(float(v), 5)  # noqa: E731
        return {"x": r(self.x / width), "y": r(self.y / height), "w": r(self.w / width), "h": r(self.h / height)}


# --------------------------------------------------------------------------
# Parsing raw VLM boxes
# --------------------------------------------------------------------------

_DICT_KEYSETS: list[tuple[tuple[str, ...], str]] = [
    (("x", "y", "w", "h"), FMT_XYWH),
    (("x", "y", "width", "height"), FMT_XYWH),
    (("left", "top", "width", "height"), FMT_XYWH),
    (("x1", "y1", "x2", "y2"), FMT_XYXY),
    (("xmin", "ymin", "xmax", "ymax"), FMT_XYXY),
    (("left", "top", "right", "bottom"), FMT_XYXY),
    (("x_min", "y_min", "x_max", "y_max"), FMT_XYXY),
]


def _num(v: Any) -> float | None:
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v.strip().rstrip("px").strip())
        except ValueError:
            return None
    return None


def extract_numbers(raw: Any) -> tuple[list[float], str | None] | None:
    """Pull four numbers (and the format, when the shape declares it) out of a raw box.

    Accepts a list/tuple of 4 numbers, a nested `[[...]]`, or a dict with one of
    the usual key sets. Returns None when no box can be read.
    """
    if isinstance(raw, dict):
        low = {str(k).lower(): v for k, v in raw.items()}
        for keys, fmt in _DICT_KEYSETS:
            if all(k in low for k in keys):
                vals = [_num(low[k]) for k in keys]
                if None not in vals:
                    return [float(v) for v in vals], fmt  # type: ignore[arg-type]
        for inner in ("bbox", "box", "bounding_box", "bounding_box_2d"):
            if inner in low:
                return extract_numbers(low[inner])
        return None
    if isinstance(raw, (list, tuple)):
        if len(raw) == 1 and isinstance(raw[0], (list, tuple, dict)):
            return extract_numbers(raw[0])
        if len(raw) == 2 and all(isinstance(p, (list, tuple)) and len(p) == 2 for p in raw):
            vals2 = [_num(v) for p in raw for v in p]
            return ([float(v) for v in vals2], FMT_XYXY) if None not in vals2 else None  # type: ignore[arg-type]
        if len(raw) == 4:
            vals = [_num(v) for v in raw]
            return ([float(v) for v in vals], None) if None not in vals else None  # type: ignore[arg-type]
    return None


def _unit_scale(values: Iterable[float], space: str, doc_w: float, doc_h: float,
                image_w: float, image_h: float) -> tuple[float, float, str]:
    """Return (sx, sy, resolved_space) turning raw numbers into CSS pixels."""
    vals = list(values)
    if space == SPACE_AUTO:
        space = SPACE_NORM if all(0.0 <= v <= 1.0 for v in vals) else SPACE_CSS
    if space == SPACE_NORM:
        return doc_w, doc_h, space
    if space == SPACE_NORM1000:
        return doc_w / 1000.0, doc_h / 1000.0, space
    # pixels of the image the model saw; 1:1 when it saw the CSS-pixel screenshot
    sx = doc_w / image_w if image_w else 1.0
    sy = doc_h / image_h if image_h else 1.0
    return sx, sy, SPACE_CSS


def to_css_candidates(
    raw: Any,
    *,
    fmt: str | None = None,
    space: str = SPACE_AUTO,
    doc_size: tuple[float, float],
    image_size: tuple[float, float] | None = None,
) -> list[tuple[BBox, str]]:
    """Convert a raw VLM box into candidate CSS-pixel boxes.

    Returns `[(box, interpretation)]`. A bare 4-number list is ambiguous
    (corners vs size) so both readings are returned; the resolver keeps the one
    that lines up with a real DOM element. Invalid boxes are dropped.
    """
    parsed = extract_numbers(raw)
    if parsed is None:
        return []
    vals, declared = parsed
    fmt = fmt or declared
    doc_w, doc_h = doc_size
    img_w, img_h = image_size if image_size else (doc_w, doc_h)
    sx, sy, _ = _unit_scale(vals, space, doc_w, doc_h, img_w, img_h)
    a, b, c, d = vals
    out: list[tuple[BBox, str]] = []
    if fmt in (None, FMT_XYXY) and c > a and d > b:
        out.append((BBox.from_xyxy(a, b, c, d).scaled(sx, sy), FMT_XYXY))
    if fmt in (None, FMT_XYWH) and c > 0 and d > 0:
        out.append((BBox(a, b, c, d).scaled(sx, sy), FMT_XYWH))
    return [(bx, how) for bx, how in out if bx.valid]
