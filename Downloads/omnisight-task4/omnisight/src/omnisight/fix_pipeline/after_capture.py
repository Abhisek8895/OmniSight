"""Task 2: render the repaired page with Playwright and capture before/after screenshots.

Two ways to produce the "after" page:

* **live CSS** (default) - load the original page, take the *before* shot, apply
  the validated CSS fixes to the same live DOM (Task 1), wait for the page to
  re-render, take the *after* shot. Same load, same viewport, same scroll state,
  so the only difference between the two images is the fix.
* **repaired page** - load an already-repaired HTML file/URL in a fresh page for
  the *after* shot (use this if Task 1 writes a repaired HTML file to disk).

Nothing in here raises for expected failures (bad page, CSS that does not apply,
screenshot errors); the outcome is recorded in `fix_result.json` instead.
"""

from __future__ import annotations

import json
import shutil
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from playwright.sync_api import Browser, Page

import omnisight
from omnisight.context_pipeline.browser import (
    browser_session,
    open_page,
    resolve_target,
    slugify,
)
from omnisight.context_pipeline.config import PipelineConfig, Viewport
from omnisight.fix_pipeline import compare
from omnisight.fix_pipeline.css_applier import CssFixApplier, DomCssApplier
from omnisight.fix_pipeline.models import (
    STATUS_APPLY_FAILED,
    STATUS_CAPTURE_FAILED,
    STATUS_OK,
    STATUS_RENDER_FAILED,
    ApplyResult,
    CssFix,
)

RESULT_SCHEMA_VERSION = "1.0"
# Files written into `<out_dir>/`. Keep these stable: later stages load them by name.
BEFORE_VIEWPORT = "before_viewport.png"
BEFORE_FULL = "before_full.png"
AFTER_VIEWPORT = "after_viewport.png"
AFTER_FULL = "after_full.png"
COMPARISON = "comparison.png"
DIFF = "diff.png"
APPLIED_CSS = "applied_fix.css"
RESULT_JSON = "fix_result.json"



@dataclass(frozen=True)
class AfterFixOptions:
    capture_viewport: bool = True
    capture_full_page: bool = True
    settle_ms: int = 300                 # extra wait after the page re-renders
    networkidle_timeout_ms: int = 3000   # best effort; pages that never idle are fine
    capture_on_apply_failure: bool = False  # shoot "after" even if no fix applied
    make_comparison: bool = True
    make_diff: bool = True
    diff_threshold: int = 16             # per-channel tolerance for "changed" pixels
    subdir: str = "fix"                  # output goes to <slug>/<viewport>/<subdir>/


# --------------------------------------------------------------------------
# Waiting and capturing
# --------------------------------------------------------------------------
_JS_SETTLE = """async () => {
    if (document.fonts && document.fonts.ready) { await document.fonts.ready; }
    await Promise.all(Array.from(document.images).filter(i => !i.complete).map(i =>
        new Promise(r => { i.onload = i.onerror = r; setTimeout(r, 2000); })));
    // two animation frames: styles applied -> layout done -> painted
    await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
    window.scrollTo(0, 0);
    return true;
}"""


def wait_for_render(page: Page, opts: AfterFixOptions, cfg: PipelineConfig) -> None:
    """Block until the page has finished rendering after load or after a CSS change."""
    try:
        page.wait_for_load_state("networkidle", timeout=opts.networkidle_timeout_ms)
    except Exception:
        pass  # long-polling / analytics pages never go idle; that is fine
    if cfg.wait_for_selector:
        page.wait_for_selector(cfg.wait_for_selector, timeout=cfg.timeout_ms)
    page.evaluate(_JS_SETTLE)
    if opts.settle_ms:
        page.wait_for_timeout(opts.settle_ms)


def _image_meta(path: Path, root: Path) -> dict:
    from PIL import Image

    with Image.open(path) as im:
        w, h = im.size
    return {"path": path.relative_to(root).as_posix(), "width": w, "height": h}


