"""Shared fixtures for the OmniSight responsive UI tests (Task 3).

* Serves the repository root with a throw-away static server (or uses BASE_URL).
* Provides one Playwright page per viewport.
* Collects per-test data and writes reports/responsive_results.json.
"""
import functools
import http.server
import json
import os
import pathlib
import threading
from datetime import datetime, timezone

import pytest
from playwright.sync_api import sync_playwright

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SITE_PATH = "/Mock-Website/"  # same folder the existing Playwright/test script targets
SHOTS_ROOT = REPO_ROOT / "artifacts" / "screenshots"
RESULTS_JSON = REPO_ROOT / "reports" / "responsive_results.json"

VIEWPORTS = {
    "desktop": {"width": 1440, "height": 900},
    "tablet": {"width": 768, "height": 1024},
    "mobile": {"width": 390, "height": 844},
    "small-mobile": {"width": 320, "height": 700},
}

_RESULTS = []  # filled by the report hook below
_META = {}


def pytest_addoption(parser):
    g = parser.getgroup("responsive")
    g.addoption("--screenshot-set", default="baseline", choices=["baseline", "current"],
                help="Sub-folder of artifacts/screenshots/ to write into (default: baseline).")
    g.addoption("--overwrite-baseline", action="store_true",
                help="Allow replacing existing baseline screenshots.")


def pytest_configure(config):
    config.addinivalue_line("markers", "viewport_matrix: runs once per viewport")


def pytest_sessionstart(session):
    cfg = session.config
    if cfg.getoption("--screenshot-set") == "baseline" and not cfg.getoption("--overwrite-baseline"):
        existing = list((SHOTS_ROOT / "baseline").rglob("*.png"))
        if existing:
            raise pytest.UsageError(
                f"{len(existing)} baseline screenshots already exist and are preserved. "
                "Use --screenshot-set current for a new run, or --overwrite-baseline to replace them.")


@pytest.fixture(scope="session")
def base_url():
    env = os.environ.get("BASE_URL")
    if env:
        yield env.rstrip("/") + "/"
        return
    handler = functools.partial(_QuietHandler, directory=str(REPO_ROOT))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}{SITE_PATH}"
    server.shutdown()


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch()
        _META["browser"] = f"chromium {b.version}"
        _META["playwright"] = _playwright_version()
        yield b
        b.close()


def _playwright_version():
    try:
        from importlib.metadata import version
        return version("playwright")
    except Exception:
        return "unknown"


@pytest.fixture(params=list(VIEWPORTS), ids=list(VIEWPORTS))
def vp_name(request):
    return request.param


@pytest.fixture
def vp(vp_name):
    return {"name": vp_name, **VIEWPORTS[vp_name]}


@pytest.fixture
def record(request):
    """Per-test dict the test fills in (screenshots, metrics, findings, notes)."""
    data = {"screenshots": [], "metrics": {}, "findings": [], "notes": []}
    request.node._record = data
    return data


@pytest.fixture
def page(browser, base_url, vp, record):
    ctx = browser.new_context(viewport={"width": vp["width"], "height": vp["height"]})
    pg = ctx.new_page()
    problems = []
    pg.on("console", lambda m: problems.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
    pg.on("pageerror", lambda e: problems.append(f"pageerror: {e}"))
    pg.on("requestfailed", lambda r: problems.append(f"requestfailed: {r.url} {r.failure}"))
    pg.on("response", lambda r: problems.append(f"http {r.status}: {r.url}") if r.status >= 400 else None)
    try:
        resp = pg.goto(base_url, wait_until="load")
    except Exception as exc:  # network failure / server down
        ctx.close()
        pytest.fail(f"Could not reach the site at {base_url}: {exc}")
    if resp is None or not resp.ok:
        status = resp.status if resp else "no response"
        ctx.close()
        pytest.fail(f"Route {base_url} unavailable (HTTP {status})")
    pg.evaluate("document.fonts.ready")
    pg.page_problems = problems
    record["metrics"]["viewport"] = f'{vp["width"]}x{vp["height"]}'
    yield pg
    ctx.close()


@pytest.fixture
def shot(request, page, vp):
    """shot(step, state, full_page=False) -> repo-relative path of the saved PNG."""
    set_name = request.config.getoption("--screenshot-set")
    out_dir = SHOTS_ROOT / set_name / vp["name"]
    out_dir.mkdir(parents=True, exist_ok=True)

    def _shot(step, state, full_page=False):
        name = f'{step:02d}_{state}_{vp["width"]}x{vp["height"]}{"_fullpage" if full_page else ""}.png'
        path = out_dir / name
        page.screenshot(path=str(path), full_page=full_page)
        rel = path.relative_to(REPO_ROOT).as_posix()
        request.node._record["screenshots"].append(rel)
        return rel

    return _shot


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    rec = getattr(item, "_record", None)
    # one row per test: use the call phase, or setup phase if it failed/skipped there
    if (rep.when == "call") or (rep.when == "setup" and rep.outcome != "passed"):
        reason = None
        if rep.outcome == "skipped" and rep.longrepr:
            reason = rep.longrepr[2].replace("Skipped: ", "") if isinstance(rep.longrepr, tuple) else str(rep.longrepr)
        _RESULTS.append({
            "test": item.name,
            "nodeid": item.nodeid,
            "viewport": getattr(item, "callspec", None) and item.callspec.params.get("vp_name"),
            "outcome": rep.outcome,
            "duration_s": round(rep.duration, 3),
            "skip_reason": reason,
            "failure": str(rep.longrepr).splitlines()[-1] if rep.outcome == "failed" else None,
            **(rec or {}),
        })


def pytest_sessionfinish(session, exitstatus):
    if not _RESULTS:
        return
    summary = {k: sum(1 for r in _RESULTS if r["outcome"] == k) for k in ("passed", "failed", "skipped")}
    summary["total"] = len(_RESULTS)
    doc = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "screenshot_set": session.config.getoption("--screenshot-set"),
        "environment": _META,
        "viewports": VIEWPORTS,
        "summary": summary,
        "note": ("Automated checks cover horizontal overflow, off-screen elements, nav overlap, "
                 "text size, tap-target size and form layout only. They do not prove the whole UI "
                 "is correct; see reports/ui_defects.md for manually reviewed findings."),
        "results": sorted(_RESULTS, key=lambda r: (r["viewport"] or "", r["test"])),
    }
    RESULTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_JSON.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
