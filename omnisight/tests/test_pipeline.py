"""End-to-end and unit tests for the Week 2 context pipeline.

Run with either:
    python -m unittest discover -s tests -v
    pytest
"""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from PIL import Image, ImageChops  # noqa: E402

from omnisight.cli import main as cli_main  # noqa: E402
from omnisight.context_pipeline.browser import browser_session, resolve_target, slugify  # noqa: E402
from omnisight.context_pipeline.config import PipelineConfig, Viewport, load_config  # noqa: E402
from omnisight.context_pipeline.html_context import clean_html, rules_to_css  # noqa: E402
from omnisight.context_pipeline.pipeline import capture_context  # noqa: E402
from omnisight.context_pipeline.render import render_vlm_context  # noqa: E402

SAMPLES = ROOT / "samples"
DESKTOP = Viewport("desktop", 1440, 900)
MOBILE = Viewport("mobile", 375, 812, is_mobile=True)


class BrowserTestCase(unittest.TestCase):
    """Shares one Chromium instance and one temp output dir per test class."""

    cfg = PipelineConfig(extra_wait_ms=50)

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.tmp = Path(cls._tmp.name)
        cls._session = browser_session(cls.cfg)
        try:
            cls.browser = cls._session.__enter__()
        except Exception as exc:  # no Chromium installed
            cls._tmp.cleanup()
            raise unittest.SkipTest(f"Chromium unavailable: {exc}")

    @classmethod
    def tearDownClass(cls):
        cls._session.__exit__(None, None, None)
        cls._tmp.cleanup()

    def capture(self, sample: str, viewport: Viewport, cfg: PipelineConfig | None = None) -> tuple[dict, Path]:
        out = self.tmp / f"{Path(sample).stem}-{viewport.name}"
        bundle = capture_context(self.browser, str(SAMPLES / sample), viewport, cfg or self.cfg, out)
        return bundle, out


def hint_types(bundle: dict) -> set[str]:
    return {h["type"] for h in bundle["hints"]}


class TestDetection(BrowserTestCase):
    def test_clean_page_is_quiet(self):
        bundle, _ = self.capture("clean_page.html", DESKTOP)
        self.assertEqual(bundle["hints"], [], bundle["hints"])
        bundle, _ = self.capture("clean_page.html", MOBILE)
        self.assertEqual(bundle["hints"], [], bundle["hints"])

    def test_login_planted_defects_are_found(self):
        bundle, _ = self.capture("defective_login.html", DESKTOP)
        expected = {
            "text-clipped", "overlap", "low-contrast", "image-broken", "image-distorted",
            "image-missing-alt", "small-tap-target", "empty-interactive", "tiny-text",
            "container-overflow",
        }
        self.assertTrue(expected <= hint_types(bundle), f"missing: {expected - hint_types(bundle)}")

    def test_hints_point_at_the_right_elements(self):
        bundle, _ = self.capture("defective_login.html", DESKTOP)
        els = {e["id"]: e for e in bundle["elements"]}
        by_type = {h["type"]: h for h in bundle["hints"]}
        self.assertIn("submit", els[by_type["text-clipped"]["element_id"]]["attrs"]["class"])
        self.assertIn("hint", els[by_type["low-contrast"]["element_id"]]["attrs"]["class"])
        self.assertEqual(els[by_type["image-broken"]["element_id"]]["tag"], "img")
        overlap = by_type["overlap"]
        pair = {els[overlap["element_id"]]["tag"], els[overlap["related_id"]]["tag"]}
        self.assertEqual(pair, {"h1", "span"})

    def test_mobile_horizontal_scroll(self):
        desktop, _ = self.capture("defective_login.html", DESKTOP)
        mobile, _ = self.capture("defective_login.html", MOBILE)
        self.assertNotIn("horizontal-scroll", hint_types(desktop))
        self.assertIn("horizontal-scroll", hint_types(mobile))
        self.assertIsNotNone(mobile["page"]["horizontal_overflow"])
        offenders = [h for h in mobile["hints"] if h["type"] == "viewport-overflow"]
        self.assertEqual(len(offenders), 1, "only the outermost offender should be reported")

    def test_overlay_and_ancestor_clipping(self):
        mobile, _ = self.capture("defective_dashboard.html", MOBILE)
        self.assertIn("overlay-covers-content", hint_types(mobile))
        self.assertIn("clipped-by-ancestor", hint_types(mobile))
        desktop, _ = self.capture("defective_dashboard.html", DESKTOP)
        self.assertNotIn("clipped-by-ancestor", hint_types(desktop))  # fits when 3 columns wide


