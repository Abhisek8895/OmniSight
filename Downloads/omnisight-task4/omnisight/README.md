# OmniSight — Week 2: Screenshot & HTML Context Pipeline · Week 3: CSS Fixes · Task 4: Anomaly Detection

Captures screenshots of a web page and collects the HTML/CSS context a
vision-language model (VLM) needs to find UI defects, locate them, and propose
code fixes.

## Where this fits

| Stage | Task | Status |
|---|---|---|
| 1 | VLM Setup & Integration | Week 1 |
| **2** | **Screenshot & HTML Context Pipeline** | **this repo** |
| 3 | Prompt Engineering & Defect Detection | next |
| 4 | Fix Generation & Code Extraction | |
| 5 | Code Validation & Fix Output | |

This stage makes no VLM calls. Its output is the input to Stage 3.

## Quick start

```bash
pip install -r requirements.txt
python -m playwright install chromium
pip install -e .                      # optional: gives you the `omnisight` command

# a local file, a URL, or a dev server
omnisight capture samples/defective_login.html
omnisight capture https://example.com --viewports desktop,mobile
omnisight capture http://localhost:3000 --wait-for "#root > *"   # React app

# use a config file (targets + viewports + limits)
omnisight capture -c config/default.yaml

# re-render the prompt text from a saved bundle with a different budget
omnisight render outputs/sample_run/defective-login/mobile/context.json --max-chars 20000
```

Without installing, prefix with `PYTHONPATH=src` and use `python -m omnisight ...`.
`outputs/sample_run/` contains a finished run on the three sample pages so you
can inspect real output straight away.

## What you get

For every `target × viewport`, in `outputs/<page>/<viewport>/`:

| File | Purpose |
|---|---|
| `context.json` | Full-fidelity bundle. **This is what Stage 3 loads.** |
| `vlm_context.md` | Budgeted text view of the bundle, ready to paste into a prompt. |
| `screenshot_viewport.png` | Above-the-fold view. |
| `screenshot_full.png` | Entire scrollable page. |
| `screenshot_annotated.png` | Same page with numbered boxes (`H1`, `H2`, …) around flagged elements. Red/orange/blue = high/medium/low severity. |
| `tiles/` | Overlapping full-width slices of tall pages, so small text survives VLM downscaling. |
| `crops/` | Zoomed crops of the most serious suspects (overlaps include both elements). |
| `page.cleaned.html` | Rendered DOM with scripts, styles and SVG internals stripped. Recorded elements carry `data-omni-id`. |
| `styles.css` | Only the CSS rules that match something on the page, in cascade order. |

Plus `outputs/<page>/manifest.json` summarising all viewports of a page.

All coordinates are **CSS pixels from the top-left of the full page**, and the
screenshots are written in CSS pixels too (even with `device_scale_factor: 2`),
so a bounding box maps 1:1 onto the images.

### `context.json` at a glance

```
schema_version, tool{}, created_at, target{input,url}, viewport{}
page{ title, document size, fonts_used, font_faces (with load status), horizontal_overflow, ... }
screenshots{ viewport, full_page, annotated, tiles[], crops[] }
hints[]     { id, type, severity, element_id, related_id, message, details }
elements[]  { id, selector, tag, attrs, text, bbox, in_viewport, parent, styles, rule_ids,
              flags, html_snippet?, react?{components, source} }
css{ rules[ {id, source, at[], selector, css, matches, media_active, states} ], text, stats }
html{ text, chars, original_chars, omitted_subtrees }
diagnostics{ console_errors, page_errors, failed_requests, http_errors }
```

`element_id` in a hint, `data-omni-id` in the HTML, `H<n>` in the annotated image
and `el#<n>` in `vlm_context.md` are all the same ids, so a defect the VLM sees
in the pixels can be traced to a selector, its computed styles and the exact CSS
rules that produced it. That is what Stage 4 needs to write a fix.

