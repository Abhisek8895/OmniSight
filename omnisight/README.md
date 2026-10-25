# OmniSight — Week 2: Screenshot & HTML Context Pipeline

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
