"""Turn a VLM's analysis into `RawFinding` objects.

VLMs rarely return exactly the schema you asked for, so the parser is lenient:

* JSON anywhere in the reply (bare, in a ```json fence, or after chatter), as
  `{"anomalies": [...]}`, a bare list, or one object
* many key aliases (`bbox`/`bounding_box`/`box`, `element_id`/`el`, ...)
* free text such as ``el#11 ... [556, 315, 646, 357]`` or ``x=556 y=315 w=90 h=42``

Nothing here touches the DOM; linking findings to elements is `resolver.py`.
"""

from __future__ import annotations

import json
import re
from typing import Any

from omnisight.anomaly_pipeline.models import RawFinding

_LIST_KEYS = ("anomalies", "defects", "findings", "issues", "detections", "results", "problems", "components")
_BBOX_KEYS = ("bbox", "bounding_box", "bounding_box_2d", "box", "box_2d", "bbox_2d", "coordinates", "coords", "location")
_SEVERITY_MAP = {
    "critical": "high", "severe": "high", "major": "high", "high": "high", "serious": "high",
    "medium": "medium", "moderate": "medium", "med": "medium", "warning": "medium",
    "low": "low", "minor": "low", "info": "low", "trivial": "low", "cosmetic": "low",
}
KNOWN_TYPES = (
    "text-clipped", "text-overflow", "clipped-by-ancestor", "container-overflow", "viewport-overflow",
    "horizontal-scroll", "overlap", "occluded", "overlay-covers-content", "low-contrast", "tiny-text",
    "small-tap-target", "empty-interactive", "image-broken", "image-distorted", "image-missing-alt",
    "offscreen-content", "misalignment", "inconsistent-spacing", "wrong-color",
)

_NUM = r"-?\d+(?:\.\d+)?"


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def normalize_severity(value: Any) -> str | None:
    if value is None:
        return None
    return _SEVERITY_MAP.get(str(value).strip().lower())


def _as_int(v: Any) -> int | None:
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, float) and v.is_integer():
        return int(v)
    if isinstance(v, str):
        m = re.search(r"\d+", v)
        if m:
            return int(m.group())
    return None


def _as_float(v: Any) -> float | None:
    """Confidence as 0..1. Accepts 0.85, 85, "85%"."""
    if isinstance(v, bool) or v is None:
        return None
    s = str(v).strip()
    pct = s.endswith("%")
    try:
        f = float(s.rstrip("%"))
    except ValueError:
        return None
    if pct or 1.0 < f <= 100.0:
        f /= 100.0
    return f if 0.0 <= f <= 1.0 else None


def _first(d: dict[str, Any], *keys: str) -> Any:
    low = {str(k).lower(): v for k, v in d.items()}
    for k in keys:
        if k in low and low[k] not in (None, "", []):
            return low[k]
    return None


# --------------------------------------------------------------------------
# JSON path
# --------------------------------------------------------------------------

def _json_candidates(text: str) -> list[Any]:
    """All JSON values that can be decoded from `text` (fenced blocks first)."""
    found: list[Any] = []
    for m in re.finditer(r"```(?:json|JSON)?\s*\n(.*?)```", text, re.DOTALL):
        try:
            found.append(json.loads(m.group(1)))
        except json.JSONDecodeError:
            pass
    if found:
        return found
    dec = json.JSONDecoder()
    i = 0
    while i < len(text):
        if text[i] in "[{":
            try:
                val, end = dec.raw_decode(text, i)
            except json.JSONDecodeError:
                i += 1
                continue
            found.append(val)
            i = end
        else:
            i += 1
    return found


def _looks_like_finding(d: Any) -> bool:
    if not isinstance(d, dict):
        return False
    low = {str(k).lower() for k in d}
    keys = set(_BBOX_KEYS) | {"element_id", "el", "element", "hint_id", "selector", "css_selector", "description",
                              "type", "defect_type", "issue", "text", "visible_text"}
    return bool(low & keys)


