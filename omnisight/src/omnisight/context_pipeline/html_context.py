"""Collect HTML/CSS context from a loaded page and shrink it for a VLM prompt."""

from __future__ import annotations

import re
from importlib import resources
from pathlib import Path
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup, Comment, Tag
from playwright.sync_api import Page

from omnisight.context_pipeline.config import PipelineConfig

_EXTRACT_JS: str | None = None

_LIST_UNREADABLE_SHEETS_JS = """() => {
    const out = [];
    for (const s of document.styleSheets) {
        try { s.cssRules; } catch (e) { if (s.href) out.push(s.href); }
    }
    return out;
}"""


def _extract_js() -> str:
    global _EXTRACT_JS
    if _EXTRACT_JS is None:
        _EXTRACT_JS = (
            resources.files("omnisight.context_pipeline")
            .joinpath("js/extract.js")
            .read_text(encoding="utf-8")
        )
    return _EXTRACT_JS


# --------------------------------------------------------------------------
# Browser-side extraction
# --------------------------------------------------------------------------
def fetch_unreadable_sheets(page: Page) -> dict[str, str]:
    """Stylesheets whose rules the page's JS cannot read (file:// or cross-origin).

    Chromium blocks `sheet.cssRules` for these, so we fetch the text ourselves
    and let the extractor parse it in a detached CSSStyleSheet.
    """
    hrefs: list[str] = page.evaluate(_LIST_UNREADABLE_SHEETS_JS)
    texts: dict[str, str] = {}
    for href in hrefs:
        try:
            parsed = urlparse(href)
            if parsed.scheme == "file":
                texts[href] = Path(unquote(parsed.path)).read_text(encoding="utf-8", errors="replace")
            else:
                resp = page.context.request.get(href, timeout=10_000)
                if resp.ok:
                    texts[href] = resp.text()
        except Exception:
            continue  # reported as "unavailable" by the extractor
    return texts


def extract_page_context(page: Page, cfg: PipelineConfig) -> dict:
    """Run the in-page extractor and return its raw result."""
    page.evaluate("window.scrollTo(0, 0)")
    external = fetch_unreadable_sheets(page)
    return page.evaluate(
        _extract_js(),
        {
            "maxElements": cfg.max_elements,
            "maxHints": cfg.max_hints,
            "maxRules": cfg.max_rules,
            "maxTextLen": cfg.max_text_len,
            "styleProps": list(cfg.style_props),
            "externalSheets": external,
        },
    )


# --------------------------------------------------------------------------
# HTML cleaning
# --------------------------------------------------------------------------
_DATA_URI = re.compile(r"^(data:[^,]{0,80},)(.+)$", re.S)
_KEEP_SVG_ATTRS = {"width", "height", "viewbox", "class", "role", "aria-label", "data-omni-id", "fill"}


def _shorten_attr(value: str, limit: int = 200) -> str:
    m = _DATA_URI.match(value)
    if m:
        return f"{m.group(1)}…({len(m.group(2))} chars)"
    return value if len(value) <= limit else value[: limit - 1] + "…"


def _is_attached(tag: Tag, root: BeautifulSoup) -> bool:
    node = tag
    while node.parent is not None:
        node = node.parent
    return node is root


