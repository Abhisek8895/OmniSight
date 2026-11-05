"""Anomaly detection and coordinate extraction (Week 4 / Task 4).

`detect_anomalies(bundle, vlm_response)` takes the Week 2 context bundle and the
VLM's analysis and returns ranked anomalies, each with the UI component it
concerns and a bounding box in CSS pixels.

Without a VLM response it runs in `heuristic` mode and promotes the Week 2
layout hints instead, which is useful as an offline baseline and as a check on
what the VLM reported.
"""

from __future__ import annotations

from typing import Any

from omnisight.anomaly_pipeline.bbox import SPACE_AUTO, SPACES, BBox
from omnisight.anomaly_pipeline.context import ContextIndex
from omnisight.anomaly_pipeline.models import (
    MODE_HEURISTIC,
    MODE_VLM,
    RES_ELEMENT_ID,
    RES_HINT_ID,
    RES_NONE,
    RES_SELECTOR,
    SEVERITY_WEIGHT,
    SRC_DOM,
    SRC_VLM,
    Anomaly,
    DetectionResult,
    RawFinding,
)
from omnisight.anomaly_pipeline.resolver import resolve
from omnisight.anomaly_pipeline.vlm_parser import normalize_severity, parse_vlm_response

_SEV_RANK = {"high": 3, "medium": 2, "low": 1}
_STRONG = {RES_ELEMENT_ID, RES_HINT_ID, RES_SELECTOR}


def _hint_summary(h: dict[str, Any]) -> dict[str, Any]:
    return {"id": h["id"], "type": h["type"], "severity": h["severity"], "message": h.get("message", "")}


def findings_from_hints(idx: ContextIndex) -> list[RawFinding]:
    """Heuristic mode: one finding per Week 2 hint."""
    out: list[RawFinding] = []
    for i, h in enumerate(idx.hints.values(), 1):
        out.append(RawFinding(
            index=i, description=h.get("message", ""), type=h["type"], severity=h["severity"],
            element_id=h.get("element_id"), related_element_id=h.get("related_id"),
            hint_id=h["id"], source=MODE_HEURISTIC,
        ))
    return out


def _confidence(f: RawFinding, method: str, iou: float | None, corroborated: bool) -> float:
    """Heuristic 0..1 trust score (not a calibrated probability).

    Starts from the VLM's own confidence (0.6 if it gave none, 0.5 for hint-only
    findings). Each independent signal moves it a fraction of the way towards 1, so the
    model's own ranking is never flattened; contradictions scale it down.
    """
    c = f.confidence if f.confidence is not None else (0.6 if f.source == MODE_VLM else 0.5)

    def up(c: float, frac: float) -> float:
        return c + (1.0 - c) * frac

    if method in _STRONG:
        c = up(c, 0.40)             # tied to an element by id / hint / selector
    elif method == RES_NONE:
        c *= 0.60                   # nothing in the DOM backs this finding
    else:
        c = up(c, 0.15)             # matched by geometry / text only
    if f.source == MODE_VLM:
        if corroborated:
            c = up(c, 0.25)         # a Week 2 hint also flags this element
        if iou is not None:
            if iou >= 0.5:
                c = up(c, 0.25)     # the model's box agrees with the measured DOM box
            elif iou < 0.1:
                c *= 0.60           # model's box and element id contradict each other
    return max(0.02, min(0.99, c))


def _build(f: RawFinding, idx: ContextIndex, *, coord_space: str, image_size, min_iou: float) -> Anomaly | None:
    res = resolve(f, idx, coord_space=coord_space, image_size=image_size, min_iou=min_iou)
    warnings = list(res.warnings)
    element = idx.elements.get(res.element_id) if res.element_id is not None else None

    if element is not None:
        bbox, src = idx.boxes[res.element_id], SRC_DOM
        hints = idx.hints_for(res.element_id)
    elif res.vlm_bbox is not None:
        clamped = res.vlm_bbox.clamped(*idx.doc_size)
        if clamped.area < res.vlm_bbox.area * 0.999:
            warnings.append("VLM box extended beyond the page and was clipped to it.")
        if not clamped.valid:
            return None
        bbox, src, hints = clamped, SRC_VLM, []
    else:
        return None

    related_id = res.related_element_id
    if related_id is None and element is not None:
        own = [h for h in hints if h.get("element_id") == res.element_id and h.get("related_id") in idx.boxes]
        related_id = own[0]["related_id"] if own else None
    related_bbox = idx.boxes.get(related_id) if related_id is not None else None

    hint_sevs = [h["severity"] for h in hints if h.get("severity") in _SEV_RANK]
    top_hint = max(hints, key=lambda h: _SEV_RANK.get(h.get("severity"), 0)) if hints else None
    severity = f.severity or (max(hint_sevs, key=_SEV_RANK.get) if hint_sevs else "medium")
    ftype = f.type or (top_hint["type"] if top_hint else "unspecified")
    desc = f.description or " ".join(h.get("message", "") for h in hints[:2]).strip() or ftype

    conf = _confidence(f, res.method, res.vlm_bbox_iou, corroborated=bool(hints))
    return Anomaly(
        id="", rank=0, type=ftype, severity=severity, confidence=conf, description=desc,
        bbox=bbox, bbox_source=src, resolution=res.method, source=f.source, element=element,
        related_element_id=related_id if related_bbox else None, related_bbox=related_bbox,
        hints=[_hint_summary(h) for h in hints], vlm_bbox=res.vlm_bbox, vlm_bbox_iou=res.vlm_bbox_iou,
        warnings=warnings,
    )