## Why the context is shaped this way

- **Only relevant CSS.** Every rule is tested against the live DOM; rules that match
  nothing are dropped. Each element lists the rules that apply to it, and rules from
  `@media` blocks record whether they are active at this viewport (the usual cause of
  "works on desktop, breaks on mobile").
- **External stylesheets always readable.** Chromium blocks `cssRules` for `file://` and
  cross-origin sheets; the pipeline fetches those itself and parses them in a detached
  stylesheet.
- **Hints are leads, not verdicts.** Measured in the browser, they tell the VLM where to
  look and give it numbers (contrast 1.7:1, 172px overflow). The prompt should still ask
  it to confirm against the image and to look for what heuristics cannot see.
- **Budgets.** Large pages are shrunk deliberately: elements capped (flagged ones first),
  big unflagged subtrees collapsed in the HTML, CSS for suspects prioritised,
  `vlm_context.md` sections capped by priority. Flagged elements are never dropped.
- **Live DOM is never mutated.** The id-tagged HTML is a clone.
- **Diagnostics.** Failed fonts, 404s and console errors are collected because they often
  *cause* the visual defect.
- **React.** When a React dev build is present, elements are mapped to component names
  (and `file:line` on React ≤ 18) via the fiber attached to each DOM node.

## Layout checks

| Hint | Meaning |
|---|---|
| `horizontal-scroll`, `viewport-overflow` | Page wider than the viewport; outermost offending elements |
| `text-clipped`, `text-overflow`, `clipped-by-ancestor` | Text cut off or spilling out of its box / an `overflow:hidden` ancestor |
| `container-overflow` | Child sticks out of a parent that has a visible background or border |
| `overlap`, `occluded`, `overlay-covers-content` | Content on top of content; invisible overlays blocking the page |
| `low-contrast` | WCAG contrast below 4.5:1 (3:1 for large text); downgraded over images/gradients |
| `tiny-text`, `small-tap-target`, `empty-interactive` | Readability and accessibility basics |
| `image-broken`, `image-distorted`, `image-missing-alt` | Image problems |
| `offscreen-content` | Visible content positioned off the page |

Fixed/sticky chrome is excluded from `overlap` by design; `occluded` and
`overlay-covers-content` report when it actually hides something.

## Configuration

`config/default.yaml` documents every option. The ones you will touch most:
`viewports`, `wait_until`, `wait_for_selector`, `max_context_chars`, `crop_hinted_elements`,
`tile_height`. CLI flags override the file (`--viewports desktop,mobile,1280x720,390x844m`).

## Use from Python

```python
from omnisight.context_pipeline import load_config, run_pipeline, render_vlm_context
import json

cfg = load_config("config/default.yaml")
run_pipeline(["http://localhost:3000"], cfg, output_dir="outputs")

bundle = json.load(open("outputs/localhost-3000/mobile/context.json"))
prompt_text = render_vlm_context(bundle, max_chars=40_000)
images = [bundle["screenshots"]["full_page"]["path"], bundle["screenshots"]["annotated"]["path"]]
```

Playwright's sync API cannot run inside an already-running asyncio loop (e.g. a Jupyter
cell); use the CLI or a plain script.

## Tests

```bash
python -m unittest discover -s tests -v     # or: pytest
```

23 tests: detection of every planted defect in `samples/`, a clean page producing zero
hints, external CSS over `file://`, media-rule activity per viewport, React component
extraction, bundle consistency, screenshot/bbox alignment, tiling, budgets, the CLI and
failure isolation. Tests skip themselves if Chromium is not installed.

## Known limitations

- Open shadow DOM and iframes are not traversed.
- Only the initial state is captured: no hover/focus/open-menu states, no login flows
  (authenticated pages would need Playwright `storage_state`).
