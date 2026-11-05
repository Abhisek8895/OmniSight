"""Task 1 interface: apply validated CSS fixes to the live (local) DOM.

`CssFixApplier` is the seam between the two tasks. Task 2 only ever calls
`applier.apply(page, fixes)`; whoever owns Task 1 can replace `DomCssApplier`
with their own class that has the same method and returns an `ApplyResult`.

`DomCssApplier` is a complete reference implementation so Task 2 works
end-to-end today:

* every fix is tested against the page first (valid selector? element exists?),
* every fix gets its own `<style data-omni-fix>` tag, so one bad fix cannot
  break the others,
* failures are returned as data (`FixOutcome.status`), never raised.
"""

from __future__ import annotations

from typing import Protocol, Sequence

from playwright.sync_api import Page

from omnisight.fix_pipeline.models import (
    APPLIED,
    APPLY_ERROR,
    INVALID_CSS,
    INVALID_SELECTOR,
    TARGET_NOT_FOUND,
    ApplyResult,
    CssFix,
    FixOutcome,
)


class CssFixApplier(Protocol):
    """Anything that can apply fixes to a loaded Playwright page."""

    def apply(self, page: Page, fixes: Sequence[CssFix]) -> ApplyResult: ...


_JS_COUNT_MATCHES = """(sel) => {
    try { return { count: document.querySelectorAll(sel).length }; }
    catch (e) { return { error: String(e && e.message || e) }; }
}"""

# Injects the CSS and reports how many *effective* rules the browser accepted
# (rules that keep at least one valid declaration). Browsers silently discard
# CSS they cannot parse, so `rules === 0` means the fix is invalid even though
# nothing threw.
_JS_INJECT = """({css, index}) => {
    const el = document.createElement('style');
    el.setAttribute('data-omni-fix', String(index));
    el.textContent = css;
    (document.head || document.documentElement).appendChild(el);
    const count = (rules) => {
        let n = 0;
        for (const r of Array.from(rules)) {
            if (r.style && r.style.length > 0) n++;
            if (r.cssRules) n += count(r.cssRules);
        }
        return n;
    };
    const rules = el.sheet ? count(el.sheet.cssRules) : 0;
    if (rules === 0) { el.remove(); }
    return { rules };
}"""


def normalize_css(fix: CssFix) -> tuple[str | None, str]:
    """Return `(css, error)`; `css` is None when the fix cannot be turned into rules."""
    css = (fix.css or "").strip()
    if not css:
        return None, "fix has no CSS"
    css = css.replace("</style", "<\\/style")  # never let CSS close its own tag
    if "{" in css:
        return css, ""                         # already complete rules
    if not fix.selector:
        return None, "CSS has only declarations and no selector to attach them to"
    return f"{fix.selector} {{ {css.rstrip(';')}; }}", ""


class DomCssApplier:
    """Reference Task 1 implementation: inject fixes as `<style>` tags."""

    def apply(self, page: Page, fixes: Sequence[CssFix]) -> ApplyResult:
        result = ApplyResult()
        applied_chunks: list[str] = []

        for i, fix in enumerate(fixes):
            outcome = FixOutcome(
                index=i, status=APPLY_ERROR, selector=fix.selector,
                element_id=fix.element_id, hint_id=fix.hint_id,
            )
            result.outcomes.append(outcome)
            try:
                # 1. Identify the target DOM element.
                if fix.selector:
                    probe = page.evaluate(_JS_COUNT_MATCHES, fix.selector)
                    if "error" in probe:
                        outcome.status = INVALID_SELECTOR
                        outcome.message = probe["error"]
                        continue
                    outcome.matched = probe["count"]
                    if probe["count"] == 0:
                        outcome.status = TARGET_NOT_FOUND
                        outcome.message = f"No element matches {fix.selector!r}"
                        continue

                # 2. Build the rule text.
                css, err = normalize_css(fix)
                if css is None:
                    outcome.status = INVALID_CSS
                    outcome.message = err
                    continue

                # 3. Apply it and confirm the browser accepted it.
                injected = page.evaluate(_JS_INJECT, {"css": css, "index": i})
                if injected["rules"] == 0:
                    outcome.status = INVALID_CSS
                    outcome.message = "Browser rejected the CSS (no valid rules parsed)"
                    continue

                outcome.status = APPLIED
                outcome.message = f"{injected['rules']} rule(s) applied"
                applied_chunks.append(css)
            except Exception as exc:  # a crashed page must not abort the run
                outcome.status = APPLY_ERROR
                outcome.message = f"{type(exc).__name__}: {exc}"

        result.applied_css = "\n\n".join(applied_chunks) + ("\n" if applied_chunks else "")
        return result
