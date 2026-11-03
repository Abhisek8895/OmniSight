"""Responsive UI tests for the OmniSight mock store (Mock-Website/index.html).

The mock store is ONE static page: sections #home, #products, #cart, #checkout,
#confirmation reached through anchor links, and a plain HTML <form> with native
validation. It has no CSS, no JavaScript, no product-detail pages and no cart or
confirmation logic. Tests only exercise what exists; the rest is skipped with a reason.

Check policy
  HARD     -> assertion; failure = test fails (overflow, off-screen content, nav, form reachability)
  ADVISORY -> recorded under "findings" in responsive_results.json, never fails the test
              (tap-target size, unused desktop space, small text, non-scaling form controls)
"""
import re

import pytest
from playwright.sync_api import expect

NAV = {"Home": "#home", "Products": "#products", "Cart": "#cart", "Checkout": "#checkout"}
TAP_MIN = 44      # px, common touch guideline (Apple HIG); WCAG 2.2 AA floor is 24
TEXT_MIN = 12     # px

AUDIT_JS = """
() => {
  const vw = document.documentElement.clientWidth;
  const vis = el => { const r = el.getBoundingClientRect(), s = getComputedStyle(el);
                      return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  const label = el => el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') +
                      (el.textContent.trim() ? ` "${el.textContent.trim().slice(0, 24)}"` : '');
  const all = [...document.body.querySelectorAll('*')].filter(vis);
  const rect = el => { const r = el.getBoundingClientRect(); return {l: r.left, r: r.right, t: r.top, b: r.bottom, w: r.width, h: r.height}; };
  const offscreen = all.filter(e => rect(e).r > vw + 1 || rect(e).l < -1).map(label);
  const navRects = [...document.querySelectorAll('nav a')].map(a => ({n: a.textContent.trim(), ...rect(a)}));
  const overlaps = [];
  for (let i = 0; i < navRects.length; i++) for (let j = i + 1; j < navRects.length; j++) {
    const a = navRects[i], b = navRects[j];
    if (a.l < b.r && b.l < a.r && a.t < b.b && b.t < a.b) overlaps.push(a.n + '/' + b.n);
  }
  const small = [...document.body.querySelectorAll('*')].filter(e =>
      vis(e) && [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()) &&
      parseFloat(getComputedStyle(e).fontSize) < %(TEXT_MIN)d).map(label);
  const targets = [...document.querySelectorAll('a, button, input, textarea')].filter(vis).map(e =>
      ({el: label(e), w: Math.round(rect(e).w), h: Math.round(rect(e).h)}));
  const controls = [...document.querySelectorAll('form input, form textarea')].map(e =>
      ({id: e.id, w: Math.round(rect(e).w), x: Math.round(rect(e).l)}));
  // right-most pixel of actual content (text glyph boxes + controls), not block containers
  let contentRight = 0;
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n; (n = walker.nextNode());) {
    if (!n.textContent.trim() || !n.parentElement || !vis(n.parentElement)) continue;
    const rg = document.createRange(); rg.selectNodeContents(n);
    for (const r of rg.getClientRects()) contentRight = Math.max(contentRight, r.right);
  }
  document.querySelectorAll('input, textarea, button').forEach(e => { if (vis(e)) contentRight = Math.max(contentRight, rect(e).r); });
  return {
    viewport_width: vw,
    scroll_width: document.documentElement.scrollWidth,
    h_overflow_px: document.documentElement.scrollWidth - vw,
    offscreen, nav_overlaps: overlaps,
    nav_rows: new Set(navRects.map(n => Math.round(n.t))).size,
    small_text: small, targets, controls,
    content_right_px: Math.round(contentRight),
    has_viewport_meta: !!document.querySelector('meta[name=viewport][content*="width=device-width"]'),
  };
}
""" % {"TEXT_MIN": TEXT_MIN}


def settle(page, hash_=None):
    """Wait for anchor navigation + scrolling to finish before any screenshot."""
    if hash_:
        page.wait_for_function("h => location.hash === h", arg=hash_)
        expect(page.locator(hash_)).to_be_in_viewport()
    page.wait_for_function(
        """() => new Promise(res => { const y = scrollY;
             requestAnimationFrame(() => requestAnimationFrame(() => res(y === scrollY))); })""")


def audit(page, record, vp, scope):
    a = page.evaluate(AUDIT_JS)
    record["metrics"][f"audit_{scope}"] = {k: a[k] for k in (
        "viewport_width", "scroll_width", "h_overflow_px", "offscreen", "nav_overlaps", "nav_rows")}
    return a


