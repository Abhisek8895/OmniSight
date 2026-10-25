"""Browser session helpers: target resolution, page preparation, diagnostics."""

from __future__ import annotations

import re
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator
from urllib.parse import urlparse

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from omnisight.context_pipeline.config import PipelineConfig, Viewport


def resolve_target(target: str) -> str:
    """Turn a URL or local file path into something `page.goto` accepts."""
    parsed = urlparse(target)
    if parsed.scheme in ("http", "https", "file"):
        return target
    path = Path(target).expanduser()
    if not path.exists():
        raise FileNotFoundError(
            f"Target is neither a URL nor an existing file: {target!r}"
        )
    return path.resolve().as_uri()


def slugify(target: str) -> str:
    """Filesystem-safe name for a target, used for output folders."""
    parsed = urlparse(target)
    if parsed.scheme in ("http", "https"):
        raw = f"{parsed.netloc}{parsed.path}"
    elif parsed.scheme == "file":
        raw = Path(parsed.path).stem
    else:
        raw = Path(target).stem
    slug = re.sub(r"[^A-Za-z0-9]+", "-", raw).strip("-").lower()
    return slug or "page"


@dataclass
class Diagnostics:
    """Things that go wrong while loading a page and often *cause* UI defects."""

    console_errors: list[str] = field(default_factory=list)
    page_errors: list[str] = field(default_factory=list)
    failed_requests: list[dict] = field(default_factory=list)
    http_errors: list[dict] = field(default_factory=list)

    def attach(self, page: Page) -> None:
        page.on(
            "console",
            lambda m: self.console_errors.append(m.text[:300])
            if m.type in ("error", "warning") and len(self.console_errors) < 50
            else None,
        )
        page.on(
            "pageerror",
            lambda e: self.page_errors.append(str(e)[:300])
            if len(self.page_errors) < 50
            else None,
        )
        page.on(
            "requestfailed",
            lambda r: self.failed_requests.append(
                {
                    "url": r.url[:300],
                    "type": r.resource_type,
                    "error": (r.failure or "")[:120],
                }
            )
            if len(self.failed_requests) < 50
            else None,
        )
        page.on(
            "response",
            lambda r: self.http_errors.append(
                {"url": r.url[:300], "status": r.status, "type": r.request.resource_type}
            )
            if r.status >= 400 and len(self.http_errors) < 50
            else None,
        )

    def to_dict(self) -> dict:
        return {
            "console_errors": self.console_errors,
            "page_errors": self.page_errors,
            "failed_requests": self.failed_requests,
            "http_errors": self.http_errors,
        }


@contextmanager
def browser_session(cfg: PipelineConfig) -> Iterator[Browser]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=cfg.headless)
        try:
            yield browser
        finally:
            browser.close()


@contextmanager
def open_page(
    browser: Browser, url: str, viewport: Viewport, cfg: PipelineConfig
) -> Iterator[tuple[Page, BrowserContext, Diagnostics]]:
    """Open `url` at `viewport`, wait until it has settled, and yield the page."""
    context = browser.new_context(
        viewport={"width": viewport.width, "height": viewport.height},
        device_scale_factor=cfg.device_scale_factor,
        is_mobile=viewport.is_mobile,
        has_touch=viewport.is_mobile,
        reduced_motion="reduce",
    )
    context.set_default_timeout(cfg.timeout_ms)
    page = context.new_page()
    diagnostics = Diagnostics()
    diagnostics.attach(page)
    try:
        page.goto(url, wait_until=cfg.wait_until, timeout=cfg.timeout_ms)
        prepare_page(page, cfg)
        yield page, context, diagnostics
    finally:
        context.close()


def prepare_page(page: Page, cfg: PipelineConfig) -> None:
    """Wait for selector/fonts, trigger lazy loading, settle."""
    if cfg.wait_for_selector:
        page.wait_for_selector(cfg.wait_for_selector, timeout=cfg.timeout_ms)

    # Web fonts change text metrics, so wait for them before measuring.
    page.evaluate("document.fonts ? document.fonts.ready.then(() => true) : true")

    if cfg.scroll_to_load:
        page.evaluate(
            """async () => {
                const step = Math.max(200, Math.floor(window.innerHeight * 0.8));
                let y = 0;
                const limit = 60;                      // safety for infinite feeds
                for (let i = 0; i < limit; i++) {
                    window.scrollTo(0, y);
                    await new Promise(r => setTimeout(r, 80));
                    if (y >= document.documentElement.scrollHeight - window.innerHeight) break;
                    y += step;
                }
                window.scrollTo(0, 0);
                await new Promise(r => setTimeout(r, 100));
            }"""
        )
        # Give lazily-loaded images a chance to finish.
        page.evaluate(
            """() => Promise.all(Array.from(document.images)
                .filter(i => !i.complete)
                .map(i => new Promise(r => { i.onload = i.onerror = r; setTimeout(r, 2000); })))"""
        )

    if cfg.extra_wait_ms:
        page.wait_for_timeout(cfg.extra_wait_ms)