def _finding_list(value: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Locate the list of finding dicts inside a decoded JSON value, plus top-level metadata."""
    meta: dict[str, Any] = {}
    if isinstance(value, list):
        return [v for v in value if _looks_like_finding(v)], meta
    if isinstance(value, dict):
        low = {str(k).lower(): v for k, v in value.items()}
        meta = {k: low[k] for k in ("coordinate_space", "coord_space", "coordinate_system", "bbox_format") if k in low}
        for k in _LIST_KEYS:
            if isinstance(low.get(k), list):
                return [v for v in low[k] if _looks_like_finding(v)], meta
        for k in ("anomalous_component", "anomaly", "primary", "primary_anomaly", "component"):
            if _looks_like_finding(low.get(k)):
                return [low[k]], meta
        if _looks_like_finding(value):
            return [value], meta
        for v in value.values():          # one level of nesting, e.g. {"analysis": {"defects": [...]}}
            if isinstance(v, (dict, list)):
                lst, m2 = _finding_list(v)
                if lst:
                    return lst, {**m2, **meta}
    return [], meta


def _space_from(token: Any) -> str | None:
    if not token:
        return None
    t = str(token).strip().lower().replace("-", "_").replace(" ", "_")
    if "1000" in t:
        return "normalized1000"
    if t.startswith("norm") or t in ("relative", "unit", "0_1", "fraction"):
        return "normalized"
    if t in ("css", "css_px", "px", "pixel", "pixels", "image", "image_px"):
        return "css"
    return None


def _format_from(token: Any) -> str | None:
    if not token:
        return None
    t = str(token).strip().lower().replace("-", "").replace("_", "")
    if t in ("xyxy", "corners", "ltrb", "x1y1x2y2"):
        return "xyxy"
    if t in ("xywh", "ltwh", "size"):
        return "xywh"
    return None


def _from_dict(i: int, d: dict[str, Any], meta: dict[str, Any]) -> RawFinding:
    bbox_raw = _first(d, *_BBOX_KEYS)
    if bbox_raw is None and _first(d, "x", "x1", "xmin", "left") is not None:
        bbox_raw = d                      # the finding dict *is* the box
    if isinstance(bbox_raw, str):         # "[10, 20, 30, 40]" or "x=.. y=.. w=.. h=.."
        _, box, fmt = _scan_text_bbox(bbox_raw)
        bbox_raw, fmt_from_str = box, fmt
    else:
        fmt_from_str = None
    ref = _first(d, "element_id", "el", "element", "el_id", "omni_id", "data-omni-id")
    related = _first(d, "related_element_id", "related_id", "related_element", "other_element_id")
    return RawFinding(
        index=i,
        description=str(_first(d, "description", "summary", "reason", "explanation", "message", "details", "issue") or "").strip(),
        type=(str(_first(d, "type", "defect_type", "category", "kind", "label", "name") or "").strip().lower().replace(" ", "-") or None),
        severity=normalize_severity(_first(d, "severity", "priority", "impact")),
        confidence=_as_float(_first(d, "confidence", "score", "probability")),
        element_id=_as_int(ref),
        related_element_id=_as_int(related),
        hint_id=_as_int(_first(d, "hint_id", "hint", "h")),
        selector=(str(_first(d, "selector", "css_selector", "dom_selector") or "").strip() or None),
        text=(str(_first(d, "text", "visible_text", "element_text") or "").strip() or None),
        bbox_raw=bbox_raw,
        bbox_format=_format_from(_first(d, "bbox_format", "format")) or fmt_from_str or _format_from(meta.get("bbox_format")),
        coord_space=_space_from(_first(d, "coordinate_space", "coord_space", "coordinate_system"))
        or _space_from(meta.get("coordinate_space") or meta.get("coord_space") or meta.get("coordinate_system")),
    )


# --------------------------------------------------------------------------
# free-text path
# --------------------------------------------------------------------------

_RE_KV_XYWH = re.compile(rf"\bx\s*[=:]\s*({_NUM})[\s,;]+y\s*[=:]\s*({_NUM})[\s,;]+(?:w|width)\s*[=:]\s*({_NUM})[\s,;]+(?:h|height)\s*[=:]\s*({_NUM})", re.I)
_RE_KV_XYXY = re.compile(rf"\bx1\s*[=:]\s*({_NUM})[\s,;]+y1\s*[=:]\s*({_NUM})[\s,;]+x2\s*[=:]\s*({_NUM})[\s,;]+y2\s*[=:]\s*({_NUM})", re.I)
_RE_BOXTAG = re.compile(rf"\(\s*({_NUM})\s*,\s*({_NUM})\s*\)\s*,?\s*\(\s*({_NUM})\s*,\s*({_NUM})\s*\)")
_RE_LIST4 = re.compile(rf"[\[\(]\s*({_NUM})\s*,\s*({_NUM})\s*,\s*({_NUM})\s*,\s*({_NUM})\s*[\]\)]")
_RE_EL = re.compile(r"\bel#(\d+)|data-omni-id=[\"']?(\d+)|\belement[\s_-]*(?:id)?\s*[#:=]\s*(\d+)", re.I)
_RE_HINT = re.compile(r"\bH(\d+)\b")
_RE_TICKS = re.compile(r"`([^`]{3,200})`")
_RE_BULLET = re.compile(r"^\s*(?:[-*•]|\d+[.)]|#{2,4})\s+")
_RE_SEV = re.compile(r"\b(critical|severe|major|high|medium|moderate|low|minor)\b", re.I)


def _scan_text_bbox(chunk: str) -> tuple[str, Any, str | None]:
    """Find the first box in `chunk`. Returns (chunk_without_it, raw_numbers_or_None, format_or_None)."""
    for rx, fmt in ((_RE_KV_XYXY, "xyxy"), (_RE_KV_XYWH, "xywh"), (_RE_BOXTAG, "xyxy"), (_RE_LIST4, None)):
        m = rx.search(chunk)
        if m:
            return chunk, [float(g) for g in m.groups()], fmt
    return chunk, None, None


_FILE_EXT = re.compile(r"\.(png|jpe?g|gif|webp|json|md|css|html?|js|py)$", re.I)


def _looks_like_selector(s: str) -> bool:
    s = s.strip()
    return bool(s) and not _FILE_EXT.search(s) and bool(re.search(r"[>.#\[]", s) or re.fullmatch(r"[a-z][a-z0-9]*", s))


def _split_chunks(text: str) -> list[str]:
    chunks: list[str] = []
    cur: list[str] = []
    for line in text.splitlines():
        if not line.strip():
            if cur:
                chunks.append(" ".join(cur))
                cur = []
            continue
        if _RE_BULLET.match(line) and cur:
            chunks.append(" ".join(cur))
            cur = []
        cur.append(line.strip())
    if cur:
        chunks.append(" ".join(cur))
    return chunks


def _from_text_chunk(i: int, chunk: str) -> RawFinding | None:
    _, box, fmt = _scan_text_bbox(chunk)
    refs = [int(next(g for g in m.groups() if g)) for m in _RE_EL.finditer(chunk)]
    hints = [int(h) for h in _RE_HINT.findall(chunk)]
    ticks = [t.strip() for t in _RE_TICKS.findall(chunk) if _looks_like_selector(t)]
    if box is None and not refs and not hints and not ticks:
        return None
    sev = _RE_SEV.search(chunk)
    low = chunk.lower()
    ftype = next((t for t in KNOWN_TYPES if t in low), None)
    quoted = re.search(r"\"([^\"]{2,80})\"", chunk)
    desc = _RE_BULLET.sub("", chunk).strip()
    return RawFinding(
        index=i,
        description=desc,
        type=ftype,
        severity=normalize_severity(sev.group(1)) if sev else None,
        element_id=refs[0] if refs else None,
        related_element_id=refs[1] if len(refs) > 1 and refs[1] != refs[0] else None,
        hint_id=hints[0] if hints else None,
        selector=ticks[0] if ticks else None,
        text=quoted.group(1) if quoted else None,
        bbox_raw=box,
        bbox_format=fmt,
    )


# --------------------------------------------------------------------------
# public entry point
# --------------------------------------------------------------------------

def parse_vlm_response(response: str | dict | list) -> list[RawFinding]:
    """Parse a VLM reply into raw findings (possibly empty).

    `response` may be the reply text, or already-decoded JSON.
    """
    if isinstance(response, (dict, list)):
        items, meta = _finding_list(response)
        return [_from_dict(i, d, meta) for i, d in enumerate(items, 1)]

    text = str(response)
    best: tuple[list[dict[str, Any]], dict[str, Any]] = ([], {})
    for cand in _json_candidates(text):
        items, meta = _finding_list(cand)
        if len(items) > len(best[0]):
            best = (items, meta)
    if best[0]:
        return [_from_dict(i, d, best[1]) for i, d in enumerate(best[0], 1)]

    out: list[RawFinding] = []
    for chunk in _split_chunks(text):
        f = _from_text_chunk(len(out) + 1, chunk)
        if f:
            out.append(f)
    return out
