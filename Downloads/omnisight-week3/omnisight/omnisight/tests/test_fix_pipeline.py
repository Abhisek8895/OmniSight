"""Tests for Week 3 Task 2 (before/after capture) and the reference Task 1 applier.

Run with: python -m unittest discover -s tests -v   (or pytest)
Tests skip themselves if Chromium is not installed.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from PIL import Image  # noqa: E402

from omnisight.cli import main as cli_main  # noqa: E402
from omnisight.context_pipeline.browser import browser_session  # noqa: E402
from omnisight.context_pipeline.config import PipelineConfig, Viewport  # noqa: E402
from omnisight.fix_pipeline import (  # noqa: E402
    AfterFixOptions,
    CssFix,
    DomCssApplier,
    capture_before_after,
    load_fixes,
)
from omnisight.fix_pipeline.css_applier import normalize_css  # noqa: E402

SAMPLE = str(ROOT / "samples" / "defective_login.html")
FIXES = ROOT / "samples" / "fixes" / "defective_login.fixes.json"
DESKTOP = Viewport("desktop", 1440, 900)
FAST = AfterFixOptions(settle_ms=50, networkidle_timeout_ms=500)


class NormalizeTests(unittest.TestCase):
    def test_declarations_are_wrapped(self):
        css, err = normalize_css(CssFix(css="color: red;", selector=".a"))
        self.assertEqual(err, "")
        self.assertIn(".a {", css)

    def test_declarations_without_selector_rejected(self):
        css, err = normalize_css(CssFix(css="color: red"))
        self.assertIsNone(css)
        self.assertTrue(err)

    def test_complete_rules_pass_through(self):
        css, _ = normalize_css(CssFix(css=".a{color:red}"))
        self.assertEqual(css, ".a{color:red}")

    def test_loader(self):
        fixes = load_fixes(FIXES)
        self.assertEqual(fixes[0].selector, "button.submit")
        self.assertEqual(fixes[0].hint_id, 1)


class BrowserTestCase(unittest.TestCase):
    cfg = PipelineConfig(extra_wait_ms=50)

    @classmethod
    def setUpClass(cls):
        try:
            cls._cm = browser_session(cls.cfg)
            cls.browser = cls._cm.__enter__()
        except Exception as exc:  # Chromium missing
            raise unittest.SkipTest(f"Chromium unavailable: {exc}")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls._cm.__exit__(None, None, None)
        cls.tmp.cleanup()

    def run_capture(self, name: str, **kw) -> dict:
        return capture_before_after(
            self.browser, SAMPLE, DESKTOP, self.cfg, self.root / name, options=FAST, **kw
        )


class BeforeAfterTests(BrowserTestCase):
    def test_live_css_saves_before_and_after(self):
        res = self.run_capture("live", fixes=load_fixes(FIXES))
        self.assertEqual(res["status"], "ok")
        out = self.root / "live"
        for name in ("before_full.png", "after_full.png", "before_viewport.png",
                     "after_viewport.png", "comparison.png", "diff.png",
                     "fix_result.json", "applied_fix.css"):
            self.assertTrue((out / name).exists(), name)
        self.assertTrue(res["comparison"]["visible_change"])
        statuses = [o["status"] for o in res["apply"]["outcomes"]]
        self.assertEqual(statuses.count("applied"), 3)
        self.assertIn("target_not_found", statuses)
        self.assertIn("invalid_css", statuses)
        with Image.open(out / "before_viewport.png") as im:
            self.assertEqual(im.size, (1440, 900))

    def test_before_is_unmodified_original(self):
        res = self.run_capture("orig", fixes=[CssFix(css="color:red", selector=".nope")],
                               applier=DomCssApplier())
        self.assertEqual(res["status"], "apply_failed")
        self.assertTrue((self.root / "orig" / "before_full.png").exists())
        self.assertFalse((self.root / "orig" / "after_full.png").exists())

    def test_capture_on_apply_failure(self):
        res = capture_before_after(
            self.browser, SAMPLE, DESKTOP, self.cfg, self.root / "force",
            fixes=[CssFix(css="color:red", selector=".nope")],
            options=AfterFixOptions(settle_ms=50, networkidle_timeout_ms=500, capture_on_apply_failure=True),
        )
        self.assertEqual(res["status"], "ok")
        self.assertFalse(res["comparison"]["visible_change"])

    def test_missing_target_is_recorded_not_raised(self):
        res = capture_before_after(
            self.browser, str(self.root / "missing.html"), DESKTOP, self.cfg,
            self.root / "missing", fixes=[CssFix(css="a{color:red}")], options=FAST,
        )
        self.assertEqual(res["status"], "render_failed")
        self.assertTrue((self.root / "missing" / "fix_result.json").exists())

    def test_repaired_page_mode(self):
        repaired = self.root / "repaired.html"
        original = Path(SAMPLE).read_text(encoding="utf-8")
        repaired.write_text(
            original.replace("</head>", "<style>.badge{position:static}</style></head>", 1),
            encoding="utf-8",
        )
        res = self.run_capture("repaired", repaired_target=str(repaired))
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["mode"], "repaired-page")
        self.assertTrue(res["comparison"]["visible_change"])

    def test_reused_before_image(self):
        before = self.root / "baseline.png"
        Image.new("RGB", (1440, 900), "white").save(before)
        res = self.run_capture("reuse", fixes=load_fixes(FIXES), before_image=before)
        self.assertEqual(res["status"], "ok")
        self.assertIn("reused_from", res["screenshots"]["before"]["full_page"])

    def test_requires_exactly_one_source(self):
        with self.assertRaises(ValueError):
            self.run_capture("bad")


class CliTests(unittest.TestCase):
    """Plain TestCase: the CLI launches its own Playwright, which cannot share a thread with BrowserTestCase's."""

    def test_cli_after_fix(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._run(Path(tmp))

    def _run(self, root: Path):
        out = root / "cli"
        code = cli_main(["after-fix", SAMPLE, "--fix", str(FIXES),
                         "--viewports", "desktop", "-o", str(out)])
        self.assertEqual(code, 0)
        self.assertTrue((out / "defective-login" / "desktop" / "fix" / "after_full.png").exists())
        manifest = json.loads((out / "defective-login" / "fix_manifest.json").read_text())
        self.assertEqual(manifest["viewports"]["desktop"]["status"], "ok")


if __name__ == "__main__":
    unittest.main()