def advisories(a, vp):
    out = []
    w = vp["width"]
    if w <= 768:
        small_t = [t for t in a["targets"] if min(t["w"], t["h"]) < TAP_MIN]
        if small_t:
            out.append({"id": "tap-target-small", "severity": "medium",
                        "detail": f"{len(small_t)} of {len(a['targets'])} interactive elements are smaller than "
                                  f"{TAP_MIN}px in one dimension",
                        "examples": [f"{t['el']} {t['w']}x{t['h']}" for t in small_t[:6]]})
        if a["controls"] and max(c["w"] for c in a["controls"]) < 0.8 * w:
            out.append({"id": "form-controls-do-not-scale", "severity": "low",
                        "detail": f"form fields are {min(c['w'] for c in a['controls'])}-"
                                  f"{max(c['w'] for c in a['controls'])}px wide on a {w}px viewport "
                                  "(not fluid; same widths as desktop)"})
    if w >= 1024:
        fill = a["content_right_px"] / w
        if fill < 0.5:
            out.append({"id": "desktop-content-not-using-width", "severity": "low",
                        "detail": f"all content ends at x={a['content_right_px']}px of {w}px "
                                  f"({fill:.0%}); no centred container or multi-column layout"})
    if a["small_text"]:
        out.append({"id": "small-text", "severity": "medium", "detail": f"text under {TEXT_MIN}px: {a['small_text']}"})
    return out


# --------------------------------------------------------------------------- tests

def test_01_homepage(page, vp, shot, record):
    settle(page)
    expect(page.locator("h1")).to_have_text("OmniSight Store")
    expect(page.locator("#home h2")).to_be_visible()
    record["screenshots_full"] = shot(1, "homepage", full_page=True)
    shot(1, "homepage")
    a = audit(page, record, vp, "homepage")
    record["findings"] += advisories(a, vp)
    assert a["has_viewport_meta"], "missing <meta name=viewport content=width=device-width>"
    assert a["h_overflow_px"] <= 0, f"horizontal overflow of {a['h_overflow_px']}px"
    assert not a["offscreen"], f"elements outside viewport: {a['offscreen']}"
    assert not a["nav_overlaps"], f"overlapping nav links: {a['nav_overlaps']}"
    assert not page.page_problems, page.page_problems


def test_02_navigation_links(page, vp, shot, record):
    """Every nav link is visible, reachable and scrolls its section into view."""
    nav = page.locator("nav")
    expect(nav).to_be_visible()
    for text, target in NAV.items():
        link = nav.get_by_role("link", name=text, exact=True)
        expect(link).to_be_visible()
        expect(link).to_have_attribute("href", target)
        box = link.bounding_box()
        assert 0 <= box["x"] and box["x"] + box["width"] <= vp["width"], f"{text} link outside viewport"
        link.click()
        settle(page, target)
        record["metrics"].setdefault("nav_checked", []).append(target)
    a = audit(page, record, vp, "navigation")
    assert a["h_overflow_px"] <= 0


def test_03_product_listing(page, vp, shot, record):
    page.get_by_role("link", name="Products", exact=True).click()
    settle(page, "#products")
    cards = page.locator("#products article")
    expect(cards).to_have_count(3)
    for i in range(3):
        expect(cards.nth(i).get_by_role("button", name="Add to Cart")).to_be_visible()
    shot(2, "product_listing")
    a = audit(page, record, vp, "products")
    assert a["h_overflow_px"] <= 0 and not a["offscreen"]
    # every card must be fully reachable horizontally
    for i in range(3):
        b = cards.nth(i).bounding_box()
        assert b["x"] >= 0 and b["x"] + b["width"] <= vp["width"] + 1


def test_04_add_to_cart(page, vp, shot, record):
    """Clicks 'Add to Cart'. The page has no script, so this documents what actually happens."""
    page.get_by_role("link", name="Products", exact=True).click()
    settle(page, "#products")
    url_before, cart_before = page.url, page.locator("#cart").inner_text()
    btn = page.locator("#products article").first.get_by_role("button", name="Add to Cart")
    btn.click()
    page.wait_for_timeout(300)  # no async work exists to await; brief pause to catch any late DOM change
    cart_after = page.locator("#cart").inner_text()
    record["metrics"]["cart_changed_after_add"] = cart_before != cart_after
    record["metrics"]["url_changed_after_add"] = page.url != url_before
    shot(3, "after_add_to_cart")
    if cart_before == cart_after:
        record["notes"].append("Add to Cart has no observable effect: #cart text unchanged "
                               "(functional gap, not a responsive defect).")
    assert page.url == url_before, "Add to Cart unexpectedly navigated away"
    assert not page.page_problems, page.page_problems


