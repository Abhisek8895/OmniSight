"""Tie a `RawFinding` to a real DOM element and settle its bounding box.

Resolution order (first hit wins, most reliable first):

1. `element_id`   - the model quoted an `el#N` id from the context
2. `hint_id`      - the model quoted an `H<n>` id; the hint names the element
3. `selector`     - exact match against recorded selectors
4. `bbox_iou`     - the model's own box overlaps a recorded element (IoU >= `min_iou`)
5. `bbox_center`  - the centre of the model's box lies inside a recorded element
6. `text`         - quoted visible text matches one element

When an element is found, the reported box is the **browser-measured DOM box**
(exact, 1:1 with the screenshot) and the model's box is kept for comparison.
When nothing matches, the model's box is reported as-is and flagged.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from omnisight.anomaly_pipeline.bbox import SPACE_AUTO, BBox, to_css_candidates
from omnisight.anomaly_pipeline.context import ContextIndex
from omnisight.anomaly_pipeline.models import (
    RES_BBOX_CENTER,
    RES_BBOX_IOU,
    RES_ELEMENT_ID,
    RES_HINT_ID,
    RES_NONE,
    RES_SELECTOR,
    RES_TEXT,
    RawFinding,
)


@dataclass
class Resolution:
    element_id: int | None
    method: str
    vlm_bbox: BBox | None = None
    vlm_bbox_iou: float | None = None
    related_element_id: int | None = None
    warnings: list[str] = field(default_factory=list)


def _best_by_iou(cands: list[tuple[BBox, str]], idx: ContextIndex) -> tuple[BBox, int | None, float]:
    """Pick (box, element_id, iou) with the best overlap across candidate readings.

    Ties go to flagged elements, then to the smaller (more specific) element.
    """
    best: tuple[float, int, float, BBox, int | None] | None = None
    for box, _ in cands:
        for eid, eb in idx.boxes.items():
            iou = box.iou(eb)
            if iou <= 0:
                continue
            flagged = 1 if idx.elements[eid].get("flags") else 0
            key = (round(iou, 4), flagged, -eb.area)
            if best is None or key > (best[0], best[1], best[2]):
                best = (key[0], key[1], key[2], box, eid)
    if best is None:
        return cands[0][0], None, 0.0
    return best[3], best[4], best[0]


def _center_element(box: BBox, idx: ContextIndex) -> int | None:
    cx, cy = box.center
    inside = [eid for eid, eb in idx.boxes.items() if eb.contains_point(cx, cy)]
    if not inside:
        return None
    # smallest element under the centre, but never a page-sized wrapper
    inside.sort(key=lambda i: idx.boxes[i].area)
    return inside[0]


def resolve(
    f: RawFinding,
    idx: ContextIndex,
    *,
    coord_space: str = SPACE_AUTO,
    image_size: tuple[float, float] | None = None,
    min_iou: float = 0.3,
) -> Resolution:
    warnings: list[str] = []

    # 0. read the model's own box (always, so we can compare it with the DOM box)
    vlm_box: BBox | None = None
    cands: list[tuple[BBox, str]] = []
    if f.bbox_raw is not None:
        cands = to_css_candidates(
            f.bbox_raw, fmt=f.bbox_format, space=f.coord_space or coord_space,
            doc_size=idx.doc_size, image_size=image_size,
        )
        if not cands:
            warnings.append("Could not read the VLM bounding box; ignoring it.")
    if cands:
        vlm_box, _, _ = _best_by_iou(cands, idx)

    def finish(eid: int | None, method: str) -> Resolution:
        iou = None
        if eid is not None and vlm_box is not None and eid in idx.boxes:
            iou = vlm_box.iou(idx.boxes[eid])
            if iou < 0.1:
                warnings.append(
                    f"VLM box and el#{eid} barely overlap (IoU {iou:.2f}); using the DOM box. "
                    "The model may have mis-quoted the element id or the box."
                )
        rel = f.related_element_id if f.related_element_id in idx.elements else None
        return Resolution(eid, method, vlm_box, iou, rel, warnings)

    # 1. element id
    if f.element_id is not None:
        if f.element_id in idx.boxes:
            return finish(f.element_id, RES_ELEMENT_ID)
        warnings.append(f"el#{f.element_id} is not in the context (or has no box); trying other signals.")

    # 2. hint id
    if f.hint_id is not None:
        h = idx.hints.get(f.hint_id)
        if h and h.get("element_id") in idx.boxes:
            res = finish(h["element_id"], RES_HINT_ID)
            if res.related_element_id is None and h.get("related_id") in idx.elements:
                res.related_element_id = h["related_id"]
            return res
        warnings.append(f"H{f.hint_id} is not in the context; trying other signals.")

    # 3. selector
    eid = idx.element_by_selector(f.selector)
    if eid is not None and eid in idx.boxes:
        return finish(eid, RES_SELECTOR)
    if f.selector:
        warnings.append(f"Selector {f.selector!r} matches no recorded element.")

    # 4/5. geometry
    if cands:
        box, eid, iou = _best_by_iou(cands, idx)
        if eid is not None and iou >= min_iou:
            return finish(eid, RES_BBOX_IOU)
        eid = _center_element(box, idx)
        if eid is not None:
            warnings.append("VLM box only loosely matches this element (matched by box centre).")
            return finish(eid, RES_BBOX_CENTER)

    # 6. text
    if f.text:
        hits = idx.elements_with_text(f.text)
        hits = [h for h in hits if h in idx.boxes]
        if hits:
            if len(hits) > 1:
                warnings.append(f"Text matched {len(hits)} elements; used the most specific one.")
            return finish(hits[0], RES_TEXT)

    if vlm_box is None:
        warnings.append("No element and no readable bounding box: this finding cannot be located.")
    else:
        warnings.append("No recorded element matches; reporting the VLM's own box (unverified).")
    return Resolution(None, RES_NONE, vlm_box, None, None, warnings)