class TestContextCollection(BrowserTestCase):
    def test_external_css_over_file_url_is_parsed(self):
        bundle, _ = self.capture("defective_dashboard.html", DESKTOP)
        stats = bundle["css"]["stats"]
        self.assertEqual(stats["unavailable"], [])
        sources = {r["source"].rsplit("/", 1)[-1] for r in bundle["css"]["rules"]}
        self.assertIn("dashboard.css", sources)
        self.assertIn(".card", bundle["css"]["text"])

    def test_rules_matching_nothing_are_dropped(self):
        page = self.tmp / "dead-css.html"
        page.write_text("<html><head><style>.live{color:red}.nothing-here{color:blue}"
                        "@media (max-width:300px){.also-dead{margin:0}}</style></head>"
                        "<body><p class='live'>hi</p></body></html>")
        bundle = capture_context(self.browser, str(page), DESKTOP, self.cfg, self.tmp / "dead-css-out")
        self.assertEqual(bundle["css"]["stats"]["dropped_unmatched"], 2)
        self.assertIn(".live", bundle["css"]["text"])
        self.assertNotIn("nothing-here", bundle["css"]["text"])
        self.assertNotIn("also-dead", bundle["css"]["text"])

    def test_media_rule_activity_follows_viewport(self):
        def small_screen_rule(bundle):
            return next(
                r for r in bundle["css"]["rules"]
                if r["selector"] == ".grid" and any("max-width: 600px" in a for a in r["at"])
            )
        desktop, _ = self.capture("defective_dashboard.html", DESKTOP)
        mobile, _ = self.capture("defective_dashboard.html", MOBILE)
        self.assertFalse(small_screen_rule(desktop)["media_active"])
        self.assertTrue(small_screen_rule(mobile)["media_active"])

    def test_react_component_names(self):
        bundle, _ = self.capture("defective_dashboard.html", DESKTOP)
        card = next(e for e in bundle["elements"] if e["attrs"].get("id") == "card-revenue")
        self.assertEqual(card["react"]["components"], ["MetricCard", "Dashboard"])
        self.assertEqual(card["react"]["source"], "src/MetricCard.jsx:8")

    def test_load_diagnostics(self):
        bundle, _ = self.capture("defective_dashboard.html", DESKTOP)
        failed = [r["url"] for r in bundle["diagnostics"]["failed_requests"]]
        self.assertTrue(any("missing-font.woff2" in u for u in failed), failed)
        self.assertTrue(any(f["status"] == "error" for f in bundle["page"]["font_faces"]))

    def test_bundle_is_internally_consistent(self):
        bundle, out = self.capture("defective_login.html", DESKTOP)
        ids = [e["id"] for e in bundle["elements"]]
        self.assertEqual(len(ids), len(set(ids)))
        idset = set(ids)
        for e in bundle["elements"]:
            self.assertTrue(e["parent"] is None or e["parent"] in idset)
        for h in bundle["hints"]:
            for key in ("element_id", "related_id"):
                self.assertTrue(h[key] is None or h[key] in idset)
        # every flagged element is addressable in the cleaned HTML
        html = bundle["html"]["text"]
        for h in bundle["hints"]:
            if h["element_id"]:
                self.assertIn(f'data-omni-id="{h["element_id"]}"', html)
        # rule ids referenced by elements exist in the shipped CSS
        rule_ids = {r["id"] for r in bundle["css"]["rules"]}
        for e in bundle["elements"]:
            self.assertTrue(set(e["rule_ids"]) <= rule_ids)
        # JSON on disk matches, files exist
        on_disk = json.loads((out / "context.json").read_text())
        self.assertEqual(on_disk["schema_version"], bundle["schema_version"])
        for name in ("page.cleaned.html", "styles.css", "vlm_context.md", "screenshot_full.png"):
            self.assertTrue((out / name).stat().st_size > 0, name)

    def test_screenshots_use_css_pixels_and_align_with_bboxes(self):
        hi_dpi = PipelineConfig(extra_wait_ms=50, device_scale_factor=2.0)
        bundle, out = self.capture("defective_login.html", DESKTOP, hi_dpi)
        full = bundle["screenshots"]["full_page"]
        self.assertEqual((full["width"], full["height"]),
                         (bundle["page"]["document"]["scroll_width"], bundle["page"]["document"]["scroll_height"]))
        for e in bundle["elements"]:
            b = e["bbox"]
            self.assertLessEqual(b["x"] + b["w"], full["width"] + 700)  # table intentionally overflows card
            self.assertLessEqual(b["y"] + b["h"], full["height"] + 2)

    def test_annotation_and_crops(self):
        bundle, out = self.capture("defective_login.html", DESKTOP)
        shots = bundle["screenshots"]
        raw = Image.open(out / shots["full_page"]["path"]).convert("RGB")
        ann = Image.open(out / shots["annotated"]["path"]).convert("RGB")
        self.assertEqual(raw.size, ann.size)
        self.assertIsNotNone(ImageChops.difference(raw, ann).getbbox(), "annotation drew nothing")
        self.assertGreaterEqual(len(shots["crops"]), 5)
        for c in shots["crops"]:
            self.assertTrue((out / c["path"]).exists())

    def test_tall_page_is_tiled(self):
        tall = self.tmp / "tall.html"
        tall.write_text("<html><body>" + "".join(f"<p style='height:80px'>row {i}</p>" for i in range(120)) + "</body></html>")
        out = self.tmp / "tall-out"
        bundle = capture_context(self.browser, str(tall), DESKTOP, self.cfg, out)
        tiles = bundle["screenshots"]["tiles"]
        self.assertGreaterEqual(len(tiles), 2)
        self.assertEqual(tiles[0]["y_start"], 0)
        for a, b in zip(tiles, tiles[1:]):
            self.assertLess(b["y_start"], a["y_end"], "tiles should overlap")

    def test_missing_target_raises(self):
        with self.assertRaises(FileNotFoundError):
            capture_context(self.browser, str(SAMPLES / "nope.html"), DESKTOP, self.cfg, self.tmp / "x")