def shoot(page: Page, out_dir: Path, prefix: str, cfg: PipelineConfig, opts: AfterFixOptions) -> dict:
    """Write `<prefix>_viewport.png` / `<prefix>_full.png`.

    Same parameters as the Week 2 capture (CSS pixels, animations off, clamped
    to `max_image_dim`), so before and after are directly comparable.
    """
    shots: dict = {}
    page.evaluate("window.scrollTo(0, 0)")
    if opts.capture_viewport:
        p = out_dir / f"{prefix}_viewport.png"
        page.screenshot(path=str(p), full_page=False, animations="disabled", scale="css")
        shots["viewport"] = _image_meta(p, out_dir)
    if opts.capture_full_page:
        dims = page.evaluate(
            "() => ({w: document.documentElement.scrollWidth, h: document.documentElement.scrollHeight})"
        )
        width = min(max(dims["w"], 1), cfg.max_image_dim)
        height = min(max(dims["h"], 1), cfg.max_image_dim)
        p = out_dir / f"{prefix}_full.png"
        page.screenshot(
            path=str(p), full_page=True, animations="disabled", scale="css",
            clip={"x": 0, "y": 0, "width": width, "height": height},
        )
        shots["full_page"] = {
            **_image_meta(p, out_dir),
            "truncated": dims["h"] > cfg.max_image_dim or dims["w"] > cfg.max_image_dim,
        }
    return shots


# --------------------------------------------------------------------------
# One target x one viewport
# --------------------------------------------------------------------------
def capture_before_after(
    browser: Browser,
    target: str,
    viewport: Viewport,
    cfg: PipelineConfig,
    out_dir: Path,
    *,
    fixes: Sequence[CssFix] | None = None,
    repaired_target: str | None = None,
    applier: CssFixApplier | None = None,
    options: AfterFixOptions | None = None,
    before_image: str | Path | None = None,
) -> dict:
    """Capture before/after screenshots for one target at one viewport.

    Pass either `fixes` (live CSS mode) or `repaired_target` (repaired page mode).
    `applier` defaults to `DomCssApplier`; Task 1 can pass its own implementation.
    `before_image` reuses an existing screenshot (e.g. the Week 2 baseline
    `screenshot_full.png`) instead of taking a fresh *before* shot.

    Returns the result dict that is also written to `fix_result.json`.
    """
    if bool(fixes) == bool(repaired_target):
        raise ValueError("Pass exactly one of `fixes` or `repaired_target`.")
    opts = options or AfterFixOptions()
    applier = applier or DomCssApplier()
    out_dir.mkdir(parents=True, exist_ok=True)

    result: dict = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "tool": {
            "name": "omnisight",
            "version": omnisight.__version__,
            "stage": "week3-after-fix-screenshot",
            "browser": f"chromium {browser.version}",
        },
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "target": {"input": target, "repaired": repaired_target},
        "viewport": {
            "name": viewport.name, "width": viewport.width,
            "height": viewport.height, "is_mobile": viewport.is_mobile,
        },
        "mode": "repaired-page" if repaired_target else "live-css",
        "status": STATUS_OK,
        "stage": "load_before",
        "error": None,
        "apply": None,
        "screenshots": {"before": {}, "after": {}},
        "comparison": None,
        "diagnostics": {},
    }
    before_shots: dict = result["screenshots"]["before"]
    after_shots: dict = result["screenshots"]["after"]

    def fail(status: str, exc: BaseException) -> None:
        result["status"] = status
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["trace"] = traceback.format_exc(limit=4)

    try:
        url = resolve_target(target)
        with open_page(browser, url, viewport, cfg) as (page, _ctx, diagnostics):
            wait_for_render(page, opts, cfg)
            result["diagnostics"] = diagnostics.to_dict()

            # ---- BEFORE ------------------------------------------------
            result["stage"] = "capture_before"
            if before_image:
                dest = out_dir / BEFORE_FULL
                if Path(before_image).resolve() != dest.resolve():
                    shutil.copyfile(before_image, dest)
                before_shots["full_page"] = {**_image_meta(dest, out_dir), "reused_from": str(before_image)}
            else:
                before_shots.update(shoot(page, out_dir, "before", cfg, opts))

            # ---- APPLY FIX (live CSS mode) -----------------------------
            if fixes:
                result["stage"] = "apply_fix"
                apply_result: ApplyResult = applier.apply(page, fixes)
                result["apply"] = apply_result.to_dict()
                if apply_result.applied_css:
                    (out_dir / APPLIED_CSS).write_text(apply_result.applied_css, encoding="utf-8")
                if not apply_result.ok and not opts.capture_on_apply_failure:
                    result["status"] = STATUS_APPLY_FAILED
                    result["error"] = "No CSS fix could be applied; see `apply.outcomes`."
                else:
                    result["stage"] = "capture_after"
                    wait_for_render(page, opts, cfg)
                    after_shots.update(shoot(page, out_dir, "after", cfg, opts))
                    result["diagnostics_after"] = diagnostics.to_dict()

        # ---- AFTER (repaired page mode) --------------------------------
        if repaired_target and result["status"] == STATUS_OK:
            result["stage"] = "load_after"
            with open_page(browser, resolve_target(repaired_target), viewport, cfg) as (page, _c, diag2):
                wait_for_render(page, opts, cfg)
                result["stage"] = "capture_after"
                after_shots.update(shoot(page, out_dir, "after", cfg, opts))
                result["diagnostics_after"] = diag2.to_dict()

    except Exception as exc:
        stage = result["stage"]
        fail(STATUS_CAPTURE_FAILED if stage.startswith("capture") else STATUS_RENDER_FAILED, exc)

    # ---- COMPARE -------------------------------------------------------
    key = "full_page" if "full_page" in before_shots and "full_page" in after_shots else "viewport"
    if result["status"] == STATUS_OK and key in before_shots and key in after_shots:
        try:
            b_path = out_dir / before_shots[key]["path"]
            a_path = out_dir / after_shots[key]["path"]
            diff_path = out_dir / DIFF if opts.make_diff else None
            result["comparison"] = compare.pixel_diff(b_path, a_path, diff_path, opts.diff_threshold)
            result["comparison"]["compared"] = key
            if opts.make_diff:
                result["screenshots"]["diff"] = _image_meta(diff_path, out_dir)
            if opts.make_comparison:
                cmp_path = compare.side_by_side(b_path, a_path, out_dir / COMPARISON)
                result["screenshots"]["comparison"] = _image_meta(cmp_path, out_dir)
        except Exception as exc:  # screenshots are saved; comparison is a bonus
            result["comparison"] = {"error": f"{type(exc).__name__}: {exc}"}

    if result["status"] == STATUS_OK:
        result["stage"] = "done"
    result["dir"] = out_dir.as_posix()
    (out_dir / RESULT_JSON).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


