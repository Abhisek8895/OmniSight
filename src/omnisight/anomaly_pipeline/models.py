"""Data contract for the anomaly-detection stage.

Input : a Week 2 `context.json` bundle + the VLM's analysis (JSON or free text).
Output: `DetectionResult` - ranked anomalies, each tied to a UI component and a
        bounding box in CSS pixels (origin top-left of the full page).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from omnisight.anomaly_pipeline.bbox import BBox

SEVERITIES = ("high", "medium", "low")
SEVERITY_WEIGHT = {"high": 3.0, "medium": 2.0, "low": 1.0}

# how a finding was tied to a DOM element
RES_ELEMENT_ID = "element_id"
RES_HINT_ID = "hint_id"
RES_SELECTOR = "selector"
RES_BBOX_IOU = "bbox_iou"
RES_BBOX_CENTER = "bbox_center"
RES_TEXT = "text"
RES_NONE = "unresolved"

# where the reported bbox comes from
SRC_DOM = "dom"            # measured in the browser for the matched element (exact)
SRC_VLM = "vlm"            # taken from the model's own box (no element matched)

MODE_VLM = "vlm"
MODE_HEURISTIC = "heuristic"


@dataclass
class RawFinding:
    """One defect as the VLM described it, before it is tied to the DOM."""

    index: int
    description: str = ""
    type: str | None = None
    severity: str | None = None
    confidence: float | None = None
    element_id: int | None = None
    related_element_id: int | None = None
    hint_id: int | None = None
    selector: str | None = None
    text: str | None = None
    bbox_raw: Any = None
    bbox_format: str | None = None
    coord_space: str | None = None
    source: str = MODE_VLM


@dataclass
class Anomaly:
    id: str                                  # "A1", "A2", ... by rank
    rank: int
    type: str
    severity: str
    confidence: float
    description: str
    bbox: BBox                               # CSS px, full-page origin
    bbox_source: str                         # SRC_DOM | SRC_VLM
    resolution: str                          # RES_*
    source: str = MODE_VLM
    element: dict[str, Any] | None = None    # matched component (from context.json)
    related_element_id: int | None = None
    related_bbox: BBox | None = None
    hints: list[dict[str, Any]] = field(default_factory=list)
    vlm_bbox: BBox | None = None
    vlm_bbox_iou: float | None = None
    merged_from: int = 1
    warnings: list[str] = field(default_factory=list)
    score: float = 0.0

    @property
    def element_id(self) -> int | None:
        return self.element["id"] if self.element else None

    def to_dict(self, doc_size: tuple[float, float]) -> dict[str, Any]:
        comp = None
        if self.element:
            e = self.element
            comp = {
                "element_id": e["id"],
                "selector": e.get("selector"),
                "tag": e.get("tag"),
                "text": e.get("text"),
                "html_snippet": e.get("html_snippet"),
                "in_viewport": e.get("in_viewport"),
                "rule_ids": e.get("rule_ids"),
                "flags": e.get("flags"),
            }
        return {
            "id": self.id,
            "rank": self.rank,
            "type": self.type,
            "severity": self.severity,
            "confidence": round(self.confidence, 3),
            "score": round(self.score, 3),
            "description": self.description,
            "source": self.source,
            "component": comp,
            "bbox": self.bbox.to_dict(),
            "bbox_normalized": self.bbox.normalized(*doc_size),
            "bbox_source": self.bbox_source,
            "resolution": self.resolution,
            "vlm_bbox": self.vlm_bbox.to_dict() if self.vlm_bbox else None,
            "vlm_bbox_iou": None if self.vlm_bbox_iou is None else round(self.vlm_bbox_iou, 3),
            "related": (
                {"element_id": self.related_element_id,
                 "bbox": self.related_bbox.to_dict() if self.related_bbox else None}
                if self.related_element_id is not None else None
            ),
            "hints": self.hints,
            "merged_from": self.merged_from,
            "warnings": self.warnings,
        }


@dataclass
class DetectionResult:
    context_file: str
    viewport: dict[str, Any]
    document: tuple[float, float]
    mode: str
    anomalies: list[Anomaly] = field(default_factory=list)
    unconfirmed_hints: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    files: dict[str, str] = field(default_factory=dict)

    @property
    def primary(self) -> Anomaly | None:
        return self.anomalies[0] if self.anomalies else None

    def to_dict(self) -> dict[str, Any]:
        doc = self.document
        return {
            "schema_version": "1.0",
            "tool": {"name": "omnisight", "stage": "anomaly-detection"},
            "context_file": self.context_file,
            "viewport": self.viewport,
            "document": {"w": doc[0], "h": doc[1]},
            "coordinate_system": "css_px, origin top-left of the full page (maps 1:1 onto screenshot_full.png)",
            "mode": self.mode,
            "primary": self.primary.to_dict(doc) if self.primary else None,
            "anomalies": [a.to_dict(doc) for a in self.anomalies],
            "unconfirmed_hints": self.unconfirmed_hints,
            "warnings": self.warnings,
            "files": self.files,
        }