def clean_html(
    raw_html: str, cfg: PipelineConfig, protected_ids: set[int]
) -> tuple[str, dict[int, str], dict]:
    """Strip noise from the DOM snapshot.

    Returns (cleaned_html, snippets, info). `protected_ids` are element ids
    (data-omni-id) whose subtrees are never dropped when shrinking to budget.
    `snippets` maps those ids to a short outerHTML excerpt.
    """
    soup = BeautifulSoup(raw_html, "html.parser")

    for c in soup.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()
    for t in soup.find_all(["script", "noscript", "style", "template"]):
        t.decompose()
    for t in soup.find_all("link"):
        t.decompose()
    for t in soup.find_all("meta"):
        if (t.get("name") or "").lower() != "viewport":
            t.decompose()
    head = soup.find("head")
    if head:
        for child in list(head.children):
            if isinstance(child, Tag) and child.name not in ("title", "meta"):
                child.decompose()

    for svg in soup.find_all("svg"):
        svg.attrs = {k: v for k, v in svg.attrs.items() if k.lower() in _KEEP_SVG_ATTRS}
        svg.clear()

    for tag in soup.find_all(True):
        for name, value in list(tag.attrs.items()):
            if isinstance(value, list):
                value = " ".join(value)
            if value == "" and name in ("class", "style"):
                del tag.attrs[name]
                continue
            tag.attrs[name] = _shorten_attr(str(value))

    for s in soup.find_all(string=True):
        if isinstance(s, Comment):
            continue
        text = re.sub(r"\s+", " ", str(s))
        if len(text) > 300:
            text = text[:299] + "…"
        if text != str(s):
            s.replace_with(text)

    # Short outerHTML excerpts for suspects (taken before any shrinking).
    snippets: dict[int, str] = {}
    for pid in protected_ids:
        tag = soup.find(attrs={"data-omni-id": str(pid)})
        if tag is not None:
            flat = re.sub(r"\s+", " ", str(tag))
            snippets[pid] = flat if len(flat) <= 700 else flat[:699] + "…"

    # Shrink: drop the biggest subtrees that contain no suspect.
    protected_tags: set[int] = set()
    for pid in protected_ids:
        tag = soup.find(attrs={"data-omni-id": str(pid)})
        while isinstance(tag, Tag):
            protected_tags.add(id(tag))
            tag = tag.parent

    omitted = 0
    pretty = soup.prettify(formatter="minimal")
    original_chars = len(pretty)
    budget = cfg.max_html_chars
    if len(pretty) > budget:
        sized = sorted(
            (
                (len(str(t)), t)
                for t in soup.find_all(True)
                if t.name not in ("html", "head", "body", "title", "meta")
                and id(t) not in protected_tags
            ),
            key=lambda x: -x[0],
        )
        total = len(pretty)
        for size, tag in sized:
            if total <= budget:
                break
            if size < 200 or not _is_attached(tag, soup):
                continue
            tag.replace_with(Comment(f" omitted <{tag.name}> subtree, {size} chars "))
            total -= size
            omitted += 1
        pretty = soup.prettify(formatter="minimal")
        if len(pretty) > budget:  # last resort: hard cut at a line boundary
            cut = pretty.rfind("\n", 0, budget)
            pretty = pretty[: cut if cut > 0 else budget] + "\n<!-- truncated -->"

    info = {
        "chars": len(pretty),
        "original_chars": original_chars,
        "omitted_subtrees": omitted,
    }
    return pretty, snippets, info


# --------------------------------------------------------------------------
# CSS text
# --------------------------------------------------------------------------
def rules_to_css(
    rules: list[dict], priority_rule_ids: set[int], max_chars: int
) -> tuple[str, list[int]]:
    """Render matched rules as CSS in cascade order, within a character budget.

    Rules that apply to flagged elements are kept first; the rest fill the
    remaining space. Returns (css_text, kept_rule_ids).
    """

    def render(rule: dict) -> str:
        decl = rule["css"]
        body = f"{rule['selector']} {{ {decl} }}"
        for at in reversed(rule["at"]):
            body = f"{at} {{ {body} }}"
        note = []
        if rule["at"] and not rule["media_active"]:
            note.append("inactive at this viewport")
        if rule["states"]:
            note.append("pseudo-state/element")
        suffix = f"  /* {', '.join(note)} */" if note else ""
        return f"/* r{rule['id']} */ {body}{suffix}"

    lines = {r["id"]: render(r) for r in rules}
    keep: set[int] = set()
    used = 0
    ordered = [r["id"] for r in rules if r["id"] in priority_rule_ids] + [
        r["id"] for r in rules if r["id"] not in priority_rule_ids
    ]
    for rid in ordered:
        cost = len(lines[rid]) + 1
        if used + cost > max_chars:
            continue
        keep.add(rid)
        used += cost

    out: list[str] = []
    last_source = None
    for r in rules:
        if r["id"] not in keep:
            continue
        if r["source"] != last_source:
            out.append(f"\n/* ===== {r['source']} ===== */")
            last_source = r["source"]
        out.append(lines[r["id"]])
    dropped = len(rules) - len(keep)
    if dropped:
        out.append(f"\n/* {dropped} further matching rules omitted (size budget) */")
    return "\n".join(out).strip() + "\n", sorted(keep)