# --------------------------------------------------------------------------
# Many targets x many viewports
# --------------------------------------------------------------------------
def run_after_fix(
    targets: list[str],
    cfg: PipelineConfig,
    *,
    fixes: Sequence[CssFix] | None = None,
    repaired_target: str | None = None,
    viewports: list[Viewport] | None = None,
    output_dir: str | Path | None = None,
    applier: CssFixApplier | None = None,
    options: AfterFixOptions | None = None,
    before_image: str | Path | None = None,
) -> list[dict]:
    """Run `capture_before_after` for every target and viewport.

    Writes `<out>/<slug>/<viewport>/<subdir>/...` plus `<out>/<slug>/fix_manifest.json`.
    A failure in one viewport is recorded and the run continues.
    (`repaired_target` and `before_image` only make sense for a single target.)
    """
    opts = options or AfterFixOptions()
    out_root = Path(output_dir or cfg.output_dir)
    vps = viewports or list(cfg.viewports)
    results: list[dict] = []

    with browser_session(cfg) as browser:
        for target in targets:
            slug = slugify(target)
            entry: dict = {"target": target, "slug": slug, "viewports": {}}
            for vp in vps:
                out_dir = out_root / slug / vp.name / opts.subdir
                try:
                    res = capture_before_after(
                        browser, target, vp, cfg, out_dir,
                        fixes=fixes, repaired_target=repaired_target,
                        applier=applier, options=opts, before_image=before_image,
                    )
                    entry["viewports"][vp.name] = {
                        "dir": out_dir.as_posix(),
                        "result": (out_dir / RESULT_JSON).as_posix(),
                        "status": res["status"],
                        "error": res["error"],
                        "visible_change": (res.get("comparison") or {}).get("visible_change"),
                    }
                except Exception as exc:  # e.g. invalid arguments; never abort the batch
                    entry["viewports"][vp.name] = {
                        "status": STATUS_RENDER_FAILED,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
            (out_root / slug).mkdir(parents=True, exist_ok=True)
            (out_root / slug / "fix_manifest.json").write_text(
                json.dumps(entry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            results.append(entry)
    return results
