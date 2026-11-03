# OmniSight Mock Store – Responsive UI Defects (Task 3 baseline)

**Page under test:** `Mock-Website/index.html` (single static page, no CSS, no JavaScript)
**Viewports:** desktop 1440×900 · tablet 768×1024 · mobile 390×844 · small-mobile 320×700
**Browser:** Chromium 141 via Playwright 1.56 · **Evidence:** `artifacts/screenshots/baseline/<viewport>/`
**Structured results:** `reports/responsive_results.json`

## How these were verified
Each defect below was (a) measured by the automated audit in `tests/responsive/test_responsive.py`
and/or (b) confirmed by viewing the baseline screenshots. Automated checks cover only overflow,
off-screen content, nav overlap, text size, tap-target size and form layout; they do not prove the rest
of the UI is correct. No defect below has been fixed – this is the *before* state.

## What was checked and found OK
| Check | Result (all 4 viewports) |
|---|---|
| Horizontal overflow (`scrollWidth` > viewport) | None |
| Elements positioned outside the viewport | None |
| Nav links overlapping / wrapping | None (one row, 4 links, no overlap) |
| Text smaller than 12px | None (16px body) |
| `<meta name="viewport">` present | Yes |
| Nav anchors scroll their section into view | Yes |
| Form fields and submit button reachable and usable | Yes |
| Console errors / failed requests | None |

## Defects

### D1 – Touch targets too small on touch-size viewports — **Medium**
- **Viewports:** tablet, mobile, small-mobile (measured; desktop not assessed against touch guideline)
- **Expected:** interactive elements ≥ 44×44px (common touch guideline; WCAG 2.2 AA minimum is 24px).
- **Observed:** all 11 interactive elements are under 44px in one dimension. Nav links are ~17px tall and
  sit on one line separated by `|` characters; "Add to Cart" buttons are 83×21px; "Place Demo Order" is 126×21px.
- **Evidence:** `baseline/mobile/01_homepage_390x844.png`, `baseline/small-mobile/01_homepage_320x700.png`,
  `baseline/tablet/01_homepage_768x1024.png`; metrics in `responsive_results.json` (`tap-target-small`).

### D2 – Native validation bubble covers the next form field — **Low/Medium**
- **Viewports:** all four (seen in screenshots)
- **Expected:** validation feedback visible next to the field without hiding other fields.
- **Observed:** on empty submit and on an invalid email, the browser's native bubble is the only error
  feedback. It is transient and sits over the Email field/label (and part of the textarea label), because the
  form has no spacing or inline error text. Users cannot see the field they must fix next.
- **Evidence:** `baseline/<viewport>/07_validation_empty_submit_*.png`, `baseline/<viewport>/08_validation_invalid_email_*.png`.

### D3 – Layout is not responsive; same fixed layout at every width — **Low**
- **Viewports:** all (impact most visible on desktop and tablet)
- **Expected:** layout adapts (e.g. centred max-width container, fluid form controls, larger comfortable spacing).
- **Observed:** the page has no stylesheet, so layout and form-control widths are identical at every viewport
  (inputs 181–185px wide at 320px, 768px and 1440px). On desktop all content ends at x=407px of 1440px (28% of width)
  and everything hugs the left edge, leaving ~70% of the screen empty. Form controls do not scale on mobile/tablet.
- **Evidence:** `baseline/desktop/01_homepage_1440x900_fullpage.png`, `baseline/small-mobile/01_homepage_320x700_fullpage.png`;
  metrics `desktop-content-not-using-width`, `form-controls-do-not-scale`.

### D4 – Checkout form fields misaligned (ragged left edges) — **Low**
- **Viewports:** all
- **Expected:** labels and inputs aligned in a column, or labels stacked above fields on narrow screens.
- **Observed:** label and field share a row; because label widths differ, inputs start at x=84, 55 and 128px,
  giving a ragged form. The textarea label sits at the textarea's bottom edge.
- **Evidence:** `baseline/<viewport>/05_checkout_form_*.png`; metric `form-fields-ragged`.

## Functional observations (not responsive defects)
- **Add to Cart does nothing visible.** Clicking it leaves `#cart` text unchanged and the URL unchanged
  (`baseline/<viewport>/03_after_add_to_cart_*.png`). The cart and confirmation sections are static placeholders.
- **No product-detail page and no order-success state exist**; these flow stages are skipped (8 skipped tests),
  not passed. Submitting a valid form cannot show a confirmation because the form has no action or script.

## Not verified
- Real mobile-device rendering, other browsers (Firefox/WebKit), landscape orientation, zoom/large-text
  settings and screen-reader behaviour were not tested.
