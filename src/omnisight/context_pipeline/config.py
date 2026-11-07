"""Pipeline configuration: dataclasses plus YAML loading."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, replace
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Viewport:
    name: str
    width: int
    height: int
    is_mobile: bool = False

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Viewport":
        return cls(
            name=str(d["name"]),
            width=int(d["width"]),
            height=int(d["height"]),
            is_mobile=bool(d.get("is_mobile", False)),
        )


DEFAULT_VIEWPORTS = (
    Viewport("desktop", 1440, 900),
    Viewport("tablet", 768, 1024),
    Viewport("mobile", 375, 812, is_mobile=True),
)

# Computed-style properties captured per element (defaults are dropped).
DEFAULT_STYLE_PROPS = (
    "display", "position", "top", "right", "bottom", "left", "z-index",
    "min-width", "max-width", "min-height", "max-height",
    "margin", "padding",
    "color", "background-color", "background-image", "opacity", "visibility",
    "font-family", "font-size", "font-weight", "line-height", "text-align",
    "text-overflow", "white-space", "word-break", "overflow-x", "overflow-y",
    "flex-direction", "flex-wrap", "justify-content", "align-items", "gap",
    "grid-template-columns", "float", "object-fit",
    "border", "border-radius", "box-shadow", "transform", "cursor",
)


@dataclass(frozen=True)
class PipelineConfig:
    # --- where things go -------------------------------------------------
    output_dir: str = "outputs"

    # --- browser / page loading -----------------------------------------
    viewports: tuple[Viewport, ...] = DEFAULT_VIEWPORTS
    wait_until: str = "load"            # load | domcontentloaded | networkidle | commit
    timeout_ms: int = 30_000
    wait_for_selector: str | None = None  # e.g. "#root > *" for React apps
    extra_wait_ms: int = 300              # settle time after load
    scroll_to_load: bool = True           # trigger lazy-loaded content
    device_scale_factor: float = 1.0      # screenshots are written in CSS px
    headless: bool = True

    # --- screenshots -----------------------------------------------------
    capture_viewport_shot: bool = True    # above-the-fold
    capture_full_page: bool = True
    tile_tall_pages: bool = True          # slice tall pages into VLM-friendly tiles
    tile_height: int = 1100
    tile_overlap: int = 100
    max_tiles: int = 8
    crop_hinted_elements: int = 8         # zoomed crops of the worst suspects
    crop_padding: int = 24
    annotate: str = "hinted"              # hinted | none
    max_image_dim: int = 8000             # safety clamp for huge pages

    # --- HTML / CSS context ---------------------------------------------
    max_elements: int = 400
    max_hints: int = 60
    max_rules: int = 3000
    max_text_len: int = 120
    max_html_chars: int = 40_000
    max_css_chars: int = 30_000
    style_props: tuple[str, ...] = DEFAULT_STYLE_PROPS

    # --- rendered VLM context -------------------------------------------
    max_context_chars: int = 60_000       # ~15k tokens
    suspect_detail_limit: int = 15

    def with_overrides(self, **overrides: Any) -> "PipelineConfig":
        clean = {k: v for k, v in overrides.items() if v is not None}
        return replace(self, **clean)


_FIELD_NAMES = {f.name for f in fields(PipelineConfig)}


def load_config(path: str | Path | None = None, **overrides: Any) -> PipelineConfig:
    """Load config from YAML (optional) and apply keyword overrides."""
    data: dict[str, Any] = {}
    if path:
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        if not isinstance(raw, dict):
            raise ValueError(f"{path}: top level must be a mapping")
        unknown = set(raw) - _FIELD_NAMES - {"targets"}
        if unknown:
            raise ValueError(f"{path}: unknown config keys: {sorted(unknown)}")
        data = {k: v for k, v in raw.items() if k in _FIELD_NAMES}
        if "viewports" in data:
            data["viewports"] = tuple(Viewport.from_dict(v) for v in data["viewports"])
        if "style_props" in data:
            data["style_props"] = tuple(data["style_props"])
    cfg = PipelineConfig(**data)
    return cfg.with_overrides(**overrides)


def load_targets(path: str | Path) -> list[str]:
    """Read the optional `targets:` list from a config file."""
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    targets = raw.get("targets") or []
    return [str(t) for t in targets]