def test_05_cart(page, vp, shot, record):
    page.get_by_role("link", name="Cart", exact=True).click()
    settle(page, "#cart")
    expect(page.locator("#cart h2")).to_have_text("Shopping Cart")
    shot(4, "cart")
    a = audit(page, record, vp, "cart")
    assert a["h_overflow_px"] <= 0


def test_06_checkout_form(page, vp, shot, record):
    page.get_by_role("link", name="Checkout", exact=True).click()
    settle(page, "#checkout")
    fields = {"name": page.locator("#name"), "email": page.locator("#email"), "address": page.locator("#address")}
    for fid, loc in fields.items():
        expect(loc).to_be_visible()
        expect(page.locator(f"label[for={fid}]")).to_be_visible()
        b = loc.bounding_box()
        assert b["x"] >= 0 and b["x"] + b["width"] <= vp["width"] + 1, f"#{fid} outside viewport"
    submit = page.get_by_role("button", name="Place Demo Order")
    expect(submit).to_be_visible()
    sb = submit.bounding_box()
    assert sb["x"] + sb["width"] <= vp["width"] + 1
    shot(5, "checkout_form")
    # fields must be fully usable: type into each one at this viewport
    fields["name"].fill("Test User")
    fields["email"].fill("test.user@example.com")
    fields["address"].fill("1 Test Street, Testville")
    shot(6, "checkout_form_filled")
    for loc in fields.values():
        assert loc.input_value()
    # layout: record whether label and field share a row (stacked vs inline)
    lb, ib = page.locator("label[for=name]").bounding_box(), fields["name"].bounding_box()
    record["metrics"]["label_and_input_same_row"] = abs(lb["y"] - ib["y"]) < ib["height"]
    a = audit(page, record, vp, "checkout")
    record["findings"] += [f for f in advisories(a, vp) if f["id"] == "form-controls-do-not-scale"]
    lefts = {c["id"]: c["x"] for c in a["controls"]}
    record["metrics"]["field_left_edges_px"] = lefts
    if max(lefts.values()) - min(lefts.values()) > 8:
        record["findings"].append({"id": "form-fields-ragged", "severity": "low",
                                   "detail": f"form fields start at different x positions {lefts} "
                                             "(labels are inline with variable width, no aligned/stacked layout)"})
    assert a["h_overflow_px"] <= 0 and not a["offscreen"]


def test_07_validation_errors(page, vp, shot, record):
    """Empty submit must be blocked by native validation; bad email must be flagged."""
    page.get_by_role("link", name="Checkout", exact=True).click()
    settle(page, "#checkout")
    url_before = page.url
    page.get_by_role("button", name="Place Demo Order").click()
    page.wait_for_timeout(300)
    assert page.url == url_before, "empty form was submitted"
    states = page.evaluate("""() => Object.fromEntries(['name','email','address'].map(id => {
        const e = document.getElementById(id); return [id, {valueMissing: e.validity.valueMissing, msg: e.validationMessage}]; }))""")
    record["metrics"]["empty_submit_validity"] = states
    assert all(s["valueMissing"] for s in states.values()), states
    # Headless Chromium does render the native bubble in screenshots (observed). Validity is still asserted
    # through the Constraint Validation API because the bubble is transient browser UI, not page DOM.
    record["notes"].append("Native validation bubble is browser UI (not DOM); asserted via the Constraint "
                           "Validation API and also visible in the screenshot.")
    shot(7, "validation_empty_submit")
    page.fill("#name", "Test User")
    page.fill("#email", "not-an-email")
    page.fill("#address", "1 Test Street")
    page.get_by_role("button", name="Place Demo Order").click()
    page.wait_for_timeout(300)
    email = page.evaluate("() => ({typeMismatch: email.validity.typeMismatch, msg: email.validationMessage})")
    record["metrics"]["invalid_email_validity"] = email
    assert email["typeMismatch"], email
    assert page.url == url_before
    shot(8, "validation_invalid_email")
    a = audit(page, record, vp, "validation")
    assert a["h_overflow_px"] <= 0


def test_08_product_details(page, vp):
    pytest.skip("Not supported: the mock store has no product-detail page or route "
                "(products are static <article> blocks without links).")


def test_09_order_success(page, vp):
    pytest.skip("Not supported: the form has no action/JS, so submitting a valid form never produces a "
                "confirmation; #confirmation only contains static placeholder text.")