def _merge(items: list[Anomaly]) -> list[Anomaly]:
    """Collapse findings about the same element (or the same unresolved box) into one."""
    merged: list[Anomaly] = []
    for a in items:
        target = None
        for m in merged:
            same_el = a.element_id is not None and a.element_id == m.element_id
            same_box = (a.element_id is None and m.element_id is None and a.type == m.type
                        and a.bbox.iou(m.bbox) > 0.7)
            if same_el or same_box:
                target = m
                break
        if target is None:
            merged.append(a)
            continue
        target.merged_from += a.merged_from
        if _SEV_RANK[a.severity] > _SEV_RANK[target.severity]:
            target.severity = a.severity
        if a.confidence > target.confidence:
            target.confidence = a.confidence
        if a.type != target.type and a.type != "unspecified" and target.type == "unspecified":
            target.type = a.type
        if a.description and a.description not in target.description:
            target.description = f"{target.description} | {a.description}".strip(" |")
        for w in a.warnings:
            if w not in target.warnings:
                target.warnings.append(w)
        if target.vlm_bbox is None:
            target.vlm_bbox, target.vlm_bbox_iou = a.vlm_bbox, a.vlm_bbox_iou
        if target.related_bbox is None and a.related_bbox is not None:
            target.related_element_id, target.related_bbox = a.related_element_id, a.related_bbox
    return merged


def detect_anomalies(
    bundle: dict[str, Any],
    vlm_response: str | dict | list | None = None,
    *,
    coord_space: str = SPACE_AUTO,
    image_size: tuple[float, float] | None = None,
    min_iou: float = 0.3,
    min_confidence: float = 0.0,
    context_file: str = "",
) -> DetectionResult:
    """Find the anomalous components and their bounding boxes.

    bundle        parsed Week 2 `context.json`
    vlm_response  the VLM's reply (text, or decoded JSON). `None` = heuristic mode.
    coord_space   how to read bare numbers from the VLM: auto | css | normalized | normalized1000
    image_size    (w, h) of the image the VLM saw, if it was downscaled from the screenshot
    min_iou       minimum overlap to snap a bare VLM box onto a DOM element
    """
    if coord_space not in SPACES:
        raise ValueError(f"coord_space must be one of {SPACES}, got {coord_space!r}")
    idx = ContextIndex(bundle)
    result = DetectionResult(
        context_file=context_file, viewport=idx.viewport, document=idx.doc_size,
        mode=MODE_HEURISTIC if vlm_response is None else MODE_VLM,
    )

    if vlm_response is None:
        findings = findings_from_hints(idx)
        if not findings:
            result.warnings.append("Heuristic mode: the page has no layout hints, so nothing was flagged.")
    else:
        findings = parse_vlm_response(vlm_response)
        if not findings:
            result.warnings.append(
                "The VLM response contained no readable findings (no JSON list, element ids or boxes). "
                "Check the reply format; see `omnisight anomaly-prompt` for the expected schema."
            )

    built: list[Anomaly] = []
    for f in findings:
        a = _build(f, idx, coord_space=coord_space, image_size=image_size, min_iou=min_iou)
        if a is None:
            result.warnings.append(f"Finding #{f.index} could not be located and was dropped: {f.description[:80]!r}")
            continue
        built.append(a)

    anomalies = [a for a in _merge(built) if a.confidence >= min_confidence]
    for a in anomalies:
        a.score = SEVERITY_WEIGHT[a.severity] * a.confidence
    anomalies.sort(key=lambda a: (-a.score, a.bbox.y, a.bbox.x))
    for n, a in enumerate(anomalies, 1):
        a.id, a.rank = f"A{n}", n
    result.anomalies = anomalies

    if result.mode == MODE_VLM:
        covered = {a.element_id for a in anomalies if a.element_id is not None}
        covered |= {a.related_element_id for a in anomalies if a.related_element_id is not None}
        for h in idx.hints.values():
            eid = h.get("element_id")
            # an overlap-style hint involves two elements; a finding on either one confirms it
            confirmed = eid in covered or (h.get("related_id") is not None and h["related_id"] in covered)
            if h.get("severity") in ("high", "medium") and not confirmed and eid in idx.boxes:
                result.unconfirmed_hints.append({
                    **_hint_summary(h), "element_id": eid,
                    "selector": idx.elements[eid].get("selector"), "bbox": idx.boxes[eid].to_dict(),
                })
    return result


__all__ = ["detect_anomalies", "findings_from_hints", "normalize_severity", "BBox"]