class TestRender(BrowserTestCase):
    def test_budget_is_respected_and_priorities_kept(self):
        bundle, _ = self.capture("defective_dashboard.html", MOBILE)
        full = render_vlm_context(bundle, 60_000)
        small = render_vlm_context(bundle, 9_000)
        self.assertLess(len(small), len(full))
        self.assertLess(len(small), 9_000 * 1.15)
        for text in (full, small):
            self.assertIn("## Automated layout checks", text)
            self.assertIn("overlay-covers-content", text)
        self.assertIn("MetricCard", full)

    def test_universal_rules_not_listed_per_element(self):
        bundle, _ = self.capture("defective_dashboard.html", DESKTOP)
        suspects = render_vlm_context(bundle).split("## Suspect elements")[1].split("## Diagnostics")[0]
        self.assertNotIn("* { box-sizing", suspects)


class TestCli(unittest.TestCase):
    """The CLI launches its own browser, so these tests must not share one."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.tmp = Path(cls._tmp.name)
        try:
            with browser_session(PipelineConfig()):
                pass
        except Exception as exc:
            cls._tmp.cleanup()
            raise unittest.SkipTest(f"Chromium unavailable: {exc}")

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_capture_then_render(self):
        out = self.tmp / "cli-out"
        code = cli_main(["capture", str(SAMPLES / "defective_login.html"), "-o", str(out), "--viewports", "mobile,800x600"])
        self.assertEqual(code, 0)
        self.assertTrue((out / "defective-login" / "mobile" / "context.json").exists())
        self.assertTrue((out / "defective-login" / "800x600" / "context.json").exists())
        manifest = json.loads((out / "defective-login" / "manifest.json").read_text())
        self.assertEqual(set(manifest["viewports"]), {"mobile", "800x600"})

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cli_main(["render", str(out / "defective-login" / "mobile" / "context.json"), "--max-chars", "12000"])
        self.assertEqual(code, 0)
        self.assertIn("# Page context", buf.getvalue())

    def test_failures_do_not_abort_the_run(self):
        out = self.tmp / "cli-fail"
        code = cli_main(["capture", "http://127.0.0.1:9/unreachable", str(SAMPLES / "clean_page.html"),
                         "-o", str(out), "--viewports", "desktop", "--timeout-ms", "3000"])
        self.assertEqual(code, 1)
        self.assertTrue((out / "clean-page" / "desktop" / "context.json").exists())


class TestPureFunctions(unittest.TestCase):
    def test_resolve_target_and_slugify(self):
        self.assertTrue(resolve_target(str(SAMPLES / "clean_page.html")).startswith("file://"))
        self.assertEqual(resolve_target("https://example.com/a"), "https://example.com/a")
        self.assertEqual(slugify("https://Example.com/Docs/Intro?x=1"), "example-com-docs-intro")
        self.assertEqual(slugify(str(SAMPLES / "clean_page.html")), "clean-page")
        with self.assertRaises(FileNotFoundError):
            resolve_target("definitely/not/here.html")

    def test_config_loading(self):
        cfg = load_config(ROOT / "config" / "default.yaml", timeout_ms=5000)
        self.assertEqual(cfg.timeout_ms, 5000)
        self.assertEqual([v.name for v in cfg.viewports], ["desktop", "tablet", "mobile"])
        self.assertTrue(cfg.viewports[2].is_mobile)
        bad = Path(tempfile.mkdtemp()) / "bad.yaml"
        bad.write_text("not_a_real_option: 1\n")
        with self.assertRaises(ValueError):
            load_config(bad)

    def test_clean_html_strips_noise_and_protects_suspects(self):
        filler = "".join(f"<li>entry number {i} with some filler text to take up space</li>" for i in range(300))
        raw = f"""<!DOCTYPE html><html><head><title>t</title><meta charset="utf-8">
          <meta name="viewport" content="width=device-width"><style>body{{}}</style>
          <link rel="stylesheet" href="a.css"><script>alert(1)</script></head>
          <body><!-- secret comment --><svg viewBox="0 0 1 1"><path d="M0 0"/></svg>
          <img src="data:image/png;base64,{'A' * 5000}" data-omni-id="1">
          <ul data-omni-id="2">{filler}</ul>
          <button data-omni-id="3">Keep me</button></body></html>"""
        cfg = PipelineConfig(max_html_chars=3000)
        cleaned, snippets, info = clean_html(raw, cfg, {3})
        for noise in ("alert(1)", "secret comment", "a.css", "<path", "AAAAAAAA", "body{"):
            self.assertNotIn(noise, cleaned)
        self.assertIn('name="viewport"', cleaned)
        self.assertIn("Keep me", cleaned)
        self.assertIn("omitted <ul> subtree", cleaned)
        self.assertGreater(info["omitted_subtrees"], 0)
        self.assertLessEqual(info["chars"], 3100)
        self.assertIn(3, snippets)

    def test_rules_to_css_prefers_priority_rules_and_keeps_cascade_order(self):
        def rule(i, sel):
            return {"id": i, "source": "a.css", "at": [], "selector": sel, "css": "color: red;",
                    "media_active": True, "states": False}
        rules = [rule(1, ".a"), rule(2, ".b"), rule(3, ".c")]
        one_line = len("/* r1 */ .a { color: red; }") + 1
        text, kept = rules_to_css(rules, {3}, one_line * 2 + 5)
        self.assertEqual(kept, [1, 3])  # priority rule 3 kept, then earliest filler
        self.assertLess(text.index(".a {"), text.index(".c {"))
        self.assertIn("omitted", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
