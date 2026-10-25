"""Orchestrates one capture: screenshots + HTML/CSS context -> output bundle."""

from __future__ import annotations

import json
import traceback
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import Browser

import omnisight
from omnisight.context_pipeline import screenshot as shots_mod
from omnisight.context_pipeline.browser import (
    browser_session,
    open_page,
    resolve_target,
    slugify,
)
from omnisight.context_pipeline.config import PipelineConfig, Viewport
from omnisight.context_pipeline.html_context import clean_html, extract_page_context, rules_to_css
from omnisight.context_pipeline.render import render_vlm_context

SCHEMA_VERSION = "1.0"


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def capture_context(
    browser: Browser,
    target: str,
    viewport: Viewport,
    cfg: PipelineConfig,
    out_dir: Path,
) -> dict:
    """Capture one target at one viewport and write the bundle into `out_dir`.

    Output layout::

        out_dir/
          context.json            full-fidelity bundle (the Week 3 input)
          vlm_context.md          budgeted text view for prompting
          page.cleaned.html       cleaned DOM snapshot
          styles.css              CSS rules that match the page
          screenshot_viewport.png above-the-fold
          screenshot_full.png     whole page
          screenshot_annotated.png  flagged elements boxed as H<n>
          tiles/  crops/          VLM-friendly slices and zoomed suspects
    """
    url = resolve_target(target)
    out_dir.mkdir(parents=True, exist_ok=True)

    with open_page(browser, url, viewport, cfg) as (page, _ctx, diagnostics):
        raw_shots = shots_mod.capture_raw(page, out_dir, cfg)
        extracted = extract_page_context(page, cfg)
        browser_version = browser.version

    elements: list[dict] = extracted["elements"]
    hints: list[dict] = extracted["hints"]
    rules: list[dict] = extracted["rules"]

    # --- HTML ----------------------------------------------------------
    flagged_ids = {h[k] for h in hints for k in ("element_id", "related_id") if h.get(k)}
    cleaned_html, snippets, html_info = clean_html(extracted["html"], cfg, flagged_ids)
    for el in elements:
        if el["id"] in snippets:
            el["html_snippet"] = snippets[el["id"]]

    # --- CSS -----------------------------------------------------------
    priority_rules = {rid for el in elements if el["id"] in flagged_ids for rid in el["rule_ids"]}
    css_text, kept_rule_ids = rules_to_css(rules, priority_rules, cfg.max_css_chars)
    stats = extracted["rule_stats"]
    css_stats = {
        "sheets": stats["sheets"],
        "total": stats["total"],
        "kept": len(kept_rule_ids),
        "matched": stats["kept"],
        "dropped_unmatched": stats["dropped_unmatched"],
        "unparsable": stats["unparsable"],
        "unavailable": stats["unavailable"],
        "keyframes": stats["keyframes"],
        "font_faces": stats["font_faces"],
    }

    # --- screenshots that depend on the element map ---------------------
    screenshots = dict(raw_shots)
    screenshots["tiles"] = shots_mod.make_tiles(out_dir, raw_shots, cfg)
    annotated = shots_mod.annotate(out_dir, raw_shots, elements, hints, cfg)
    if annotated:
        screenshots["annotated"] = annotated
    screenshots["crops"] = shots_mod.make_crops(out_dir, raw_shots, elements, hints, cfg)

    bundle = {
        "schema_version": SCHEMA_VERSION,
        "tool": {
            "name": "omnisight",
            "version": omnisight.__version__,
            "stage": "week2-screenshot-html-context",
            "browser": f"chromium {browser_version}",
        },
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "target": {"input": target, "url": extracted["page"]["url"]},
        "viewport": {
            "name": viewport.name,
            "width": viewport.width,
            "height": viewport.height,
            "is_mobile": viewport.is_mobile,
        },
        "page": extracted["page"],
        "screenshots": screenshots,
        "hints": hints,
        "elements": elements,
        "css": {
            "rules": [r for r in rules if r["id"] in set(kept_rule_ids)],
            "text": css_text,
            "stats": css_stats,
            "file": "styles.css",
        },
        "html": {"text": cleaned_html, "file": "page.cleaned.html", **html_info},
        "diagnostics": diagnostics.to_dict(),
        "vlm_context_file": "vlm_context.md",
    }

    # Rules referenced by elements but trimmed from the budgeted CSS are no longer resolvable.
    kept = set(kept_rule_ids)
    for el in elements:
        el["rule_ids"] = [r for r in el["rule_ids"] if r in kept]

    (out_dir / "page.cleaned.html").write_text(cleaned_html, encoding="utf-8")
    (out_dir / "styles.css").write_text(css_text, encoding="utf-8")
    (out_dir / "vlm_context.md").write_text(
        render_vlm_context(bundle, cfg.max_context_chars, cfg.suspect_detail_limit), encoding="utf-8"
    )
    _write_json(out_dir / "context.json", bundle)
    return bundle


def summarize(bundle: dict) -> dict:
    sev = {"high": 0, "medium": 0, "low": 0}
    for h in bundle["hints"]:
        sev[h["severity"]] += 1
    return {
        "viewport": bundle["viewport"]["name"],
        "document": f"{bundle['page']['document']['scroll_width']}x{bundle['page']['document']['scroll_height']}",
        "elements": len(bundle["elements"]),
        "css_rules": bundle["css"]["stats"]["kept"],
        "hints": sev,
    }


def run_pipeline(
    targets: list[str],
    cfg: PipelineConfig,
    viewports: list[Viewport] | None = None,
    output_dir: str | Path | None = None,
) -> list[dict]:
    """Capture every target at every viewport. Failures are recorded, not fatal."""
    out_root = Path(output_dir or cfg.output_dir)
    vps = viewports or list(cfg.viewports)
    results: list[dict] = []

    with browser_session(cfg) as browser:
        for target in targets:
            slug = slugify(target)
            entry: dict = {"target": target, "slug": slug, "viewports": {}}
            for vp in vps:
                out_dir = out_root / slug / vp.name
                try:
                    bundle = capture_context(browser, target, vp, cfg, out_dir)
                    entry["viewports"][vp.name] = {
                        "dir": out_dir.as_posix(),
                        "context": (out_dir / "context.json").as_posix(),
                        "summary": summarize(bundle),
                    }
                except Exception as exc:  # keep going; report at the end
                    entry["viewports"][vp.name] = {
                        "error": f"{type(exc).__name__}: {exc}",
                        "trace": traceback.format_exc(limit=4),
                    }
            (out_root / slug).mkdir(parents=True, exist_ok=True)
            _write_json(out_root / slug / "manifest.json", entry)
            results.append(entry)
    return results