- Screenshots are clamped to `max_image_dim` (8000px); the context says so when a page is longer.
- Contrast over background images and gradients is flagged as uncertain, not measured.
- Not verified against live public websites in the build environment (no outbound network);
  validated on the bundled fixtures plus a synthetic 1,500-article, 200,000px-tall page.

---

# Week 3 — CSS Fix Application (Task 1) + Post-Fix Screenshots (Task 2)

Code lives in `src/omnisight/fix_pipeline/`.

```bash
# apply AI fixes to the live DOM, then save before/after screenshots
omnisight after-fix samples/defective_login.html \
    --fix samples/fixes/defective_login.fixes.json --viewports desktop,mobile

# one inline fix
omnisight after-fix page.html --selector "button.submit" --css "width:auto"

# shoot an already-repaired page instead
omnisight after-fix page.html --repaired page.fixed.html

# reuse the Week 2 baseline as the "before" image
omnisight after-fix page.html --fix fixes.json --before-image outputs/page/desktop/screenshot_full.png
```

Output per viewport in `outputs/<page>/<viewport>/fix/`:
`before_*.png`, `after_*.png`, `comparison.png` (side by side), `diff.png`,
`applied_fix.css`, `fix_result.json` (status, per-fix outcomes, pixel diff).

## How the two tasks merge

| File | Owner | Role |
|---|---|---|
| `models.py` | shared | `CssFix` (input), `FixOutcome` / `ApplyResult` (output) |
| `css_applier.py` | Task 1 | `CssFixApplier` protocol + reference `DomCssApplier` |
| `after_capture.py`, `compare.py` | Task 2 | wait, screenshot, save, diff |

The only seam is `applier.apply(page, fixes) -> ApplyResult`. To merge, replace
`DomCssApplier` with the Task 1 class (same method) and pass it as
`applier=` to `run_after_fix` / `capture_before_after`. Failures
(`target_not_found`, `invalid_selector`, `invalid_css`, `apply_error`) are
returned as data, never raised.

Tests: `PYTHONPATH=src python -m pytest -q`


---

# Task 4 — Anomaly Detection & Coordinate Extraction

Takes the VLM's analysis of a page and returns **which UI component is anomalous and its
bounding box**. Input: a Week 2 `context.json` + the VLM's reply. Output: ranked anomalies, each
tied to a DOM element, with a box in CSS pixels (origin top-left of the full page, so it maps
1:1 onto `screenshot_full.png`).

```bash
# 1. Build the prompt for the VLM (task + JSON schema + the Week 2 text context)
omnisight anomaly-prompt outputs/sample_run/defective-login/desktop -o prompt.txt
#    ...send prompt.txt + screenshot_full.png (+ screenshot_annotated.png) to your VLM, save its reply...

# 2. Detect anomalies and extract coordinates
omnisight detect outputs/sample_run/defective-login/desktop --vlm-response reply.json
omnisight detect outputs/sample_run/defective-login/desktop --vlm-response reply.txt --json

# No VLM reply? Run on the Week 2 hints only (offline baseline)
omnisight detect outputs/sample_run/defective-login/desktop
```

Without installing: prefix with `PYTHONPATH=src python -m omnisight ...`.

## What you get (`<viewport dir>/anomalies/`, or `-o DIR`)

| File | Purpose |
|---|---|
| `anomalies.json` | `primary` + ranked `anomalies[]`, `unconfirmed_hints[]`, `warnings[]` |
| `anomalies_annotated.png` | Full-page screenshot with a numbered box per anomaly (red/orange/blue = high/medium/low) |
| `primary_anomaly.png` | Padded crop of the top-ranked anomaly |

Each anomaly: `id`, `rank`, `type`, `severity`, `confidence`, `description`, `component`
(`element_id`, `selector`, `tag`, `text`, `html_snippet`, `rule_ids`, `flags`),
`bbox` (`x,y,w,h,x2,y2`), `bbox_normalized` (0–1 of the page), `bbox_source`, `resolution`,
`vlm_bbox` + `vlm_bbox_iou`, `related` (second element of an overlap), `hints`, `warnings`.

