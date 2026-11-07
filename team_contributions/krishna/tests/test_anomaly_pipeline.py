"""Tests for Week 4 / Task 4: anomaly detection and bounding-box extraction.

Needs neither Chromium nor network: it works from saved `context.json` bundles.
Run with: python -m unittest discover -s tests -v   (or pytest)
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from PIL import Image  # noqa: E402

from omnisight.anomaly_pipeline import (  # noqa: E402
    BBox,
    build_prompt,
    detect_anomalies,
    load_bundle,
    parse_vlm_response,
    write_outputs,
)
from omnisight.anomaly_pipeline.bbox import extract_numbers, to_css_candidates  # noqa: E402
from omnisight.cli import main as cli_main  # noqa: E402

SAMPLE_RUN = ROOT / "outputs" / "sample_run"
LOGIN = SAMPLE_RUN / "defective-login" / "desktop"
DASH = SAMPLE_RUN / "defective-dashboard" / "desktop"
VLM_LOGIN = ROOT / "samples" / "vlm_responses" / "defective_login.desktop.vlm.json"
VLM_DASH = ROOT / "samples" / "vlm_responses" / "defective_dashboard.desktop.vlm.txt"


def make_bundle() -> dict:
    """A 1000x800 page with four known elements and two hints."""
    def el(i, sel, x, y, w, h, flags=(), text=""):
        return {"id": i, "selector": sel, "tag": sel.split(" ")[-1].split(".")[0], "attrs": {}, "text": text,
                "bbox": {"x": x, "y": y, "w": w, "h": h}, "in_viewport": True, "parent": None,
                "styles": {}, "rule_ids": [], "flags": list(flags)}
    return {
        "viewport": {"name": "desktop", "width": 1000, "height": 800},
        "page": {"document": {"scroll_width": 1000, "scroll_height": 800}},
        "screenshots": {"full_page": {"path": "screenshot_full.png", "width": 1000, "height": 800}},
        "elements": [
            el(1, "body > div.card", 100, 50, 800, 600),
            el(2, "body > div.card > button.go", 200, 100, 80, 40, ["text-clipped"], "Continue now"),
            el(3, "body > div.card > h1", 200, 200, 400, 50, ["overlap"], "Title"),
            el(4, "body > div.card > span.badge", 300, 205, 100, 30, [], "New"),
            el(5, "body > div.card > p.note", 200, 400, 400, 20, ["low-contrast"], "Fine print here"),
        ],
        "hints": [
            {"id": 1, "type": "text-clipped", "severity": "high", "element_id": 2, "related_id": None,
             "message": "Text is cut off.", "details": {}},
            {"id": 2, "type": "overlap", "severity": "high", "element_id": 3, "related_id": 4,
             "message": "Overlaps badge.", "details": {}},
            {"id": 3, "type": "low-contrast", "severity": "medium", "element_id": 5, "related_id": None,
             "message": "Contrast 1.9:1.", "details": {}},
        ],
    }


class BBoxTests(unittest.TestCase):
    def test_iou_and_corners(self):
        a, b = BBox(0, 0, 10, 10), BBox(5, 0, 10, 10)
        self.assertAlmostEqual(a.iou(b), 50 / 150)
        self.assertEqual(BBox.from_xyxy(10, 20, 30, 50), BBox(10, 20, 20, 30))
        self.assertEqual(a.iou(BBox(20, 20, 5, 5)), 0.0)

    def test_clamp_and_normalise(self):
        c = BBox(-10, 90, 50, 50).clamped(100, 100)
        self.assertEqual((c.x, c.y, c.w, c.h), (0, 90, 40, 10))
        self.assertEqual(BBox(50, 25, 10, 5).normalized(100, 50), {"x": 0.5, "y": 0.5, "w": 0.1, "h": 0.1})

    def test_dict_shapes(self):
        self.assertEqual(extract_numbers({"x": 1, "y": 2, "w": 3, "h": 4}), ([1, 2, 3, 4], "xywh"))
        self.assertEqual(extract_numbers({"xmin": 1, "ymin": 2, "xmax": 3, "ymax": 4}), ([1, 2, 3, 4], "xyxy"))
        self.assertEqual(extract_numbers({"left": 1, "top": 2, "right": 3, "bottom": 4}), ([1, 2, 3, 4], "xyxy"))
        self.assertEqual(extract_numbers([[1, 2], [3, 4]]), ([1, 2, 3, 4], "xyxy"))
        self.assertEqual(extract_numbers([[1, 2, 3, 4]]), ([1, 2, 3, 4], None))
        self.assertIsNone(extract_numbers([1, 2, 3]))
        self.assertIsNone(extract_numbers("nope"))

    def test_bare_list_is_ambiguous(self):
        c = to_css_candidates([10, 10, 50, 40], doc_size=(1000, 800))
        self.assertEqual({how for _, how in c}, {"xyxy", "xywh"})

    def test_normalised_spaces(self):
        c = to_css_candidates([0.1, 0.25, 0.2, 0.5], fmt="xyxy", doc_size=(1000, 800))
        self.assertEqual(c[0][0], BBox(100, 200, 100, 200))
        c = to_css_candidates([100, 250, 200, 500], fmt="xyxy", space="normalized1000", doc_size=(1000, 800))
        self.assertEqual((c[0][0].x, c[0][0].y, c[0][0].w, c[0][0].h), (100, 200, 100, 200))

    def test_downscaled_image(self):
        c = to_css_candidates([50, 25, 100, 75], fmt="xyxy", doc_size=(1000, 800), image_size=(500, 400))
        self.assertEqual(c[0][0], BBox(100, 50, 100, 100))


class ParserTests(unittest.TestCase):
    def test_fenced_json_with_chatter(self):
        text = 'Sure!\n```json\n{"anomalies":[{"element_id":2,"bbox":[1,2,3,4],"severity":"Critical"}]}\n```\nDone.'
        (f,) = parse_vlm_response(text)
        self.assertEqual((f.element_id, f.severity, f.bbox_raw), (2, "high", [1, 2, 3, 4]))

    def test_inline_json_and_bare_list(self):
        (f,) = parse_vlm_response('Result: {"defects":[{"selector":"a > b","description":"x"}]} thanks')
        self.assertEqual(f.selector, "a > b")
        fs = parse_vlm_response('[{"el": "el#7", "bounding_box": {"x":1,"y":2,"width":3,"height":4}}]')
        self.assertEqual((fs[0].element_id, fs[0].bbox_raw), (7, {"x": 1, "y": 2, "width": 3, "height": 4}))

    def test_confidence_forms_and_aliases(self):
        text = json.dumps({"findings": [
            {"category": "Low Contrast", "priority": "minor", "confidence": "85%", "box": [1, 2, 9, 9], "summary": "s"},
            {"type": "x", "confidence": 90, "bbox": [1, 2, 9, 9]},
            {"type": "y", "confidence": 0.4, "bbox": [1, 2, 9, 9]},
        ]})
        a, b, c = parse_vlm_response(text)
        self.assertEqual((a.type, a.severity, a.confidence, a.description), ("low-contrast", "low", 0.85, "s"))
        self.assertEqual((b.confidence, c.confidence), (0.9, 0.4))

    def test_single_object_and_coordinate_meta(self):
        (f,) = parse_vlm_response({"coordinate_space": "normalized_1000", "bbox_format": "xywh",
                                   "anomalous_component": {"bbox": [1, 2, 3, 4]}})
        self.assertEqual((f.coord_space, f.bbox_format), ("normalized1000", "xywh"))

    def test_bbox_given_as_string(self):
        (f,) = parse_vlm_response({"anomalies": [{"bbox": "x=10 y=20 w=30 h=40"}]})
        self.assertEqual((f.bbox_raw, f.bbox_format), ([10.0, 20.0, 30.0, 40.0], "xywh"))

    def test_free_text(self):
        text = (
            "1. **High** - el#11 button is clipped [556, 315, 646, 357], text-clipped.\n"
            "2. Overlap between el#3 and el#4 (H2): x=512 y=72 w=416 h=42\n"
            "3. `body > div.wrap > p.hint` has low contrast.\n"
            "Closing remark with nothing locatable.\n"
        )
        a, b, c = parse_vlm_response(text)
        self.assertEqual((a.element_id, a.severity, a.type, a.bbox_raw), (11, "high", "text-clipped", [556.0, 315.0, 646.0, 357.0]))
        self.assertEqual((b.element_id, b.related_element_id, b.hint_id, b.bbox_format), (3, 4, 2, "xywh"))
        self.assertEqual(c.selector, "body > div.wrap > p.hint")

    def test_box_tag_format(self):
        (f,) = parse_vlm_response("el#2 is odd <box>(10,20),(110,70)</box>")
        self.assertEqual((f.bbox_raw, f.bbox_format), ([10.0, 20.0, 110.0, 70.0], "xyxy"))

    def test_nothing_found(self):
        self.assertEqual(parse_vlm_response("Looks fine to me."), [])
        self.assertEqual(parse_vlm_response('{"anomalies": []}'), [])
        self.assertEqual(parse_vlm_response(""), [])

    def test_file_names_are_not_selectors(self):
        self.assertEqual(parse_vlm_response("See `screenshot_full.png` for details."), [])


class DetectorTests(unittest.TestCase):
    def setUp(self):
        self.bundle = make_bundle()

    def detect(self, response, **kw):
        return detect_anomalies(self.bundle, response, **kw)

    def test_element_id_uses_dom_box_and_records_vlm_box(self):
        r = self.detect({"anomalies": [{"element_id": 2, "type": "text-clipped", "severity": "high",
                                        "bbox": [198, 98, 284, 144]}]})
        a = r.primary
        self.assertEqual((a.element_id, a.resolution, a.bbox_source), (2, "element_id", "dom"))
        self.assertEqual((a.bbox.x, a.bbox.y, a.bbox.w, a.bbox.h), (200, 100, 80, 40))
        self.assertIsNotNone(a.vlm_bbox)
        self.assertGreater(a.vlm_bbox_iou, 0.7)
        self.assertEqual(a.element["selector"], "body > div.card > button.go")

    def test_bare_box_snaps_to_element_either_format(self):
        xyxy = self.detect([{"bbox": [200, 100, 280, 140], "type": "t"}]).primary
        xywh = self.detect([{"bbox": [200, 100, 80, 40], "type": "t"}]).primary
        for a in (xyxy, xywh):
            self.assertEqual((a.element_id, a.resolution), (2, "bbox_iou"))
            self.assertEqual(a.bbox.w, 80)

    def test_prefers_small_specific_element_over_container(self):
        a = self.detect([{"bbox": [205, 98, 285, 142]}]).primary
        self.assertEqual(a.element_id, 2)          # not the 800x600 card that also contains it

    def test_selector_and_hint_and_text_resolution(self):
        self.assertEqual(self.detect([{"selector": "body  >  div.card > h1"}]).primary.resolution, "selector")
        r = self.detect([{"hint_id": 2}]).primary
        self.assertEqual((r.element_id, r.resolution, r.related_element_id), (3, "hint_id", 4))
        self.assertEqual(r.related_bbox, BBox(300, 205, 100, 30))
        t = self.detect([{"text": "fine print"}]).primary
        self.assertEqual((t.element_id, t.resolution), (5, "text"))

    def test_related_element_from_hint_when_element_id_given(self):
        a = self.detect([{"element_id": 3, "type": "overlap"}]).primary
        self.assertEqual(a.related_element_id, 4)

    def test_conflicting_id_and_box_warns_and_lowers_confidence(self):
        good = self.detect([{"element_id": 2, "confidence": 0.8, "bbox": [200, 100, 280, 140]}]).primary
        bad = self.detect([{"element_id": 2, "confidence": 0.8, "bbox": [600, 600, 700, 700]}]).primary
        self.assertTrue(any("barely overlap" in w for w in bad.warnings))
        self.assertEqual(bad.bbox, good.bbox)       # the DOM box still wins
        self.assertLess(bad.confidence, good.confidence)

    def test_unknown_element_falls_back_to_box(self):
        a = self.detect([{"element_id": 99, "bbox": [200, 100, 280, 140]}]).primary
        self.assertEqual((a.element_id, a.resolution), (2, "bbox_iou"))
        self.assertTrue(any("el#99" in w for w in a.warnings))

    def test_unresolved_box_is_kept_flagged_and_clamped(self):
        r = self.detect([{"type": "misalignment", "bbox": [900, 700, 1200, 900]}])
        a = r.primary
        self.assertEqual((a.element_id, a.resolution, a.bbox_source), (None, "unresolved", "vlm"))
        self.assertEqual((a.bbox.x2, a.bbox.y2), (1000, 800))
        self.assertTrue(any("clipped" in w for w in a.warnings))

    def test_unlocatable_finding_is_dropped_with_warning(self):
        r = self.detect([{"description": "something is off", "type": "x"}])
        self.assertEqual(r.anomalies, [])
        self.assertTrue(any("could not be located" in w for w in r.warnings))

    def test_duplicates_merge_and_keep_highest_severity(self):
        r = self.detect([
            {"element_id": 2, "severity": "low", "confidence": 0.5, "description": "a"},
            {"selector": "body > div.card > button.go", "severity": "high", "confidence": 0.9, "description": "b"},
        ])
        self.assertEqual(len(r.anomalies), 1)
        a = r.primary
        self.assertEqual((a.severity, a.merged_from, a.confidence > 0.9), ("high", 2, True))
        self.assertIn("a", a.description)
        self.assertIn("b", a.description)

    def test_ranking_follows_severity_times_confidence(self):
        r = self.detect([
            {"element_id": 5, "severity": "medium", "confidence": 0.9},
            {"element_id": 2, "severity": "high", "confidence": 0.7},
            {"element_id": 3, "severity": "high", "confidence": 0.95},
        ])
        self.assertEqual([a.element_id for a in r.anomalies], [3, 2, 5])
        self.assertEqual([a.id for a in r.anomalies], ["A1", "A2", "A3"])
        self.assertEqual(r.primary.rank, 1)

    def test_defaults_come_from_hints(self):
        a = self.detect([{"element_id": 5}]).primary
        self.assertEqual((a.type, a.severity), ("low-contrast", "medium"))
        self.assertIn("Contrast", a.description)

    def test_normalised_and_downscaled_inputs(self):
        n = self.detect([{"bbox": [0.2, 0.125, 0.28, 0.175], "bbox_format": "xyxy"}]).primary
        self.assertEqual(n.element_id, 2)
        n1000 = self.detect({"coordinate_space": "normalized1000", "anomalies": [{"bbox": [200, 125, 280, 175]}]}).primary
        self.assertEqual(n1000.element_id, 2)
        small = self.detect([{"bbox": [100, 50, 140, 70], "bbox_format": "xyxy"}], image_size=(500, 400)).primary
        self.assertEqual(small.element_id, 2)

    def test_min_confidence_filter(self):
        r = self.detect([{"element_id": 2, "confidence": 0.9}, {"bbox": [900, 700, 950, 750], "confidence": 0.2}],
                        min_confidence=0.5)
        self.assertEqual(len(r.anomalies), 1)

    def test_unconfirmed_hints_listed(self):
        r = self.detect([{"element_id": 2}])
        self.assertEqual({h["id"] for h in r.unconfirmed_hints}, {2, 3})      # H1 confirmed; H2, H3 not
        r = self.detect([{"element_id": 4}])                                  # badge is only the *related* side of H2
        self.assertNotIn(2, {h["id"] for h in r.unconfirmed_hints})

    def test_empty_reply_warns(self):
        r = self.detect("All good!")
        self.assertEqual(r.anomalies, [])
        self.assertTrue(r.warnings)
        self.assertEqual(len(r.unconfirmed_hints), 3)

    def test_heuristic_mode(self):
        r = detect_anomalies(self.bundle)
        self.assertEqual(r.mode, "heuristic")
        self.assertEqual({a.element_id for a in r.anomalies}, {2, 3, 5})
        self.assertEqual(r.unconfirmed_hints, [])
        self.assertEqual(r.primary.severity, "high")

    def test_bad_coord_space(self):
        with self.assertRaises(ValueError):
            detect_anomalies(self.bundle, [], coord_space="furlongs")

    def test_to_dict_is_json_serialisable(self):
        r = self.detect([{"element_id": 3, "confidence": 0.9, "bbox": [200, 200, 600, 250]}])
        d = json.loads(json.dumps(r.to_dict()))
        p = d["primary"]
        self.assertEqual(p["bbox"], {"x": 200.0, "y": 200.0, "w": 400.0, "h": 50.0, "x2": 600.0, "y2": 250.0})
        self.assertEqual(p["bbox_normalized"], {"x": 0.2, "y": 0.25, "w": 0.4, "h": 0.0625})
        self.assertEqual(p["component"]["element_id"], 3)
        self.assertEqual(p["related"]["element_id"], 4)
        self.assertEqual(d["document"], {"w": 1000.0, "h": 800.0})


@unittest.skipUnless(LOGIN.exists() and VLM_LOGIN.exists(), "sample run not present")
class SampleRunTests(unittest.TestCase):
    """The shipped sample bundles + hand-written VLM replies."""

    def test_login_json_reply(self):
        r = detect_anomalies(load_bundle(LOGIN), json.loads(VLM_LOGIN.read_text()))
        by_el = {a.element_id: a for a in r.anomalies if a.element_id}
        self.assertEqual(set(by_el), {11, 7, 17, 15})
        # exact browser-measured boxes, as recorded in context.json
        self.assertEqual((by_el[11].bbox.x, by_el[11].bbox.y, by_el[11].bbox.w, by_el[11].bbox.h), (556.5, 315, 90, 42))
        self.assertEqual(by_el[7].resolution, "bbox_iou")
        self.assertEqual(by_el[15].resolution, "bbox_iou")           # normalised box
        self.assertEqual(by_el[17].resolution, "selector")
        self.assertEqual(r.primary.element_id, 11)
        unresolved = [a for a in r.anomalies if a.element_id is None]
        self.assertEqual(len(unresolved), 1)
        self.assertLess(unresolved[0].confidence, 0.3)
        self.assertIn(2, {h["id"] for h in r.unconfirmed_hints})     # the overlap the VLM missed

    def test_dashboard_free_text_reply(self):
        r = detect_anomalies(load_bundle(DASH), VLM_DASH.read_text(encoding="utf-8"))
        self.assertEqual([a.element_id for a in r.anomalies][:1], [30])
        self.assertEqual({a.element_id for a in r.anomalies}, {30, 4, 32})
        self.assertEqual(r.primary.type, "overlay-covers-content")
        self.assertEqual((r.primary.bbox.w, r.primary.bbox.h), (1440, 900))

    def test_every_dom_bbox_lies_on_the_screenshot(self):
        for page in ("defective-login", "defective-dashboard"):
            for vp in ("desktop", "mobile", "tablet"):
                d = SAMPLE_RUN / page / vp
                if not (d / "context.json").exists():
                    continue
                r = detect_anomalies(load_bundle(d))
                with Image.open(d / "screenshot_full.png") as im:
                    for a in r.anomalies:
                        self.assertGreaterEqual(a.bbox.x, -1, (page, vp, a.id))
                        self.assertGreaterEqual(a.bbox.y, -1, (page, vp, a.id))
                        self.assertLessEqual(a.bbox.y, im.height, (page, vp, a.id))

    def test_clean_page_has_no_anomalies(self):
        clean = SAMPLE_RUN / "clean-page" / "desktop"
        if clean.exists():
            r = detect_anomalies(load_bundle(clean))
            self.assertEqual(r.anomalies, [])
            self.assertTrue(r.warnings)

    def test_prompt_embeds_schema_and_context(self):
        p = build_prompt(load_bundle(LOGIN))
        self.assertIn('"anomalies"', p)
        self.assertIn("el#11", p)
        self.assertIn("Automated layout checks", p)

    def test_outputs_written_and_aligned(self):
        bundle = load_bundle(LOGIN)
        r = detect_anomalies(bundle, json.loads(VLM_LOGIN.read_text()))
        with tempfile.TemporaryDirectory() as tmp:
            files = write_outputs(r, bundle, LOGIN, tmp)
            self.assertEqual(set(files), {"annotated", "primary_crop", "json"})
            data = json.loads((Path(tmp) / "anomalies.json").read_text())
            self.assertEqual(data["primary"]["component"]["element_id"], 11)
            self.assertEqual(data["files"]["json"], "anomalies.json")
            with Image.open(LOGIN / "screenshot_full.png") as base, Image.open(Path(tmp) / "anomalies_annotated.png") as ann:
                self.assertEqual(base.size, ann.size)
            with Image.open(Path(tmp) / "primary_anomaly.png") as crop:
                self.assertGreaterEqual(crop.width, 90)
                self.assertGreaterEqual(crop.height, 42)
                self.assertLess(crop.width, 400)


@unittest.skipUnless(LOGIN.exists() and VLM_LOGIN.exists(), "sample run not present")
class CliTests(unittest.TestCase):
    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli_main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_detect_with_vlm_response(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, _ = self.run_cli("detect", str(LOGIN), "--vlm-response", str(VLM_LOGIN), "-o", tmp)
            self.assertEqual(code, 0)
            self.assertIn("<== primary", out)
            self.assertIn("el#11", out)
            self.assertTrue((Path(tmp) / "anomalies.json").exists())

    def test_detect_json_and_heuristic(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, _ = self.run_cli("detect", str(LOGIN / "context.json"), "--json", "-o", tmp)
            self.assertEqual(code, 0)
            data = json.loads(out)
            self.assertEqual(data["mode"], "heuristic")
            self.assertTrue(data["anomalies"])

    def test_bad_inputs(self):
        self.assertEqual(self.run_cli("detect", "/nonexistent/context.json")[0], 2)
        self.assertEqual(self.run_cli("detect", str(LOGIN), "--vlm-response", "/nonexistent.json")[0], 2)
        self.assertEqual(self.run_cli("detect", str(LOGIN), "--image-size", "abc")[0], 2)

    def test_anomaly_prompt(self):
        code, out, _ = self.run_cli("anomaly-prompt", str(LOGIN))
        self.assertEqual(code, 0)
        self.assertIn("Reply with ONLY a JSON object", out)


if __name__ == "__main__":
    unittest.main()
