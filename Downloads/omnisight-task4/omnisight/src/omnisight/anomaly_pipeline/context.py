"""Load a Week 2 `context.json` bundle and index it for lookups."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from omnisight.anomaly_pipeline.bbox import BBox


def load_bundle(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if p.is_dir():
        p = p / "context.json"
    bundle = json.loads(p.read_text(encoding="utf-8"))
    if "elements" not in bundle or "viewport" not in bundle:
        raise ValueError(f"{p} does not look like an OmniSight context.json (missing 'elements'/'viewport').")
    return bundle


def _norm_selector(s: str) -> str:
    return re.sub(r"\s*>\s*", " > ", re.sub(r"\s+", " ", s.strip()))


class ContextIndex:
    """Lookup tables over one bundle. Element boxes are CSS px, full-page origin."""

    def __init__(self, bundle: dict[str, Any]):
        self.bundle = bundle
        self.elements: dict[int, dict[str, Any]] = {e["id"]: e for e in bundle["elements"]}
        self.boxes: dict[int, BBox] = {}
        for eid, e in self.elements.items():
            b = e.get("bbox")
            if b and b.get("w", 0) > 0 and b.get("h", 0) > 0:
                self.boxes[eid] = BBox.from_dict(b)
        self.hints: dict[int, dict[str, Any]] = {h["id"]: h for h in bundle.get("hints", [])}
        self.by_selector: dict[str, int] = {}
        for eid, e in self.elements.items():
            self.by_selector.setdefault(_norm_selector(e.get("selector", "")), eid)

        doc = bundle.get("page", {}).get("document") or {}
        shot = (bundle.get("screenshots") or {}).get("full_page") or {}
        self.doc_w = float(doc.get("scroll_width") or shot.get("width") or bundle["viewport"]["width"])
        self.doc_h = float(doc.get("scroll_height") or shot.get("height") or bundle["viewport"]["height"])
        self.viewport = bundle["viewport"]

    @property
    def doc_size(self) -> tuple[float, float]:
        return (self.doc_w, self.doc_h)

    def element_by_selector(self, selector: str | None) -> int | None:
        if not selector:
            return None
        return self.by_selector.get(_norm_selector(selector))

    def hints_for(self, element_id: int) -> list[dict[str, Any]]:
        return [h for h in self.hints.values() if h.get("element_id") == element_id or h.get("related_id") == element_id]

    def elements_with_text(self, text: str) -> list[int]:
        t = " ".join(text.split()).lower()
        if len(t) < 3:
            return []
        hits = [eid for eid, e in self.elements.items() if t in " ".join((e.get("text") or "").split()).lower()]
        # the most specific (smallest) elements first
        return sorted(hits, key=lambda i: self.boxes[i].area if i in self.boxes else float("inf"))