## How coordinates are decided

VLM pixel boxes are approximate; the browser measured every element exactly. So each finding is
tied to an element and **the measured DOM box is reported**; the VLM's own box is kept for comparison.

| `resolution` | The finding was matched by… |
|---|---|
| `element_id` | an `el#N` id from the context (most reliable) |
| `hint_id` | an `H<n>` id; the hint names the element |
| `selector` | exact match against a recorded selector |
| `bbox_iou` | the VLM box overlapping an element (IoU ≥ `--min-iou`, default 0.3) |
| `bbox_center` | the VLM box centre falling inside an element (flagged as loose) |
| `text` | quoted visible text |
| `unresolved` | nothing — the VLM box is reported as is (`bbox_source: "vlm"`), clipped to the page, low confidence |

Other behaviour worth knowing:

- **Bare `[a, b, c, d]` is ambiguous** (corners vs x/y/w/h). Both readings are tried and the one that lines up with a real element wins.
- **Coordinate spaces**: `--coord-space auto` treats all-≤1 numbers as normalised 0–1, otherwise CSS px. Use `normalized1000` for 0–1000 models, and `--image-size WxH` if the VLM saw a downscaled image. A reply can also declare `"coordinate_space"` / `"bbox_format"` itself.
- **Conflicts** (an element id whose box is nowhere near the VLM's box) are reported in `warnings` and lower confidence; the DOM box still wins.
- **Duplicates** on the same element merge (highest severity, joined descriptions).
- **Ranking** = severity weight (3/2/1) × `confidence`. `confidence` starts at the VLM's own value and is raised by independent evidence (id/selector match, a Week 2 hint on the same element, VLM and DOM boxes agreeing) and lowered by contradictions. It is a heuristic trust score, **not a calibrated probability**.
- **`unconfirmed_hints`**: high/medium Week 2 hints the VLM did not mention — leads worth a second look.
- **Accepted reply formats**: JSON (bare, in a ```json fence, or after chatter) as `{"anomalies":[…]}`, `defects`, `findings`, a bare list, or one object; many key aliases (`bbox`/`bounding_box`/`box`, `element_id`/`el`, …); or free text containing `el#N`, `H<n>`, backticked selectors and boxes like `[x1, y1, x2, y2]`, `x=… y=… w=… h=…`, `<box>(x1,y1),(x2,y2)</box>`.

## Use from Python

```python
from omnisight.anomaly_pipeline import load_bundle, detect_anomalies, write_outputs

bundle = load_bundle("outputs/sample_run/defective-login/desktop")
result = detect_anomalies(bundle, vlm_reply_text)      # text or decoded JSON; None = heuristic mode
p = result.primary
print(p.type, p.element["selector"], p.bbox)           # BBox(x=556.5, y=315, w=90, h=42)
write_outputs(result, bundle, "outputs/sample_run/defective-login/desktop", "out/")
```

## Status of this stage — please read

- **No VLM is called here.** The repo has no VLM client yet, so `samples/vlm_responses/` holds
  *hand-written stand-ins* for VLM replies (a JSON one mixing reference styles, a free-text one).
  Replace them with real model output; the prompt from `omnisight anomaly-prompt` asks for the
  schema this stage parses best.
- Tested on the bundled sample pages and a fresh capture of `samples/defective_login.html`;
  **not tested against real VLM output** — expect to tune the parser to your model's habits.
- The VLM-box → element snapping uses overlap only. Defects that are not on a recorded element
  (misalignment, wrong colour, uneven spacing) keep the model's own box, unverified.
- Only the initial page state is analysed (same limits as Week 2).

## Tests

```bash
python -m pytest tests -q          # or: python -m unittest discover -s tests -v
```

`tests/test_anomaly_pipeline.py` (44 tests) needs neither Chromium nor network.
